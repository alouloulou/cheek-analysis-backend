# Cheek Analysis Backend

FastAPI backend for the Cheek Analysis mobile app. This backend receives image data from the Flutter app, analyzes it using Azure AI, and returns personalized cheek improvement recommendations.

## Features

- **Image Analysis**: Receives image bytes from Flutter app and serves them temporarily for AI analysis
- **AI Integration**: Uses Azure AI (GPT-4.1) for facial analysis and recommendation generation
- **Supabase Integration**: Stores analysis results and retrieves user profile data
- **Temporary Image Serving**: Creates temporary URLs for AI to access images without base64 encoding

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `AZURE_AI_TOKEN`: Your Azure AI token for GPT-4.1 access
- `SUPABASE_URL`: Your Supabase project URL (already set)
- `SUPABASE_KEY`: Your Supabase anon key (already set)

### 3. Run the Server

For development:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### POST /analyze

Analyzes an uploaded image and returns cheek metrics with improvement plan.

**Request:**
- `user_id` (form field): User's UUID from Supabase
- `image` (file): Image file (JPG/PNG)

**Response:**
```json
{
  "analysis_id": "uuid",
  "user_id": "user-uuid",
  "timestamp": "2024-01-01T12:00:00Z",
  "cheek_metrics": {
    "cheek_lift": 6.2,
    "cheek_fullness": 7.1,
    "smile_symmetry": 6.8,
    "muscle_tone": 6.5,
    "elasticity_sagging": 6.9,
    "fat_vs_muscle_contribution": "60% muscle / 40% fat"
  },
  "improvement_plan": {
    "cheek_improvement_plan": {
      "title": "Personalized Cheek Improvement Plan",
      "description": "...",
      "steps": [...]
    }
  },
  "status": "completed"
}
```

### GET /temp-image/{image_id}

Serves temporary images for AI analysis. These URLs are automatically generated and cleaned up after analysis.

## Architecture

1. **Flutter App** → Sends image bytes to `/analyze`
2. **Backend** → Saves image temporarily and creates URL
3. **Azure AI** → Analyzes image via temporary URL
4. **Backend** → Generates improvement plan based on user data
5. **Supabase** → Stores analysis results
6. **Backend** → Returns complete analysis to Flutter
7. **Cleanup** → Removes temporary files

## Deployment

### Local Development
- Backend runs on `http://localhost:8000`
- Update Flutter app's `backendUrl` to point to your local server

### Production
- Deploy to platforms like Render, Railway, or Heroku
- Update Flutter app's `backendUrl` to your production URL
- Ensure CORS settings allow your Flutter app's domain

## File Structure

```
backend/
├── main.py              # FastAPI app and main endpoints
├── ai_analysis.py       # Azure AI integration
├── supabase_client.py   # Supabase database operations
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── temp_images/        # Temporary image storage (auto-created)
└── README.md          # This file
```

## Notes

- Temporary images are automatically cleaned up after analysis
- The AI model expects specific prompt formats for consistent results
- User profile data from Supabase is used to personalize recommendations
- All analysis results are stored in Supabase for future reference
