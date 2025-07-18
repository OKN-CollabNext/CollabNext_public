#!/bin/bash

# Set your token here
GHCR_PAT="YOUR_PAT_HERE"

# List of package names (not tags, just the package)
PACKAGES=(
  deployment-package
  database
  backend
  frontend
)

ORG="okn-collabnext"

for pkg in "${PACKAGES[@]}"; do
  echo "Making $pkg public..."
  curl -X PATCH \
    -H "Authorization: Bearer $GHCR_PAT" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/orgs/$ORG/packages/container/$pkg/visibility" \
    -d '{"visibility":"public"}'
  echo # newline for readability
done