#!/bin/bash
# Content Editorial Assistant Documentation Deployment Script
# Supports both local and CI/CD deployments

set -e  # Exit on any error

# Configuration
DOCS_DIR="$(dirname "$(readlink -f "$0")")"
BUILD_DIR="$DOCS_DIR/dist"
NODE_VERSION="18"
ANTORA_PLAYBOOK="antora-playbook.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Node.js version
    if command -v node >/dev/null 2>&1; then
        NODE_CURRENT=$(node --version | sed 's/v//')
        NODE_MAJOR=$(echo $NODE_CURRENT | cut -d. -f1)
        if [ "$NODE_MAJOR" -ge "$NODE_VERSION" ]; then
            log_success "Node.js $NODE_CURRENT found (required: $NODE_VERSION+)"
        else
            log_error "Node.js $NODE_VERSION+ required, found $NODE_CURRENT"
            exit 1
        fi
    else
        log_error "Node.js not found. Please install Node.js $NODE_VERSION+"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm >/dev/null 2>&1; then
        log_error "npm not found"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Install dependencies
install_dependencies() {
    log_info "Installing Node.js dependencies..."
    cd "$DOCS_DIR"
    
    if [ -f package-lock.json ]; then
        npm ci
    else
        npm install
    fi
    
    log_success "Dependencies installed"
}

# Clean previous build
clean_build() {
    log_info "Cleaning previous build..."
    if [ -d "$BUILD_DIR" ]; then
        rm -rf "$BUILD_DIR"
    fi
    log_success "Build directory cleaned"
}

# Build documentation
build_docs() {
    log_info "Building Content Editorial Assistant documentation..."
    cd "$DOCS_DIR"
    
    # Build with Antora
    npx antora --fetch "$ANTORA_PLAYBOOK"
    
    if [ -d "$BUILD_DIR" ]; then
        log_success "Documentation built successfully"
        log_info "Build output: $BUILD_DIR"
    else
        log_error "Build failed - output directory not found"
        exit 1
    fi
}

# Validate build
validate_build() {
    log_info "Validating build..."
    
    # Check if index.html exists
    if [ -f "$BUILD_DIR/index.html" ]; then
        log_success "Main index file found"
    else
        log_error "Main index file missing"
        exit 1
    fi
    
    # Check for common pages
    if [ -f "$BUILD_DIR/getting-started.html" ]; then
        log_success "Getting started page found"
    else
        log_warning "Getting started page not found"
    fi
    
    # Count total HTML files
    HTML_COUNT=$(find "$BUILD_DIR" -name "*.html" | wc -l)
    log_info "Generated $HTML_COUNT HTML pages"
    
    log_success "Build validation passed"
}

# Deploy to GitLab Pages (local simulation)
deploy_pages() {
    log_info "Preparing GitLab Pages deployment..."
    
    PUBLIC_DIR="$DOCS_DIR/../public"
    
    # Clean and create public directory
    if [ -d "$PUBLIC_DIR" ]; then
        rm -rf "$PUBLIC_DIR"
    fi
    mkdir -p "$PUBLIC_DIR"
    
    # Copy build to public directory
    cp -r "$BUILD_DIR"/* "$PUBLIC_DIR/"
    
    log_success "Files copied to public/ directory for GitLab Pages"
    log_info "Public directory: $PUBLIC_DIR"
}

# Deploy to custom staging server (example)
deploy_staging() {
    local STAGING_URL="$1"
    log_info "Deploying to staging: $STAGING_URL"
    
    # This is a placeholder - replace with your actual staging deployment
    # Examples:
    # - rsync to staging server
    # - Upload to S3/CloudFlare
    # - Deploy to Netlify/Vercel
    
    log_warning "Staging deployment not configured - implement in deploy.sh"
    log_info "Build is ready at: $BUILD_DIR"
}

# Serve locally for testing
serve_local() {
    local PORT="${1:-8080}"
    log_info "Starting local server on port $PORT..."
    cd "$BUILD_DIR"
    
    if command -v python3 >/dev/null 2>&1; then
        log_info "Documentation available at: http://localhost:$PORT"
        python3 -m http.server "$PORT"
    elif command -v python >/dev/null 2>&1; then
        log_info "Documentation available at: http://localhost:$PORT"
        python -m http.server "$PORT"
    elif command -v npx >/dev/null 2>&1; then
        log_info "Documentation available at: http://localhost:$PORT"
        npx http-server . -p "$PORT"
    else
        log_error "No suitable HTTP server found (tried python3, python, npx)"
        exit 1
    fi
}

# Main deployment logic
main() {
    local COMMAND="${1:-build}"
    local PARAM="$2"
    
    echo "============================================"
    echo "Content Editorial Assistant Docs Deployment"
    echo "============================================"
    
    case "$COMMAND" in
        "build")
            check_prerequisites
            install_dependencies
            clean_build
            build_docs
            validate_build
            log_success "Documentation build completed successfully!"
            ;;
        "pages")
            check_prerequisites
            install_dependencies
            clean_build
            build_docs
            validate_build
            deploy_pages
            log_success "GitLab Pages deployment prepared!"
            ;;
        "staging")
            check_prerequisites
            install_dependencies
            clean_build
            build_docs
            validate_build
            deploy_staging "$PARAM"
            ;;
        "serve")
            if [ ! -d "$BUILD_DIR" ]; then
                log_warning "Build directory not found, building first..."
                check_prerequisites
                install_dependencies
                clean_build
                build_docs
                validate_build
            fi
            serve_local "$PARAM"
            ;;
        "clean")
            clean_build
            log_success "Build cleaned"
            ;;
        *)
            echo "Usage: $0 {build|pages|staging|serve|clean} [parameter]"
            echo ""
            echo "Commands:"
            echo "  build                 - Build documentation only"
            echo "  pages                 - Build and prepare for GitLab Pages"
            echo "  staging [url]         - Build and deploy to staging"
            echo "  serve [port]          - Serve locally (default port: 8080)"
            echo "  clean                 - Clean build directory"
            echo ""
            echo "Examples:"
            echo "  $0 build              # Build documentation"
            echo "  $0 pages              # Prepare for GitLab Pages"
            echo "  $0 serve 3000         # Serve locally on port 3000"
            echo "  $0 staging https://staging.example.com"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
