from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any
import tempfile
from pathlib import Path

# Import our AI analysis functions
from ai_analysis import analyze_cheek_metrics, generate_improvement_plan
from supabase_client import save_analysis_to_supabase

app = FastAPI(title="Cheek Analysis API", version="1.0.0")

# Enable CORS for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Flutter app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store temporary images
TEMP_DIR = Path("temp_images")
TEMP_DIR.mkdir(exist_ok=True)

# Store temporary image URLs for AI access
temp_image_store: Dict[str, str] = {}

@app.get("/")
async def root():
    return {"message": "Cheek Analysis API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cheek-analysis-backend"}

@app.post("/test-analyze")
async def test_analyze():
    """Test endpoint to check if analysis pipeline works without image upload"""
    try:
        print("Testing analysis pipeline...")

        # Test user data retrieval
        user_data = await get_user_data_from_supabase("test-user-id")
        print(f"User data test: {user_data}")

        # Test with mock metrics
        mock_metrics = {
            "cheek_lift": 6.2,
            "cheek_fullness": 7.1,
            "smile_symmetry": 6.8,
            "muscle_tone": 6.5,
            "elasticity_sagging": 6.9,
            "fat_vs_muscle_contribution": "60% muscle / 40% fat"
        }

        # Test improvement plan generation
        improvement_plan = await generate_improvement_plan(mock_metrics, user_data)
        print(f"Improvement plan test: {improvement_plan}")

        return {
            "status": "success",
            "user_data": user_data,
            "mock_metrics": mock_metrics,
            "improvement_plan": improvement_plan
        }

    except Exception as e:
        print(f"Test error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}

@app.post("/analyze")
async def analyze_image(
    user_id: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Analyze uploaded image and return cheek metrics + improvement plan
    """
    analysis_id = None
    try:
        print(f"Starting analysis for user: {user_id}")

        # Validate image
        if not image.content_type.startswith('image/'):
            print(f"Invalid image type: {image.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")

        # Generate unique ID for this analysis
        analysis_id = str(uuid.uuid4())
        print(f"Generated analysis ID: {analysis_id}")

        # Save image temporarily
        file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        temp_filename = f"{analysis_id}.{file_extension}"
        temp_filepath = TEMP_DIR / temp_filename

        # Write uploaded file to temporary location
        with open(temp_filepath, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        print(f"Saved temporary image: {temp_filepath}")

        # Create temporary URL for AI access
        temp_url = f"https://cheek-analysis-backend.onrender.com/temp-image/{analysis_id}"
        temp_image_store[analysis_id] = str(temp_filepath)
        print(f"Created temp URL: {temp_url}")

        # Get user data from Supabase (for personalized recommendations)
        print("Getting user data from Supabase...")
        user_data = await get_user_data_from_supabase(user_id)
        print(f"User data retrieved: {user_data}")

        # Analyze image with AI
        print("Starting AI analysis...")
        cheek_metrics = await analyze_cheek_metrics(temp_url)
        print(f"AI analysis complete: {cheek_metrics}")

        # Generate personalized improvement plan
        print("Generating improvement plan...")
        improvement_plan = await generate_improvement_plan(cheek_metrics, user_data)
        print("Improvement plan generated")

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
        print("Saving to Supabase...")
        await save_analysis_to_supabase(analysis_result)
        print("Saved to Supabase successfully")

        # Clean up temporary file
        cleanup_temp_file(analysis_id)
        print("Analysis completed successfully")

        return analysis_result

    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

        # Clean up on error
        if analysis_id:
            cleanup_temp_file(analysis_id)

        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/temp-image/{image_id}")
async def serve_temp_image(image_id: str):
    """Serve temporary image for AI analysis"""
    if image_id not in temp_image_store:
        raise HTTPException(status_code=404, detail="Image not found")
    
    filepath = temp_image_store[image_id]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image file not found")
    
    return FileResponse(filepath)

def cleanup_temp_file(analysis_id: str):
    """Clean up temporary files"""
    try:
        if analysis_id in temp_image_store:
            filepath = temp_image_store[analysis_id]
            if os.path.exists(filepath):
                os.remove(filepath)
            del temp_image_store[analysis_id]
    except Exception as e:
        print(f"Error cleaning up temp file: {e}")

async def get_user_data_from_supabase(user_id: str) -> Dict[str, Any]:
    """Get user profile data from Supabase for personalized recommendations"""
    # This will be implemented in supabase_client.py
    from supabase_client import get_user_profile
    return await get_user_profile(user_id)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
