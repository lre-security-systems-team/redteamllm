#!/bin/bash
# This script recursively deletes all __pycache__ directories

echo "Deleting all __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} +
echo "Done."
