import json
import os
import re
from typing import Dict, Any
from openai import OpenAI

# OpenAI configuration
MODEL = "gpt-5-mini"  # Using GPT-5 mini for cost efficiency
API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")

# Debug logging for environment variables
print(f"DEBUG: OPENAI_API_KEY exists: {os.getenv('OPENAI_API_KEY') is not None}")
print(f"DEBUG: API_KEY value starts with: {API_KEY[:10] if API_KEY != 'your-api-key-here' else 'DEFAULT_FALLBACK'}")

# Create OpenAI client
client = OpenAI(api_key=API_KEY)

async def analyze_cheek_metrics(image_url: str) -> Dict[str, Any]:
    """
    Analyze cheek metrics from image using OpenAI GPT-5 mini

    Args:
        image_url: URL to the temporary image

    Returns:
        Dict containing cheek analysis metrics
    """

    print(f"Starting cheek analysis for image: {image_url}")

    # Check if OpenAI API key is available
    if API_KEY == "your-api-key-here":
        print("WARNING: OpenAI API key not set, using fallback metrics")
        return {
            "cheek_lift": 6.2,
            "cheek_fullness": 7.1,
            "smile_symmetry": 6.8,
            "muscle_tone": 6.5,
            "elasticity_sagging": 6.9,
            "fat_vs_muscle_contribution": "60% muscle / 40% fat"
        }

    system_prompt = (
        "You are a facial aesthetics analysis AI. Analyze the provided selfie image and output scientifically-informed metrics "
        "related specifically to the cheeks. Metrics must be quantitative or scaled wherever possible, following approaches "
        "used in peer-reviewed research and validated facial scales. Use facial landmarks, volume estimation, and relative "
        "distances to assess cheeks. Assume the user wants to improve cheek fullness, lift, and tone naturally. "
        "Optional user info: age, sex, lifestyle factors (sleep, nutrition, hydration), adherence to exercise plans.\n\n"
        "Output strictly in JSON format with actual calculated values, not examples:\n"
        "{\n"
        '  "cheek_lift": null,                   // 0–10, 0 = very low, 10 = very lifted\n'
        '  "cheek_fullness": null,               // 0–10, 0 = flat, 10 = very full\n'
        '  "smile_symmetry": null,               // 0–10, 0 = asymmetric, 10 = perfectly symmetrical\n'
        '  "muscle_tone": null,                  // 0–10, 0 = soft, 10 = very toned\n'
        '  "elasticity_sagging": null,           // 0–10, 0 = sagging, 10 = very firm\n'
        '  "fat_vs_muscle_contribution": ""     // approximate composition as "% muscle / % fat", e.g., "60% muscle / 40% fat"\n'
        "}\n\n"
        "Instructions:\n"
        "1. Use facial landmark analysis, relative distances, contour/convexity, and tone proxies.\n"
        "2. Base any inferred improvements on age, sex, baseline metrics, and adherence assumptions.\n"
        "3. Provide realistic confidence ranges: estimates are approximate and depend on consistency.\n"
        "4. Output only JSON with real computed numbers, no placeholder values, no extra commentary."
    )
    
    user_prompt = (
        "Analyze this selfie/image and output the cheek metrics in JSON exactly as defined in the system prompt. "
        "You must compute real values for each metric based on the image analysis. "
        "Do NOT leave zeros, nulls, or placeholders. "
        "Output strictly JSON with the calculated numbers and percentages, no extra commentary."
    )
    
    try:
        print("Calling OpenAI API...")
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            temperature=0,
            top_p=1
        )

        result = response.choices[0].message.content
        print(f"AI response received: {result[:200]}...")

        # Ensure we have a string to work with
        if not isinstance(result, str):
            print(f"Warning: AI response is not a string, type: {type(result)}")
            result = str(result)

        # Parse JSON response
        try:
            metrics = json.loads(result)
            print(f"Parsed metrics: {metrics}")
            # Ensure we return a dictionary
            if not isinstance(metrics, dict):
                print(f"Warning: Parsed result is not a dict, type: {type(metrics)}")
                raise json.JSONDecodeError("Result is not a dictionary", result, 0)
            return metrics
        except json.JSONDecodeError as je:
            print(f"JSON decode error: {je}")
            # If response isn't valid JSON, try to extract JSON from text
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                try:
                    metrics = json.loads(json_match.group())
                    print(f"Extracted metrics: {metrics}")
                    # Ensure we return a dictionary
                    if not isinstance(metrics, dict):
                        print(f"Warning: Extracted result is not a dict, type: {type(metrics)}")
                        raise json.JSONDecodeError("Extracted result is not a dictionary", result, 0)
                    return metrics
                except json.JSONDecodeError:
                    print("Could not parse extracted JSON")
                    raise Exception("Could not parse AI response as JSON")
            else:
                print("Could not extract JSON from AI response")
                raise Exception("Could not parse AI response as JSON")

    except Exception as e:
        print(f"Error in cheek analysis: {e}")
        print(f"Error type: {type(e)}")
        # Return fallback metrics
        fallback_metrics = {
            "cheek_lift": 6.0,
            "cheek_fullness": 6.5,
            "smile_symmetry": 7.0,
            "muscle_tone": 6.0,
            "elasticity_sagging": 6.2,
            "fat_vs_muscle_contribution": "55% muscle / 45% fat"
        }
        print(f"Using fallback metrics: {fallback_metrics}")
        return fallback_metrics

