#!/usr/bin/env python3
"""
Startup script for the Cheek Analysis Backend
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import azure.ai.inference
        import supabase
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_environment():
    """Check if environment variables are set"""
    required_vars = ['AZURE_AI_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file or set these environment variables")
        return False
    
    print("✅ Environment variables are set")
    return True

def create_directories():
    """Create necessary directories"""
    temp_dir = Path("temp_images")
    temp_dir.mkdir(exist_ok=True)
    print("✅ Created temp_images directory")

def main():
    """Main startup function"""
    print("🚀 Starting Cheek Analysis Backend...")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        print("\n💡 Tip: Copy .env.example to .env and fill in your credentials")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("\n✅ All checks passed!")
    print("🌐 Starting server at http://localhost:8000")
    print("📚 API docs available at http://localhost:8000/docs")
    print("=" * 50)
    
    # Start the server
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
