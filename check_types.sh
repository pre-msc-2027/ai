#!/bin/bash
# Type checking script for the project

echo "🔍 Running type checking with mypy..."
echo "====================================="

mypy . --config-file mypy.ini

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Type checking passed successfully!"
else
    echo ""
    echo "❌ Type checking failed. Please fix the errors above."
    exit 1
fi
