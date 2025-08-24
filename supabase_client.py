import os
from typing import Dict, Any, Optional
from supabase import create_client, Client
import json

# Supabase configuration
SUPABASE_URL = "https://ckgihnidyyvmuylhqqur.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrZ2lobmlkeXl2bXV5bGhxcXVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM2NDYwOTYsImV4cCI6MjA2OTIyMjA5Nn0.YODqZ9QXwQJWcNqYLn_yUA3KWsstluhKlQj6PYWZ3BI"

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
        response = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
        print(f"Supabase response: {response}")
        
        if response.data:
            profile = response.data
            
            # Format user data for AI analysis
            user_data = {
                "user_lifestyle_information": {
                    "age": profile.get('age', 25),
                    "sex": profile.get('gender', 'Unknown'),
                    "ethnicity": profile.get('ethnicity', 'Unknown'),
                    "hydration": f"{profile.get('diet_quality', 5)}L" if profile.get('diet_quality') else "2.5L",
                    "sleep_quality": f"{profile.get('sleep_hours', 7)} hours",
                    "physical_activity": profile.get('exercise_frequency', '3 times a week'),
                    "posture": f"{profile.get('stress_level', 5)} for 0=Very poor - 10=Excellent",
                    "smoking_alcohol": profile.get('smoking_habits', 'no smoking') + " " + profile.get('alcohol_consumption', 'no alcohol'),
                    "sun_exposure": "10 mins a day",  # Default value
                    "protein_intake": "moderate",  # Default value
                    "collagen_vitamin_C": "moderate",  # Default value
                    "sugar_processed_food": f"{10 - profile.get('diet_quality', 5)} for 0=Very high intake - 10=Very low intake",
                    "facial_exercises": profile.get('facial_exercises', 'none'),
                    "massage_skincare": "yes" if profile.get('massage_skincare', 0) > 5 else "no",
                    "weight_changes": f"{profile.get('age', 25) * 2.5}Kg"  # Estimated weight
                }
            }
            
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
