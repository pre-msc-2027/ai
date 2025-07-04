#!/bin/bash
# Code quality and formatting script

set -e

echo "🔍 Running code quality checks..."

echo "📝 Checking imports with isort..."
poetry run isort --check-only --diff .

echo "🎨 Checking formatting with black..."
poetry run black --check --diff .

echo "🔍 Running flake8..."
poetry run flake8 .

echo "🔍 Running mypy..."
poetry run mypy .

echo "✅ All checks passed!"
