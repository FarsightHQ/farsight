#!/bin/bash

# Farsight Project Cleanup Script
# Removes temporary files, cache files, and test data

echo "🧹 Cleaning up Farsight project..."

# Remove Python cache files
echo "Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Remove macOS files
echo "Removing macOS system files..."
find . -name ".DS_Store" -delete 2>/dev/null || true

# Remove temporary files
echo "Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true
find . -name "*.cache" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true

# Remove test CSV files from root (but keep actual data files if in subdirs)
echo "Removing test CSV files from root..."
rm -f *.csv 2>/dev/null || true

# Remove uploads directory
echo "Removing uploads directory..."
rm -rf uploads/ 2>/dev/null || true

# Remove log files
echo "Removing log files..."
find . -name "*.log" -delete 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""
echo "📁 Project structure is now clean:"
ls -la
