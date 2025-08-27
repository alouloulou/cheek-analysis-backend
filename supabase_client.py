import os
from typing import Dict, Any, Optional
from supabase import create_client, Client
import json
import uuid
from datetime import datetime, timedelta

# Supabase configuration


SUPABASE_URL = os.getenv("SUPABASE_URL", "your-token-here")
SERVICE_ROLE_KEY = os.getenv("SERVICE_ROLE_KEY", "your-token-here")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

async def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Get user profile data from Supabase for personalized recommendations

    Args:
        user_id: The user's UUID

    Returns:
        Dict containing user profile data
    """
    try:
        print(f"Getting user profile for: {user_id}")
        # Get user profile from profiles table
        #response = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
        response = supabase.table('profiles').select('*').eq('id', user_id).maybe_single().execute()
        print(f"Supabase response: {response}")
        
        if response.data:
            profile = response.data
            print(f"Retrieved profile data: {profile}")

            # Calculate derived values from real user data
            diet_quality = profile.get('diet_quality')
            hydration = f"{diet_quality * 0.3 + 1.5:.1f}L" if diet_quality else "2.5L"  # 1.5-4.5L based on diet quality
            sugar_score = 10 - diet_quality if diet_quality else 5

            # Format user data for AI analysis using REAL data from database
            user_data = {
                "user_lifestyle_information": {
                    "age": profile.get('age'),
                    "sex": profile.get('gender'),
                    "ethnicity": profile.get('ethnicity'),
                    "hydration": hydration,
                    "sleep_quality": f"{profile.get('sleep_hours')} hours" if profile.get('sleep_hours') else None,
                    "physical_activity": profile.get('exercise_frequency'),
                    "posture": f"{profile.get('stress_level')} for 0=Very poor - 10=Excellent" if profile.get('stress_level') else None,
                    "smoking_alcohol": f"{profile.get('smoking_habits', 'no smoking')} {profile.get('alcohol_consumption', 'no alcohol')}",
                    "sun_exposure": profile.get('sun_exposure'),
                    "protein_intake": profile.get('protein_intake'),
                    "collagen_vitamin_C": profile.get('collagen_vitamin_c'),
                    "sugar_processed_food": f"{sugar_score} for 0=Very high intake - 10=Very low intake",
                    "facial_exercises": profile.get('facial_exercises'),
                    "massage_skincare": "yes" if profile.get('massage_skincare', 0) > 5 else "no",
                    "weight_changes": profile.get('weight_changes')
                }
            }

            print(f"Formatted user data for AI: {user_data}")
            
            return user_data
        else:
            # Return default user data if profile not found
            return get_default_user_data()
            
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return get_default_user_data()

def get_default_user_data() -> Dict[str, Any]:
    """Return default user data when profile is not available"""
    return {
        "user_lifestyle_information": {
            "age": 25,
            "sex": "Unknown",
            "ethnicity": "Unknown",
            "hydration": "2.5L",
            "sleep_quality": "7 hours",
            "physical_activity": "3 times a week",
            "posture": "5 for 0=Very poor - 10=Excellent",
            "smoking_alcohol": "no smoking no alcohol",
            "sun_exposure": "10 mins a day",
            "protein_intake": "moderate",
            "collagen_vitamin_C": "moderate",
            "sugar_processed_food": "5 for 0=Very high intake - 10=Very low intake",
            "facial_exercises": "none",
            "massage_skincare": "no",
            "weight_changes": "65Kg"
        }
    }

async def save_analysis_to_supabase(analysis_result: Dict[str, Any]) -> bool:
    """
    Save analysis results to Supabase

    Args:
        analysis_result: Complete analysis result including metrics and plan

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Prepare data for user_analyses table (matching actual schema)
        analysis_data = {
            "user_id": analysis_result["user_id"],
            "analysis_data": analysis_result["cheek_metrics"],
            "recommendations": analysis_result["improvement_plan"],
            "scores": {
                "overall_score": calculate_overall_score(analysis_result["cheek_metrics"]),
                "improvement_potential": calculate_improvement_potential(analysis_result["cheek_metrics"])
            },
            "analysis_date": analysis_result["timestamp"],
            "photo_url": None,  # We're not storing photos in Supabase anymore
            "photo_path": None,
            "device_info": {"platform": "mobile_app"},
            "app_version": "1.0.0"
        }
        
        # Insert into user_analyses table
        print(f"Inserting analysis data: {analysis_data}")
        response = supabase.table('user_analyses').insert(analysis_data).execute()
        print(f"Insert response: {response}")

        if response.data:
            print(f"Analysis saved successfully for user {analysis_result['user_id']}")
            return True
        else:
            print(f"Failed to save analysis: {response}")
            return False
            
    except Exception as e:
        print(f"Error saving analysis to Supabase: {e}")
        return False

def calculate_overall_score(cheek_metrics: Dict[str, Any]) -> float:
    """Calculate overall cheek score from individual metrics"""
    try:
        scores = [
            cheek_metrics.get('cheek_lift', 0),
            cheek_metrics.get('cheek_fullness', 0),
            cheek_metrics.get('smile_symmetry', 0),
            cheek_metrics.get('muscle_tone', 0),
            cheek_metrics.get('elasticity_sagging', 0)
        ]
        
        # Filter out any non-numeric values
        numeric_scores = [score for score in scores if isinstance(score, (int, float))]
        
        if numeric_scores:
            return round(sum(numeric_scores) / len(numeric_scores), 1)
        else:
            return 6.0  # Default score
            
    except Exception as e:
        print(f"Error calculating overall score: {e}")
        return 6.0

