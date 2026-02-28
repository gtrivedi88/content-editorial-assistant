#!/bin/bash

# This script builds, pushes, and deploys the application to OpenShift.
# It will exit immediately if any command fails.
set -e

# --- Auto-Increment Version Function ---
auto_increment_version() {
    local current_version=$1
    # Extract version numbers (v0.6.0 -> 0 6 0)
    local major=$(echo "$current_version" | sed 's/v//;s/\./ /g' | awk '{print $1}')
    local minor=$(echo "$current_version" | sed 's/v//;s/\./ /g' | awk '{print $2}')
    local patch=$(echo "$current_version" | sed 's/v//;s/\./ /g' | awk '{print $3}')
    
    # Increment minor version, reset patch
    minor=$((minor + 1))
    patch=0
    
    echo "v${major}.${minor}.${patch}"
}

# Log in to oc
oc login --token=sha256~UIl5r70mSJKWnx9tW-MCPcNy4QWC10iM5C0gGImzSL0 --server=https://api.mpp-e1-preprod.syvu.p1.openshiftapps.com:6443

# Set project
oc project cea--runtime-int

# Login to registry (you already did this once, but let's be sure)
oc registry login

# Set variables (make sure double hyphens are kept in namespace!)
REG=$(oc registry info)
NS="cea--runtime-int"
IMG="cea-app"

# --- Determine Version Tag ---
if [ -z "$1" ]; then
    echo "🔍 No version tag provided. Checking current version..."
    
    # Get current version from OpenShift
    CURRENT_VERSION=$(oc get deployment cea-app -n cea--runtime-int -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null | grep -oP 'v\d+\.\d+\.\d+' || echo "v0.6.0")
    
    echo "📌 Current version: $CURRENT_VERSION"
    NEW_VERSION=$(auto_increment_version "$CURRENT_VERSION")
    echo "🆕 Suggested new version: $NEW_VERSION"
    echo ""
    read -p "❓ Use $NEW_VERSION? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        TAG=$NEW_VERSION
    else
        echo "❌ Deployment cancelled."
        exit 1
    fi
else
    TAG=$1 # Use the provided version tag
fi

echo "🚀 Starting deployment for version: $TAG"
echo "--------------------------------------------------"

# --- Step 1: Build, Tag, and Push the Image ---
echo -e "\n🏗️  Building container image: ${IMG}:${TAG}"
podman build -t "${IMG}:${TAG}" .

echo -e "\n🏷️  Tagging image for registry..."
podman tag "${IMG}:${TAG}" "${REG}/${NS}/${IMG}:${TAG}"

echo -e "\n📤 Pushing image to registry..."
podman push "${REG}/${NS}/${IMG}:${TAG}"
echo "✅ Image pushed successfully."

# --- Step 2: Apply OpenShift Route Configuration (if changed) ---
echo -e "\n🔧 Checking OpenShift Route configuration..."
if [ -f "openshift-route.yaml" ]; then
    echo "📝 Applying Route configuration with timeout annotations..."
    oc apply -f openshift-route.yaml
    if [ $? -eq 0 ]; then
        echo "✅ Route configuration applied successfully"
    else
        echo "⚠️ Warning: Route configuration update failed, but continuing deployment..."
    fi
else
    echo "⚠️ No openshift-route.yaml found, skipping route configuration"
fi

# --- Step 2.5: Apply Persistent Storage Configuration ---
echo -e "\n💾 Applying persistent storage configuration..."
if [ -f "openshift-deployment-patch.yaml" ]; then
    echo "📝 Ensuring database and feedback persistence across pod restarts..."
    oc patch deployment cea-app -n "$NS" --patch-file openshift-deployment-patch.yaml
    if [ $? -eq 0 ]; then
        echo "✅ Persistent storage configuration applied"
        echo "   - Database: /app/instance/ → PVC (persistent)"
        echo "   - Feedback: /opt/app-root/src/feedback_data/ → PVC (persistent)"
    else
        echo "⚠️ Warning: Persistent storage patch failed, but continuing deployment..."
        echo "   ⚠️ Data will be LOST on pod restarts!"
    fi
else
    echo "⚠️ No openshift-deployment-patch.yaml found"
    echo "   ⚠️ Database and feedback will NOT persist across pod restarts!"
fi

# --- Step 3: Update and Monitor the Deployment ---
echo -e "\n🔄 Updating deployment to use new image..."
echo "ℹ️  Note: Deployment uses 'Recreate' strategy (old pod deleted before new one starts)"
oc set image deployment/cea-app "cea-app=${REG}/${NS}/${IMG}:${TAG}" -n "$NS"

echo -e "\n⏳ Monitoring rollout status..."
oc rollout status deployment/cea-app -n "$NS"

# --- Step 4: Final Verification ---
echo -e "\n✅ Deployment successful!"
echo "🔍 Final running pod status:"
oc get pods -n "$NS"

# Verify persistent storage is mounted
echo -e "\n💾 Verifying persistent storage..."
POD_NAME=$(oc get pods -n "$NS" -l deployment=cea-app -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$POD_NAME" ]; then
    echo "   Pod: $POD_NAME"
    echo "   Checking PVC mount..."
    if oc exec -n "$NS" "$POD_NAME" -- df -h 2>/dev/null | grep -q "/app/instance"; then
        echo "   ✅ PVC mounted at /app/instance (database persistent)"
        # Check if database file exists
        if oc exec -n "$NS" "$POD_NAME" -- ls /app/instance/content_editorial_assistant.db 2>/dev/null >/dev/null; then
            DB_SIZE=$(oc exec -n "$NS" "$POD_NAME" -- ls -lh /app/instance/content_editorial_assistant.db 2>/dev/null | awk '{print $5}')
            echo "   ✅ Database file exists (${DB_SIZE})"
        fi
    else
        echo "   ⚠️ Warning: PVC mount not detected at /app/instance"
    fi
else
    echo "   ⚠️ Could not verify storage (pod not ready yet)"
fi

# oc describe pod cea-app-67dc9d9fbc-7td69 -n "$NS"

echo -e "\n🎉 All done! Version ${TAG} is now live."
echo ""
echo "📊 Quick commands:"
echo "   Check feedback: ./check_feedback.sh"
echo "   View logs: oc logs -n $NS deployment/cea-app --tail=50"
echo "   Pod status: oc get pods -n $NS"