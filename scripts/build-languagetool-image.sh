#!/usr/bin/env bash
# Build the enhanced LanguageTool image with n-gram data.
#
# Usage: bash scripts/build-languagetool-image.sh
#
# Prerequisites:
#   - podman or docker installed
#   - ~24GB free disk (transient build peak: 8.5GB zip + 15GB extracted)
#   - Network access to languagetool.org download servers

set -euo pipefail

IMAGE_REPO="quay.io/rhdeveldocs/languagetool"
IMAGE_TAG="6.7-ngram-v1"
CONTAINERFILE="deployment/Containerfile.languagetool"

if command -v podman &>/dev/null; then
    RUNTIME="podman"
elif command -v docker &>/dev/null; then
    RUNTIME="docker"
else
    echo "ERROR: Neither podman nor docker found in PATH." >&2
    exit 1
fi

echo "Building ${IMAGE_REPO}:${IMAGE_TAG} with ${RUNTIME}..."
echo "NOTE: This downloads ~8.5GB of n-gram data. Build takes 20-30 minutes."
echo ""

${RUNTIME} build \
    -f "${CONTAINERFILE}" \
    -t "${IMAGE_REPO}:${IMAGE_TAG}" \
    -t "${IMAGE_REPO}:latest" \
    .

echo ""
echo "Build complete."
echo "  Tagged: ${IMAGE_REPO}:${IMAGE_TAG}"
echo "  Tagged: ${IMAGE_REPO}:latest"
echo ""
echo "To push:  ${RUNTIME} push ${IMAGE_REPO}:${IMAGE_TAG}"
echo "To run:   ${RUNTIME} run -d -p 8010:8010 ${IMAGE_REPO}:${IMAGE_TAG}"
echo ""
echo "REMINDER: Final image is ~14-15GB. Ensure cluster nodes have"
echo "sufficient disk for image pull (~15GB + pull overhead)."