def calculate_improvement_potential(cheek_metrics: Dict[str, Any]) -> float:
    """Calculate improvement potential based on current metrics"""
    try:
        overall_score = calculate_overall_score(cheek_metrics)
        
        # Higher improvement potential for lower current scores
        if overall_score < 5:
            return 9.0
        elif overall_score < 7:
            return 8.0
        elif overall_score < 8:
            return 7.0
        else:
            return 6.0
            
    except Exception as e:
        print(f"Error calculating improvement potential: {e}")
        return 7.5

async def get_user_analyses(user_id: str, limit: int = 10) -> list:
    """
    Get user's previous analyses
    
    Args:
        user_id: The user's UUID
        limit: Maximum number of analyses to return
        
    Returns:
        List of analysis records
    """
    try:
        response = supabase.table('user_analyses').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        
        return response.data if response.data else []
        
    except Exception as e:
        print(f"Error fetching user analyses: {e}")
        return []

# Image Storage Functions

async def upload_image_to_supabase(image_data: bytes, file_extension: str) -> Optional[str]:
    """
    Upload image to Supabase Storage and return public URL
    
    Args:
        image_data: Raw image bytes
        file_extension: File extension (e.g., 'jpg', 'png')
        
    Returns:
        Public URL of uploaded image or None if failed
    """
    try:
        # Ensure bucket exists
        await ensure_images_bucket_exists()
        
        # Generate unique filename
        image_id = str(uuid.uuid4())
        filename = f"temp_analysis/{image_id}.{file_extension}"
        
        print(f"Uploading image to Supabase Storage: {filename}")
        
        # Upload to Supabase Storage bucket 'images'
        response = supabase.storage.from_("images").upload(filename, image_data)
        
        if response:
            print(f"Image uploaded successfully: {filename}")
            
            # Get public URL
            public_url = supabase.storage.from_("images").get_public_url(filename)
            print(f"Public URL: {public_url}")
            
            return public_url
        else:
            print(f"Failed to upload image: {response}")
            return None
            
    except Exception as e:
        print(f"Error uploading image to Supabase: {e}")
        return None

async def ensure_images_bucket_exists():
    """
    Ensure the 'images' bucket exists, create it if it doesn't
    """
    try:
        # Try to list buckets to check if 'images' exists
        buckets = supabase.storage.list_buckets()
        
        bucket_exists = any(bucket['name'] == 'images' for bucket in buckets)
        
        if not bucket_exists:
            print("Creating 'images' bucket...")
            # Create the bucket
            result = supabase.storage.create_bucket('images', {'public': True})
            if result:
                print("Successfully created 'images' bucket")
            else:
                print("Failed to create 'images' bucket")
        else:
            print("'images' bucket already exists")
            
    except Exception as e:
        print(f"Error checking/creating bucket: {e}")
        # Continue anyway - the upload will fail with a clear error if bucket doesn't exist

async def delete_image_from_supabase(image_url: str) -> bool:
    """
    Delete image from Supabase Storage using its URL
    
    Args:
        image_url: Public URL of the image to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Extract filename from URL
        # URL format: https://[project].supabase.co/storage/v1/object/public/images/temp_analysis/[uuid].[ext]
        if "/images/" in image_url:
            # Split by /images/ and get the path after it
            filename = image_url.split("/images/")[-1]
            
            # Remove any query parameters (everything after ?)
            if "?" in filename:
                filename = filename.split("?")[0]
            
            print(f"Deleting image from Supabase Storage: {filename}")
            
            # Delete from Supabase Storage
            response = supabase.storage.from_("images").remove([filename])
            
            if response:
                print(f"Image deleted successfully: {filename}")
                return True
            else:
                print(f"Failed to delete image: {response}")
                return False
        else:
            print(f"Invalid image URL format: {image_url}")
            return False
            
    except Exception as e:
        print(f"Error deleting image from Supabase: {e}")
        return False

async def cleanup_old_temp_images() -> int:
    """
    Clean up temporary images older than 1 hour from Supabase Storage
    
    Returns:
        Number of images cleaned up
    """
    try:
        print("Starting cleanup of old temporary images")
        
        # List all files in temp_analysis folder
        response = supabase.storage.from_("images").list("temp_analysis")
        
        if not response:
            print("No files found in temp_analysis folder")
            return 0
            
        files_to_delete = []
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        for file_info in response:
            # Check if file is older than 1 hour
            created_at = datetime.fromisoformat(file_info['created_at'].replace('Z', '+00:00'))
            if created_at < cutoff_time:
                files_to_delete.append(f"temp_analysis/{file_info['name']}")
        
        if files_to_delete:
            print(f"Deleting {len(files_to_delete)} old temporary images")
            delete_response = supabase.storage.from_("images").remove(files_to_delete)
            
            if delete_response:
                print(f"Successfully cleaned up {len(files_to_delete)} old images")
                return len(files_to_delete)
            else:
                print(f"Failed to delete old images: {delete_response}")
                return 0
        else:
            print("No old images to clean up")
            return 0
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return 0
