# Backend Deployment Guide

To make your app completely standalone, you need to deploy the backend to a cloud service. Here are the easiest options:

## Option 1: Render (Recommended - Free Tier Available)

### Steps:
1. **Create Render Account**: Go to [render.com](https://render.com) and sign up
2. **Connect GitHub**: Link your GitHub account
3. **Create Web Service**: 
   - Click "New" → "Web Service"
   - Connect your repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `python main.py`
   - Set environment variables:
     - `AZURE_AI_TOKEN`: Your Azure AI token
4. **Deploy**: Render will automatically deploy your backend
5. **Get URL**: Copy your service URL (e.g., `https://your-app.onrender.com`)

### Update Flutter App:
Replace the URL in `lib/pages/analysis_page.dart`:
```dart
backendUrl = 'https://your-actual-render-url.onrender.com';
```

## Option 2: Railway

### Steps:
1. **Create Railway Account**: Go to [railway.app](https://railway.app)
2. **Deploy from GitHub**: Connect your repository
3. **Set Environment Variables**: Add `AZURE_AI_TOKEN`
4. **Deploy**: Railway handles the rest
5. **Get URL**: Copy your service URL

## Option 3: Heroku

### Steps:
1. **Create Heroku Account**: Go to [heroku.com](https://heroku.com)
2. **Install Heroku CLI**
3. **Create app**: `heroku create your-app-name`
4. **Set environment variables**: `heroku config:set AZURE_AI_TOKEN=your-token`
5. **Deploy**: `git push heroku main`

## Option 4: Google Cloud Run

### Steps:
1. **Create Google Cloud Account**
2. **Enable Cloud Run API**
3. **Create Dockerfile** (see below)
4. **Deploy**: `gcloud run deploy`

### Dockerfile for Google Cloud Run:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

## Testing Your Deployment

1. **Test API**: Visit `https://your-deployed-url.com/docs` to see the API documentation
2. **Test Endpoint**: Try `https://your-deployed-url.com/` - should return `{"message": "Cheek Analysis API is running"}`
3. **Update Flutter**: Replace the backend URL in your Flutter app
4. **Test Mobile**: The app should now work on Android/iOS without depending on any computer

## Environment Variables Needed

All deployment platforms need these environment variables:
- `AZURE_AI_TOKEN`: Your Azure AI token for GPT-4.1 access
- `PORT`: Usually set automatically by the platform

## Cost Considerations

- **Render**: Free tier available (sleeps after 15 min of inactivity)
- **Railway**: $5/month for hobby plan
- **Heroku**: $7/month for basic dyno
- **Google Cloud Run**: Pay per request (very cheap for low usage)

## Recommended: Render Free Tier

For testing and development, Render's free tier is perfect:
- ✅ Free
- ✅ Easy setup
- ✅ Automatic deployments
- ⚠️ Sleeps after 15 minutes (first request takes ~30 seconds to wake up)

Once deployed, your app will be completely standalone and work on any device!
