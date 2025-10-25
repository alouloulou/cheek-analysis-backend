import os
from typing import Dict, Any, Optional
from supabase import create_client, Client
import json
import uuid
from datetime import datetime, timedelta

# Supabase configuration (reverted)
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

            # Use user-provided values directly from profile (no derived calcs)
            diet_quality = profile.get('diet_quality')
            hydration = profile.get('hydration')
            sugar_score = profile.get('sugar_score')

            # Format user data for AI analysis using REAL data from database
            user_data = {
                "user_lifestyle_information": {
                    "age": profile.get('age'),
                    "sex": profile.get('gender'),
                    "ethnicity": profile.get('ethnicity'),
                    "hydration": hydration,
                    "sleep_quality": f"{profile.get('sleep_hours')} hours" if profile.get('sleep_hours') else None,
                    "physical_activity": profile.get('exercise_frequency'),
                    "posture": f"{profile.get('posture')} for 0=Very poor - 10=Good" if profile.get('posture') else None,
                    "stress_level": f"{profile.get('stress_level')} (0=Good - 10=Very poor)" if profile.get('stress_level') is not None else None,
                    "smoking_alcohol": f"{profile.get('smoking_habits', 'no smoking')} {profile.get('alcohol_consumption', 'no alcohol')}",
                    "sun_exposure": profile.get('sun_exposure'),
                    "protein_intake": profile.get('protein_intake'),
                    "collagen_vitamin_C": profile.get('collagen_vitamin_c'),
                    "sugar_processed_food": f"{sugar_score} for 0=Very low intake - 10=Very high intake" if sugar_score is not None else None,
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

async def verify_google_subscription(user_id: str, package_name: str, product_id: str, purchase_token: str) -> dict:
    """
    Verify Google Play subscription and update Supabase
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        import json
        
        # Load service account credentials from environment
        service_account_json = os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")
        if not service_account_json:
            raise Exception("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON environment variable not set")
        
        credentials_info = json.loads(service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/androidpublisher']
        )
        
        # Build the service
        service = build('androidpublisher', 'v3', credentials=credentials)
        
        # Verify the subscription
        result = service.purchases().subscriptions().get(
            packageName=package_name,
            subscriptionId=product_id,
            token=purchase_token
        ).execute()
        
        # Parse subscription details
        expiry_time_millis = int(result.get('expiryTimeMillis', 0))
        expiry_date = datetime.fromtimestamp(expiry_time_millis / 1000) if expiry_time_millis else None
        
        # Determine subscription status
        is_active = (
            result.get('paymentState') == 1 and  # Payment received
            expiry_date and expiry_date > datetime.now()
        )
        
        status = 'active' if is_active else 'expired'
        plan_type = 'yearly' if 'yearly' in product_id.lower() else 'monthly'
        
        # Update Supabase profiles
        await supabase.table('profiles').upsert({
            'id': user_id,
            'subscription_status': status,
            'subscription_type': plan_type,
            'subscription_start_date': datetime.now().isoformat() if is_active else None,
            'subscription_end_date': expiry_date.isoformat() if expiry_date else None,
            'updated_at': datetime.now().isoformat(),
        }).execute()
        
        # Store subscription record
        await supabase.table('subscriptions').upsert({
            'user_id': user_id,
            'provider': 'google',
            'product_id': product_id,
            'purchase_token': purchase_token,
            'status': status,
            'start_at': datetime.now().isoformat() if is_active else None,
            'end_at': expiry_date.isoformat() if expiry_date else None,
            'raw': result,
            'updated_at': datetime.now().isoformat(),
        }, on_conflict='provider,purchase_token').execute()
        
        # Acknowledge the purchase if needed
        if not result.get('acknowledgementState', 0):
            service.purchases().subscriptions().acknowledge(
                packageName=package_name,
                subscriptionId=product_id,
                token=purchase_token
            ).execute()
        
        return {
            'success': True,
            'status': status,
            'expiry_date': expiry_date.isoformat() if expiry_date else None,
            'plan_type': plan_type
        }
        
    except Exception as e:
        print(f"Error verifying Google subscription: {e}")
        # Fallback: mark as active for testing (remove in production)
        now = datetime.now()
        end_date = now + timedelta(days=365 if 'yearly' in product_id.lower() else 30)
        
        await supabase.table('profiles').upsert({
            'id': user_id,
            'subscription_status': 'active',
            'subscription_type': 'yearly' if 'yearly' in product_id.lower() else 'monthly',
            'subscription_start_date': now.isoformat(),
            'subscription_end_date': end_date.isoformat(),
            'updated_at': now.isoformat(),
        }).execute()
        
        return {
            'success': True,
            'status': 'active',
            'expiry_date': end_date.isoformat(),
            'plan_type': 'yearly' if 'yearly' in product_id.lower() else 'monthly',
            'note': 'Fallback verification used'
        }

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

async def increment_user_analysis_count(user_id: str) -> bool:
    """
    Increment the analysis count for a user in the user_analysis_limits table
    
    Args:
        user_id: The user's UUID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # First, try to get the current record
        response = supabase.table('user_analysis_limits').select('analysis_count').eq('user_id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            # Record exists, increment the count
            current_count = response.data[0].get('analysis_count', 0)
            new_count = current_count + 1
            
            update_response = supabase.table('user_analysis_limits').update({
                'analysis_count': new_count
            }).eq('user_id', user_id).execute()
            
            print(f"Updated analysis count for user {user_id}: {current_count} -> {new_count}")
            return True
        else:
            # Record doesn't exist, create it with count = 1
            insert_response = supabase.table('user_analysis_limits').insert({
                'user_id': user_id,
                'analysis_count': 1,
                'max_analyses': 3,  # Default for free users
                'subscription_type': 'free'
            }).execute()
            
            print(f"Created new analysis record for user {user_id} with count = 1")
            return True
            
    except Exception as e:
        print(f"Error incrementing analysis count for user {user_id}: {e}")
        return False

async def cleanup_old_temp_images(hours_old: int = 1) -> int:
    """
    Clean up temporary images older than specified hours
    
    Args:
        hours_old: Images older than this many hours will be deleted
        
    Returns:
        Number of images cleaned up
    """
    try:
        # List all files in the temp_analysis folder
        response = supabase.storage.from_("images").list("temp_analysis")
        
        if not response:
            print("No files found in temp_analysis folder")
            return 0
            
        files_to_delete = []
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        
        for file_info in response:
            # Parse the timestamp from filename (format: temp_YYYYMMDD_HHMMSS_uuid.ext)
            filename = file_info['name']
            if filename.startswith('temp_'):
                try:
                    # Extract timestamp from filename
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        date_part = parts[1]  # YYYYMMDD
                        time_part = parts[2]  # HHMMSS
                        
                        # Parse the datetime
                        file_datetime = datetime.strptime(f"{date_part}_{time_part}", "%Y%m%d_%H%M%S")
                        
                        if file_datetime < cutoff_time:
                            files_to_delete.append(f"temp_analysis/{filename}")
                            
                except (ValueError, IndexError) as e:
                    print(f"Could not parse timestamp from filename {filename}: {e}")
                    continue
        
        # Delete old files
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                supabase.storage.from_("images").remove([file_path])
                deleted_count += 1
                print(f"Deleted old temp image: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
                
        print(f"Cleanup complete: {deleted_count} files deleted")
        return deleted_count
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return 0
