#!/bin/bash

echo "🚀 Setting up Intelligent Test Case Generator for Qdrant Hackathon 2025"

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
echo "⚠️  Please update .env with your API keys"

# Start Docker services
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Run the first test to start TDD
echo "🧪 Running first test to begin TDD process..."
pytest tests/test_1_vector_store_initialization.py -v

echo """
📝 TDD Instructions:
1. The test above should FAIL - this is expected!
2. Now implement src/vector_store.py to make it pass
3. Run the same test command again to verify
4. Move to test_2_pattern_extraction.py

Use Claude Code to implement each feature by:
- Showing it the failing test
- Asking it to implement the minimal code to pass
- Following the patterns in CLAUDE_CODE_INSTRUCTIONS.md

Happy coding! 🎯
"""