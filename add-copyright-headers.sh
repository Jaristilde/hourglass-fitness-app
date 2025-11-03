#!/bin/bash

# Script to add copyright headers to Python files
# For Hourglass Fitness App

read -r -d '' HEADER <<'EOF'
# Copyright © 2024-2025 [YOUR NAME]. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of Hourglass Fitness Transformation application.
# Unauthorized copying, distribution, or modification of this file,
# via any medium, is strictly prohibited.
#
# Contact: [your-email@example.com]

EOF

# Add headers to Python files in the root directory only (not venv)
for file in app.py smoke.py storage.py; do
  if [ -f "$file" ]; then
    # Check if file already has copyright header
    if ! head -n 3 "$file" | grep -q "Copyright © 2024-2025"; then
      echo "Adding header to: $file"
      echo "$HEADER" > "$file.tmp"
      cat "$file" >> "$file.tmp"
      mv "$file.tmp" "$file"
    else
      echo "Skipping $file (already has header)"
    fi
  fi
done

echo "✅ Copyright headers added successfully!"
