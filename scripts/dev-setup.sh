#!/bin/bash

# Development environment setup script
set -e

echo "🚀 Setting up development environment for llms.txt-gen..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/llms_txt_gen
REDIS_URL=redis://localhost:6379

# Application Configuration
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
ENVIRONMENT=development

# AI Service Configuration
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# External Services
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO
EOF
    echo "✅ .env file created. Please update with your actual API keys."
fi

# Start development environment
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run database migrations (if any)
echo "🗄️ Running database migrations..."
docker-compose exec backend python -m alembic upgrade head

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
docker-compose exec frontend npm install

echo "✅ Development environment is ready!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🗄️ Database: localhost:5432"
echo "🔄 Redis: localhost:6379"
echo ""
echo "Use 'docker-compose logs -f' to view logs"
echo "Use 'docker-compose down' to stop services"