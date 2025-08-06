#!/bin/bash

# Git workflow setup script
set -e

echo "🔧 Setting up Git workflow..."

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Git repository not initialized. Please run 'git init' first."
    exit 1
fi

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install

# Create commit message template
echo "📝 Creating commit message template..."
cat > .gitmessage << 'EOF'
# Conventional Commits
# 
# Format: <type>[optional scope]: <description>
# 
# Types:
#   feat:     A new feature
#   fix:      A bug fix
#   docs:     Documentation only changes
#   style:    Changes that do not affect the meaning of the code
#   refactor: A code change that neither fixes a bug nor adds a feature
#   perf:     A code change that improves performance
#   test:     Adding missing tests or correcting existing tests
#   build:    Changes that affect the build system or external dependencies
#   ci:       Changes to our CI configuration files and scripts
#   chore:    Other changes that don't modify src or test files
#   revert:   Reverts a previous commit
#
# Examples:
#   feat: add user authentication
#   fix: resolve memory leak in data processing
#   docs: update API documentation
#   style: format code with black
#   test: add unit tests for user service
#   refactor: simplify database connection logic
#   perf: improve query performance
#   build: upgrade to next.js 14
#   ci: add github actions workflow
#   chore: update dependencies
#
# Scope (optional): can be anything specifying place of the commit change.
#   feat(auth): add user authentication
#   fix(api): resolve memory leak in data processing
#   docs(readme): update installation instructions
#
# Body (optional): detailed explanation of the change
#
# Footer (optional): metadata like breaking changes, issue references
#   BREAKING CHANGE: change existing API
#   Closes #123
EOF

# Configure git to use the commit message template
git config commit.template .gitmessage

# Set up branch protection rules (requires GitHub CLI)
if command -v gh &> /dev/null; then
    echo "🛡️ Setting up branch protection rules..."
    
    # Protect main branch
    gh api repos/:owner/:repo/branches/main/protection \
      --field required_status_checks='{ "strict": true, "contexts": ["ci", "code-quality"] }' \
      --field enforce_admins=true \
      --field required_pull_request_reviews='{ "required_approving_review_count": 1 }' \
      --field restrictions=null || echo "⚠️  Could not set branch protection (may need admin access)"
fi

# Create .github directory structure
mkdir -p .github

echo "✅ Git workflow setup complete!"
echo ""
echo "📋 Git workflow summary:"
echo "  - Branch strategy: Git Flow (main, develop, feature/*)"
echo "  - Commit messages: Conventional Commits"
echo "  - Pre-commit hooks: Code quality checks"
echo "  - Branch protection: Enabled (if GitHub CLI available)"
echo ""
echo "🚀 Ready to start development!"