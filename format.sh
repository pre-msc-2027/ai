#!/bin/bash
# Auto-format code script

set -e

echo "🎨 Auto-formatting code..."

echo "📝 Sorting imports with isort..."
poetry run isort .

echo "🎨 Formatting code with black..."
poetry run black .

echo "✅ Code formatted successfully!"
echo "💡 Run './lint.sh' to verify formatting"
