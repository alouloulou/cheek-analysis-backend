from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

# Import your AI analysis functions
from ai_analysis import analyze_cheek_metrics, generate_improvement_plan
from supabase_client import save_analysis_to_supabase

app = FastAPI(title="Cheek Analysis API", version="1.0.0")

# Enable CORS for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store temporary images
TEMP_DIR = Path("temp_images")
TEMP_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Cheek Analysis API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cheek-analysis-backend"}

@app.post("/analyze")
async def analyze_image(
    user_id: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Analyze uploaded image and return cheek metrics + improvement plan
    """
    try:
        print(f"Starting analysis for user: {user_id}")

        # Validate image type
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        print(f"Accepted image type: {image.content_type}")

        # Generate unique ID
        analysis_id = str(uuid.uuid4())
        file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        temp_filename = f"{analysis_id}.{file_extension}"
        temp_filepath = TEMP_DIR / temp_filename

        # Save uploaded file
        with open(temp_filepath, "wb") as f:
            f.write(await image.read())
        print(f"Saved temporary image: {temp_filepath}")

        # Create public URL for AI access
        temp_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/temp-image/{temp_filename}"
        print(f"Temporary URL for AI: {temp_url}")

        # Get user data from Supabase
        from supabase_client import get_user_profile
        user_data = await get_user_profile(user_id)
        print(f"User data retrieved: {user_data}")

        # Analyze image
        cheek_metrics = await analyze_cheek_metrics(temp_url)
        print(f"Cheek analysis complete: {cheek_metrics}")

        # Generate improvement plan
        improvement_plan = await generate_improvement_plan(cheek_metrics, user_data)
        print(f"Improvement plan generated")

        # Prepare results
        analysis_result = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "cheek_metrics": cheek_metrics,
            "improvement_plan": improvement_plan,
            "status": "completed"
        }

        # Save to Supabase
        await save_analysis_to_supabase(analysis_result)
        print("Saved to Supabase successfully")

        # Clean up temporary file
        if temp_filepath.exists():
            temp_filepath.unlink()
            print("Temporary file cleaned up")

        return analysis_result

    except Exception as e:
        print(f"Error in analysis: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

@app.get("/temp-image/{file_name}")
async def serve_temp_image(file_name: str):
    """Serve temporary image file for AI analysis"""
    file_path = TEMP_DIR / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
