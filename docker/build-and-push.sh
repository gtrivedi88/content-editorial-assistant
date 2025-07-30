#!/bin/bash

# Build and Push Script for Style Guide AI to Quay.io
# Usage: ./build-and-push.sh
# Target: quay.io/rhdeveldocs/style-guide-ai

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
QUAY_USERNAME="rhdeveldocs"
IMAGE_NAME="style-guide-ai"
TAG="latest"
FULL_IMAGE="quay.io/${QUAY_USERNAME}/${IMAGE_NAME}:${TAG}"

echo -e "${BLUE}🚀 Building Style Guide AI Docker Image${NC}"
echo -e "${YELLOW}Registry: quay.io${NC}"
echo -e "${YELLOW}Username: ${QUAY_USERNAME}${NC}"
echo -e "${YELLOW}Image: ${IMAGE_NAME}${NC}"
echo -e "${YELLOW}Tag: ${TAG}${NC}"
echo -e "${YELLOW}Full Image: ${FULL_IMAGE}${NC}"
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if we're in the docker directory
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Error: Please run this script from the docker directory${NC}"
    echo -e "${YELLOW}   cd docker && ./build-and-push.sh${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 Docker Layer Caching Optimization Active:${NC}"
echo -e '   ✅ Python dependencies - cached (unless requirements.txt changed)'
echo -e '   ✅ NLP models (spaCy, NLTK) - cached'
echo -e '   ✅ Ruby gems (Asciidoctor) - cached'
echo -e '   ✅ System dependencies - cached'
echo
echo -e "${YELLOW}⚠️  Only rebuilds if you changed:${NC}"
echo -e "   - App code (fast rebuild)"
echo -e "   - requirements.txt (rebuilds dependencies)"
echo -e "   - System dependencies"
echo
echo -e "${BLUE}💡 Lightweight image without embedded AI models${NC}"
echo -e "   - Users can connect external Ollama instances"
echo -e "   - Supports API providers (OpenAI, etc.)"
echo -e "   - Much smaller image size"
echo

# Build the lightweight image
echo -e "${BLUE}🔨 Building lightweight image...${NC}"
echo -e "${YELLOW}   Note: First build = 5-8 min | Subsequent builds = 1-2 min${NC}"
docker build -f Dockerfile -t ${FULL_IMAGE} ..

# Show image size
echo -e "${BLUE}📊 Image size:${NC}"
docker images | grep ${QUAY_USERNAME}/${IMAGE_NAME}

# Ask for confirmation before pushing
echo
echo -e "${YELLOW}⚠️  Ready to push to Quay.io registry?${NC}"
echo -e "${YELLOW}This will upload the image to: ${FULL_IMAGE}${NC}"
read -p "Continue? (y/N): " REPLY
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}❌ Push cancelled.${NC}"
    exit 1
fi

# Login to Quay.io
echo -e "${BLUE}🔐 Logging in to Quay.io...${NC}"
echo -e "${YELLOW}Please enter your Quay.io credentials:${NC}"
docker login quay.io

# Push the lightweight image
echo -e "${BLUE}📤 Pushing lightweight image...${NC}"
echo -e "${YELLOW}   Note: Only changed layers get uploaded (layer caching)${NC}"
docker push ${FULL_IMAGE}

echo -e "${GREEN}✅ Successfully pushed image to Quay.io!${NC}"
echo
echo -e "${BLUE}🎉 Your image is now available at:${NC}"
echo -e "${YELLOW}Lightweight image: ${FULL_IMAGE}${NC}"
echo
echo -e "${BLUE}📖 Users can now run your app with:${NC}"
echo -e "${GREEN}docker run -p 5000:5000 ${FULL_IMAGE}${NC}"
echo -e "${YELLOW}   Or use different port if 5000 is occupied: docker run -p 8080:5000 ${FULL_IMAGE}${NC}"
echo
echo -e "${BLUE}🌐 App will be available at: http://localhost:5000${NC}"
echo -e "${YELLOW}   (or http://localhost:8080 if using alternate port)${NC}"
echo
echo -e "${BLUE}💡 To use AI features:${NC}"
echo -e "   - Set up external Ollama: docker run -d -p 11434:11434 ollama/ollama"
echo -e "   - Configure API providers in the app settings"
echo
echo -e "${BLUE}💡 Next time you build, it will be much faster thanks to layer caching!${NC}" 