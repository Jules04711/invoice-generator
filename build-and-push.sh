#!/bin/bash

# Build and Deploy Script for Invoice Generator (Local)
# This script builds the Docker image and deploys it locally using docker-compose

echo "🏗️  Building Invoice Generator Docker image locally..."

# Build the image with local tag
docker build -t invoice-generator:latest .

if [ $? -eq 0 ]; then
    echo "✅ Image built successfully!"
    
    echo "🚀 Deploying locally with docker-compose..."
    
    # Stop any existing deployment
    docker-compose -f docker-compose-local.yml down 2>/dev/null
    
    # Deploy the stack
    docker-compose -f docker-compose-local.yml up -d
    
    if [ $? -eq 0 ]; then
        echo "✅ Application deployed successfully!"
        echo ""
        echo "📋 Your Invoice Generator is now running:"
        echo "🌐 Access at: http://$(hostname -I | awk '{print $1}'):8501"
        echo "🌐 Or locally: http://localhost:8501"
        echo ""
        echo "📊 Useful commands:"
        echo "   📋 Check status:    docker-compose -f docker-compose-local.yml ps"
        echo "   📝 View logs:       docker-compose -f docker-compose-local.yml logs"
        echo "   🔄 Restart:         docker-compose -f docker-compose-local.yml restart"
        echo "   ⏹️  Stop:            docker-compose -f docker-compose-local.yml down"
        echo ""
        echo "🎉 Happy invoicing!"
    else
        echo "❌ Failed to deploy application. Check docker-compose-local.yml file exists."
    fi
else
    echo "❌ Failed to build image. Check the Dockerfile and try again."
fi