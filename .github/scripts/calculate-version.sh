#!/bin/bash
set -euo pipefail

# Version calculation script for ChatrixCD
# Usage: ./calculate-version.sh <version_type>
# Where version_type is one of: major, minor, patch (defaults to patch if not provided or invalid)

VERSION_TYPE="${1:-patch}"

# Get current date components
YEAR=$(date +%Y)
MONTH=$(date +%m)
DAY=$(date +%d)

# Get the latest tag across all dates
LATEST_TAG=$(git tag -l | grep -E '^[0-9]{4}\.[0-9]{2}\.[0-9]{2}\.[0-9]+\.[0-9]+\.[0-9]+$' | grep -v -- '-dev$' | sort -V | tail -n 1)

if [ -z "$LATEST_TAG" ]; then
  # No tags at all - start fresh
  MAJOR=0
  MINOR=0
  PATCH=1
else
  # Extract version components from the latest tag
  TAG_MAJOR=$(echo "$LATEST_TAG" | cut -d. -f4)
  TAG_MINOR=$(echo "$LATEST_TAG" | cut -d. -f5)
  TAG_PATCH=$(echo "$LATEST_TAG" | cut -d. -f6)
  
  # Increment version based on type
  case "$VERSION_TYPE" in
    major)
      MAJOR=$((TAG_MAJOR + 1))
      MINOR=0
      PATCH=0
      ;;
    minor)
      MAJOR="$TAG_MAJOR"
      MINOR=$((TAG_MINOR + 1))
      PATCH=0
      ;;
    patch|*)
      # Default to patch increment for any unknown/empty value
      MAJOR="$TAG_MAJOR"
      MINOR="$TAG_MINOR"
      PATCH=$((TAG_PATCH + 1))
      ;;
  esac
fi

# Build final version string
VERSION="${YEAR}.${MONTH}.${DAY}.${MAJOR}.${MINOR}.${PATCH}"

# Output version (can be captured by calling script)
echo "$VERSION"
