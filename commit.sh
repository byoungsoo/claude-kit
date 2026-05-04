#!/bin/bash
git add . 

# Check if a commit message was provided as an argument
if [ $# -eq 0 ]; then
  # No argument provided, use default message
  git commit -m "Updated by commit.sh"
else
  # Use the provided message
  git commit -m "$1"
fi

git -c core.hooksPath=/dev/null push origin main