from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import uuid
from datetime import datetime
from pathlib import Path

# Import your AI analysis functions
from ai_analysis import analyze_cheek_metrics, generate_improvement_plan
from supabase_client import (
    save_analysis_to_supabase, 
    upload_image_to_supabase, 
    delete_image_from_supabase,
    cleanup_old_temp_images
)

app = FastAPI(title="Cheek Analysis API", version="1.0.0")

# Enable CORS for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep temp directory for backward compatibility (can be removed later)
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
    image_url = None
    try:
        print(f"Starting analysis for user: {user_id}")

        # Validate image type
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        print(f"Accepted image type: {image.content_type}")

        # Generate unique ID and get file extension
        analysis_id = str(uuid.uuid4())
        file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
        
        # Read image data
        image_data = await image.read()
        print(f"Read image data: {len(image_data)} bytes")

        # Upload image to Supabase Storage
        image_url = await upload_image_to_supabase(image_data, file_extension)
        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to upload image to storage")
        print(f"Image uploaded to Supabase: {image_url}")

        # Get user data from Supabase
        from supabase_client import get_user_profile
        user_data = await get_user_profile(user_id)
        print(f"User data retrieved: {user_data}")

        # Analyze image using Supabase URL
        cheek_metrics = await analyze_cheek_metrics(image_url)
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

        # Delete image from Supabase Storage after processing
        deletion_success = await delete_image_from_supabase(image_url)
        if deletion_success:
            print("Image deleted from Supabase Storage successfully")
        else:
            print("Warning: Failed to delete image from storage")

        return analysis_result

    except Exception as e:
        print(f"Error in analysis: {e}")
        import traceback
        print(traceback.format_exc())
        
        # Clean up image from storage if upload succeeded but analysis failed
        if image_url:
            try:
                await delete_image_from_supabase(image_url)
                print("Cleaned up image from storage after error")
            except:
                print("Failed to clean up image after error")
        
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

@app.post("/cleanup-images")
async def cleanup_temp_images():
    """
    Manually trigger cleanup of old temporary images from Supabase Storage
    """
    try:
        cleaned_count = await cleanup_old_temp_images()
        return {
            "message": f"Cleanup completed successfully",
            "images_cleaned": cleaned_count
        }
    except Exception as e:
        print(f"Error during manual cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {e}")

@app.on_event("startup")
async def startup_event():
    """
    Run cleanup on startup to remove any leftover temporary images
    """
    try:
        print("Running startup cleanup of temporary images...")
        cleaned_count = await cleanup_old_temp_images()
        print(f"Startup cleanup completed: {cleaned_count} images removed")
    except Exception as e:
        print(f"Error during startup cleanup: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
