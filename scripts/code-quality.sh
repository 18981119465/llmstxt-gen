#!/bin/bash

# Code quality check script
set -e

echo "🔍 Running code quality checks..."

# Backend checks
echo "📦 Checking Python code quality..."
cd backend

# Check Python formatting with black
echo "  🎨 Checking Black formatting..."
black --check --diff .

# Check imports with isort
echo "  📋 Checking import sorting..."
isort --check-only --diff .

# Run pylint
echo "  🔍 Running Pylint..."
pylint src/

# Run mypy
echo "  🦆 Running MyPy..."
mypy src/

# Run tests with coverage
echo "  🧪 Running tests..."
pytest --cov=src --cov-report=term-missing --cov-report=html

cd ..

# Frontend checks
echo "🎨 Checking frontend code quality..."
cd frontend

# Check TypeScript
echo "  📝 Running TypeScript check..."
npm run type-check

# Run ESLint
echo "  🔍 Running ESLint..."
npm run lint

# Run tests
echo "  🧪 Running tests..."
npm run test:coverage

cd ..

echo "✅ All code quality checks passed!"
echo "📊 Coverage reports available in:"
echo "  - Backend: backend/htmlcov/"
echo "  - Frontend: frontend/coverage/"