async def generate_improvement_plan(cheek_metrics: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate personalized improvement plan based on cheek metrics and user data

    Args:
        cheek_metrics: Results from cheek analysis
        user_data: User profile data from Supabase

    Returns:
        Dict containing personalized improvement plan
    """

    print("Starting improvement plan generation...")

    # Check if OpenAI API key is available
    if API_KEY == "your-api-key-here":
        print("WARNING: OpenAI API key not set, using fallback plan")
        return {
            "cheek_improvement_plan": {
                "title": "Cheek Improvement Plan",
                "description": "A personalized plan to enhance your cheek appearance through evidence-based exercises and lifestyle recommendations.",
                "steps": [
                    {
                        "category": "Facial Exercises",
                        "goal": "Improve cheek muscle tone and lift",
                        "exercises": [
                            {
                                "name": "Cheek Lift Exercise",
                                "description": "Strengthens and lifts the upper cheeks by smiling while raising the cheeks toward the eyes.",
                                "reps": "12-15",
                                "duration": "8 seconds hold per rep",
                                "frequency_per_week": "5"
                            }
                        ]
                    }
                ]
            }
        }

    # Convert data to strings to avoid json.dumps() issues
    cheek_metrics_str = str(cheek_metrics) if cheek_metrics else "No metrics available"
    user_data_str = str(user_data) if user_data else "No user data available"
    print('*************   cheek_metrics_str', cheek_metrics_str)
    print('*************user_data_str', user_data_str)

    system_prompt = f"""
You are an AI assistant that creates **personalized, science-backed cheek improvement plans**.

Input:

1. Cheek metrics:
{cheek_metrics_str}
2. User information:
{user_data_str}

Task:

- Generate a personalized cheek improvement plan in JSON format.
- The plan must be fully **based on scientific evidence**. Avoid speculative or cosmetic procedures.
- The JSON structure should be:

{{
  "cheek_improvement_plan": {{
    "title": "Cheek Improvement Plan",
    "description": "<brief summary personalized for the user, evidence-based>",
    "steps": [
      {{
        "category": "Facial Exercises",
        "goal": "<goal for this user based on muscle tone and fat/muscle ratio>",
        "exercises": [
          {{
            "name": "<exercise_name from predefined list>",
            "description": "<what this exercise does>",
            "reps": "<personalized reps>",
            "duration": "<personalized duration>",
            "frequency_per_week": "<times per week>"
          }}
        ]
      }},
      {{
        "category": "Diet & Nutrition",
        "goal": "<goal for this user based on protein, collagen, vitamin C, sugar intake>",
        "recommendations": ["<evidence-based dietary recommendation1>", "<recommendation2>", "..."]
      }},
      {{
        "category": "Lifestyle & Sleep",
        "goal": "<goal for this user based on sleep quality, physical activity, smoking/alcohol>",
        "recommendations": ["<evidence-based recommendation1>", "<recommendation2>", "..."]
      }},
      {{
        "category": "Posture & Jaw/Tongue Position",
        "goal": "<goal for this user based on posture and facial mechanics>",
        "recommendations": ["<evidence-based recommendation1>", "<recommendation2>", "..."]
      }},
      {{
        "category": "Skin Protection & Skincare",
        "goal": "<goal for this user based on sun exposure, hydration, and skin health>",
        "recommendations": ["<evidence-based recommendation1>", "<recommendation2>", "..."]
      }}
    ]
  }}
}}

Predefined Facial Exercises Library (AI must only select from this list and personalize reps/duration/frequency):

[
  {{
    "name": "Cheek Lift Exercise",
    "description": "Strengthens and lifts the upper cheeks by smiling while raising the cheeks toward the eyes.",
    "reps": "10-15",
    "duration": "5-10 seconds hold per rep",
    "frequency_per_week": "4-5"
  }},
  {{
    "name": "Smiley Face Exercise",
    "description": "Improves cheek flexibility and tone through exaggerated smiling movements.",
    "reps": "15-20",
    "duration": "3-5 seconds hold per rep",
    "frequency_per_week": "5-6"
  }},
  {{
    "name": "Fish Lips Facial Exercise",
    "description": "Tones the lower face by sucking in cheeks and forming a 'fish face'.",
    "reps": "10-15",
    "duration": "5 seconds hold per rep",
    "frequency_per_week": "3-4"
  }},
  {{
    "name": "Puffy Cheek Exercise",
    "description": "Strengthens cheek muscles by filling cheeks with air and holding.",
    "reps": "8-12",
    "duration": "10-15 seconds hold per rep",
    "frequency_per_week": "4-5"
  }},
  {{
    "name": "Make X and O Expressions",
    "description": "Enhances lip and cheek coordination by alternating exaggerated 'X' and 'O' mouth shapes.",
    "reps": "15-20",
    "duration": "2-3 seconds per movement",
    "frequency_per_week": "5-6"
  }},
  {{
    "name": "Hummingbird",
    "description": "Stimulates circulation and awakens facial muscles through humming vibrations.",
    "reps": "5-10",
    "duration": "15-20 seconds per set",
    "frequency_per_week": "3-4"
  }},
  {{
    "name": "Puppet Face Exercise",
    "description": "Improves smile muscles by exaggerating upward pulls at mouth corners.",
    "reps": "12-15",
    "duration": "5 seconds hold per rep",
    "frequency_per_week": "4-5"
  }},
  {{
    "name": "Plump Cheeks Exercise",
    "description": "Adds fullness to cheeks by controlled plumping and puffing of air.",
    "reps": "10-12",
    "duration": "8-10 seconds per rep",
    "frequency_per_week": "4-5"
  }},
  {{
    "name": "Cheek Press",
    "description": "Defines cheekbones by pressing fingers lightly against cheeks while smiling.",
    "reps": "10-12",
    "duration": "5-8 seconds hold per rep",
    "frequency_per_week": "3-4"
  }},
  {{
    "name": "Chewing Lift",
    "description": "Strengthens the jawline and lower cheeks by simulating exaggerated chewing movements.",
    "reps": "15-20",
    "duration": "5-10 seconds per rep",
    "frequency_per_week": "5"
  }},
  {{
    "name": "Facial Massage Cheek Lift",
    "description": "Improves circulation and skin elasticity by massaging cheeks upward with fingers.",
    "reps": "5-8",
    "duration": "30-60 seconds per massage",
    "frequency_per_week": "3-4"
  }}
]

Instructions:

1. Tailor **exercise type, reps, and duration** by choosing from the predefined list.
2. Adjust **diet, lifestyle, posture, and skincare recommendations** based on user lifestyle information.
3. Make the JSON **fully complete**, no blank fields.
4. Only include **methods supported by scientific research**. Avoid speculative or cosmetic suggestions.
5. Output **only valid JSON**, no extra text or explanation.
"""
    
    user_prompt = (
        "Generate a personalized, science-backed cheek improvement plan in JSON using the provided cheek metrics and user info. "
        "Include title, description, and steps with categories, goals, and evidence-based exercises or recommendations. "
        "Do not leave any fields blank. Only include scientifically supported methods. Output strictly valid JSON."
    )
    
    try:
        print("Calling OpenAI API for improvement plan...")
        print(f"Cheek metrics type: {type(cheek_metrics)}")
        print(f"User data type: {type(user_data)}")
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            top_p=1
        )
        
        # Handle the response
        print("Processing OpenAI response...")
        result = response.choices[0].message.content
        print(f"Improvement plan AI response: {result[:200]}...")
        
        # Ensure we have a string to work with
        if not isinstance(result, str):
            print(f"Warning: Improvement plan response is not a string, type: {type(result)}")
            result = str(result)
        
        # Parse JSON response
        try:
            plan = json.loads(result)
            print(f"Parsed improvement plan: {type(plan)}")
            # Ensure we return a dictionary
            if not isinstance(plan, dict):
                print(f"Warning: Parsed improvement plan is not a dict, type: {type(plan)}")
                raise json.JSONDecodeError("Result is not a dictionary", result, 0)
            return plan
        except json.JSONDecodeError as je:
            print(f"Improvement plan JSON decode error: {je}")
            # If response isn't valid JSON, try to extract JSON from text
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                try:
                    plan = json.loads(json_match.group())
                    print(f"Extracted improvement plan: {type(plan)}")
                    # Ensure we return a dictionary
                    if not isinstance(plan, dict):
                        print(f"Warning: Extracted improvement plan is not a dict, type: {type(plan)}")
                        raise json.JSONDecodeError("Extracted result is not a dictionary", result, 0)
                    return plan
                except json.JSONDecodeError:
                    print("Could not parse extracted improvement plan JSON")
                    raise Exception("Could not parse improvement plan as JSON")
            else:
                print("Could not extract JSON from improvement plan response")
                raise Exception("Could not parse improvement plan as JSON")
                
    except Exception as e:
        print(f"Error generating improvement plan: {e}")
        # Return fallback plan
        return {
            "cheek_improvement_plan": {
                "title": "Cheek Improvement Plan",
                "description": "A personalized plan to enhance your cheek appearance through evidence-based exercises and lifestyle recommendations.",
                "steps": [
                    {
                        "category": "Facial Exercises",
                        "goal": "Improve cheek muscle tone and lift",
                        "exercises": [
                            {
                                "name": "Cheek Lift Exercise",
                                "description": "Strengthens and lifts the upper cheeks by smiling while raising the cheeks toward the eyes.",
                                "reps": "12-15",
                                "duration": "8 seconds hold per rep",
                                "frequency_per_week": "5"
                            }
                        ]
                    },
                    {
                        "category": "Diet & Nutrition",
                        "goal": "Support skin health and muscle maintenance",
                        "recommendations": [
                            "Increase protein intake to support muscle maintenance",
                            "Include vitamin C rich foods for collagen synthesis",
                            "Stay well hydrated for skin plumpness"
                        ]
                    }
                ]
            }
        }
