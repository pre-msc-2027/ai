#!/bin/bash
# Setup script for development environment

echo "🚀 Setting up development environment..."

# Install poetry dependencies
echo "📦 Installing dependencies with Poetry..."
poetry install --with dev

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
poetry run pre-commit install

echo "✅ Setup complete! You're ready to develop."
echo "   Pre-commit hooks will run automatically on git commit."
echo "   To run checks manually: poetry run pre-commit run --all-files"
