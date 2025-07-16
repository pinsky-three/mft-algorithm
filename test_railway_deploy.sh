#!/bin/bash

echo "🚀 Testing Railway Deployment Fixes..."

# Test 1: Build the Docker image
echo "📦 Building Docker image..."
if docker build -t freqtrade-test . > build.log 2>&1; then
    echo "✅ Docker build successful!"
else
    echo "❌ Docker build failed. Check build.log for details."
    exit 1
fi

# Test 2: Test container startup (dry run)
echo "🔄 Testing container startup..."
if docker run --rm -d --name freqtrade-test freqtrade-test > /dev/null 2>&1; then
    echo "✅ Container starts successfully!"
    docker stop freqtrade-test > /dev/null 2>&1
else
    echo "❌ Container startup failed."
    exit 1
fi

# Test 3: Test strategy loading
echo "📋 Testing strategy loading..."
if docker run --rm freqtrade-test list-strategies 2>/dev/null | grep -q "CryptoScalpingOptimizedJuly"; then
    echo "✅ July strategy loads successfully!"
else
    echo "❌ July strategy not found."
    exit 1
fi

echo ""
echo "🎉 All deployment tests passed!"
echo "🚀 Ready for Railway deployment!"
echo ""
echo "📝 Railway Deployment Steps:"
echo "1. Commit and push your changes to git"
echo "2. Railway will automatically rebuild with the fixed Dockerfile"
echo "3. The startup.sh issue should be resolved"
echo ""
echo "💡 If Railway deployment still fails, check the Railway logs for any missing environment variables or permissions." 