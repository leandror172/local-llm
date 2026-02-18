#!/usr/bin/env bash
# Build script for monorepo

set -euo pipefail

echo "Building backend..."
cd backend
mvn clean package
cd ..

echo "Building frontend..."
cd frontend
npm run build
cd ..

echo "Build complete!"
