#!/bin/bash

# Kolkata AQI Navigation System - Deployment Script
echo "🚀 Starting deployment process..."

# Check if we're in the right directory
if [ ! -f "backend/multi_route_api.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Please create it with your Maps_API_KEY"
    exit 1
fi

# Check if Maps_API_KEY is set
if ! grep -q "Maps_API_KEY=" .env || grep -q "YOUR_KEY_HERE" .env; then
    echo "❌ Error: Maps_API_KEY not set in .env file"
    exit 1
fi

echo "✅ Environment check passed"

# Stage backend files for deployment
echo "📦 Staging backend files..."
git add backend/Procfile backend/requirements.txt backend/multi_route_api.py
git add frontend/config.js frontend/index.html frontend/multi_route.html
git add frontend/js/api.js

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "📝 No changes to commit"
else
    echo "📝 Committing changes..."
    git commit -m "Add production deployment files and configuration"
fi

echo ""
echo "🎯 Ready for deployment!"
echo ""
echo "📋 Next Steps:"
echo "1. Push to GitHub: git push origin main"
echo "2. Deploy backend on Railway:"
echo "   - Go to railway.app"
echo "   - Connect your GitHub repository"
echo "   - Add Maps_API_KEY environment variable"
echo "   - Deploy"
echo ""
echo "3. Deploy frontend on Vercel:"
echo "   - Go to vercel.com"
echo "   - Connect your GitHub repository"
echo "   - Deploy"
echo ""
echo "4. Update frontend/config.js with your Railway URL"
echo ""
echo "📚 For detailed instructions, see: DEPLOY_NOW.md"
echo ""
echo "🎉 Your AQI Navigation System will be live soon!"
