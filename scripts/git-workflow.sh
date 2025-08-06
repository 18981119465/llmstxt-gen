#!/bin/bash

# Git workflow helper script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to show help
show_help() {
    echo "Git Workflow Helper"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  feature <name>       Create new feature branch"
    echo "  hotfix <name>        Create hotfix branch"
    echo "  release <version>    Create release branch"
    echo "  finish               Merge current branch to develop"
    echo "  deploy               Merge develop to main (production)"
    echo "  sync                 Sync with remote repository"
    echo "  status               Show current branch status"
    echo "  help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 feature user-auth"
    echo "  $0 hotfix fix-memory-leak"
    echo "  $0 release v1.0.0"
    echo "  $0 finish"
    echo "  $0 deploy"
}

# Function to create feature branch
create_feature() {
    if [ -z "$1" ]; then
        print_error "Feature name is required"
        exit 1
    fi
    
    local branch_name="feature/$1"
    print_status "Creating feature branch: $branch_name"
    
    # Ensure we're on develop branch
    git checkout develop
    git pull origin develop
    
    # Create and switch to feature branch
    git checkout -b "$branch_name"
    print_success "Feature branch '$branch_name' created successfully"
}

# Function to create hotfix branch
create_hotfix() {
    if [ -z "$1" ]; then
        print_error "Hotfix name is required"
        exit 1
    fi
    
    local branch_name="hotfix/$1"
    print_status "Creating hotfix branch: $branch_name"
    
    # Ensure we're on main branch
    git checkout main
    git pull origin main
    
    # Create and switch to hotfix branch
    git checkout -b "$branch_name"
    print_success "Hotfix branch '$branch_name' created successfully"
}

# Function to create release branch
create_release() {
    if [ -z "$1" ]; then
        print_error "Release version is required"
        exit 1
    fi
    
    local branch_name="release/$1"
    print_status "Creating release branch: $branch_name"
    
    # Ensure we're on develop branch
    git checkout develop
    git pull origin develop
    
    # Create and switch to release branch
    git checkout -b "$branch_name"
    print_success "Release branch '$branch_name' created successfully"
}

# Function to finish current branch
finish_branch() {
    local current_branch=$(git branch --show-current)
    print_status "Finishing branch: $current_branch"
    
    # Check if it's a feature branch
    if [[ $current_branch == feature/* ]]; then
        print_status "Merging feature branch to develop"
        
        # Switch to develop and pull latest
        git checkout develop
        git pull origin develop
        
        # Merge feature branch
        git merge --no-ff "$current_branch" -m "Merge branch '$current_branch' into develop"
        
        # Push to remote
        git push origin develop
        
        # Optionally delete feature branch
        read -p "Delete feature branch '$current_branch'? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git branch -d "$current_branch"
            git push origin --delete "$current_branch"
            print_success "Feature branch '$current_branch' deleted"
        fi
        
        print_success "Feature branch merged to develop"
        
    elif [[ $current_branch == hotfix/* ]]; then
        print_status "Merging hotfix branch to main and develop"
        
        # Merge to main
        git checkout main
        git pull origin main
        git merge --no-ff "$current_branch" -m "Merge branch '$current_branch' into main"
        git push origin main
        
        # Merge to develop
        git checkout develop
        git pull origin develop
        git merge --no-ff "$current_branch" -m "Merge branch '$current_branch' into develop"
        git push origin develop
        
        # Delete hotfix branch
        git branch -d "$current_branch"
        git push origin --delete "$current_branch"
        
        print_success "Hotfix branch merged to main and develop"
        
    elif [[ $current_branch == release/* ]]; then
        print_status "Merging release branch to main and develop"
        
        # Merge to main
        git checkout main
        git pull origin main
        git merge --no-ff "$current_branch" -m "Release $current_branch"
        git push origin main
        
        # Create tag
        local version=$(echo $current_branch | sed 's/release\///')
        git tag -a "v$version" -m "Release version $version"
        git push origin "v$version"
        
        # Merge to develop
        git checkout develop
        git pull origin develop
        git merge --no-ff "$current_branch" -m "Merge branch '$current_branch' into develop"
        git push origin develop
        
        # Delete release branch
        git branch -d "$current_branch"
        git push origin --delete "$current_branch"
        
        print_success "Release branch merged and tagged"
        
    else
        print_error "Cannot finish branch '$current_branch'. Not a feature, hotfix, or release branch."
        exit 1
    fi
}

# Function to deploy to production
deploy_to_production() {
    print_status "Deploying to production"
    
    # Ensure we're on main branch
    git checkout main
    git pull origin main
    
    # Check if working directory is clean
    if [ -n "$(git status --porcelain)" ]; then
        print_error "Working directory is not clean. Please commit or stash changes."
        exit 1
    fi
    
    print_success "Ready for deployment. Current branch: $(git branch --show-current)"
    print_status "Latest commit: $(git log -1 --pretty=format:'%h - %s (%cr)')"
}

# Function to sync with remote
sync_with_remote() {
    print_status "Syncing with remote repository"
    
    # Fetch all branches
    git fetch --all
    
    # Update main and develop branches
    git checkout main
    git pull origin main
    
    git checkout develop
    git pull origin develop
    
    print_success "Repository synced with remote"
}

# Function to show status
show_status() {
    local current_branch=$(git branch --show-current)
    print_status "Current branch: $current_branch"
    
    # Show recent commits
    echo ""
    echo "Recent commits:"
    git log --oneline -10
    
    # Show unpushed commits
    local unpushed=$(git cherry -v 2>/dev/null | wc -l)
    if [ "$unpushed" -gt 0 ]; then
        echo ""
        print_warning "Unpushed commits: $unpushed"
    fi
    
    # Show working directory status
    if [ -n "$(git status --porcelain)" ]; then
        echo ""
        print_warning "Working directory is not clean"
        git status --short
    fi
}

# Main script logic
case "${1:-}" in
    "feature")
        create_feature "$2"
        ;;
    "hotfix")
        create_hotfix "$2"
        ;;
    "release")
        create_release "$2"
        ;;
    "finish")
        finish_branch
        ;;
    "deploy")
        deploy_to_production
        ;;
    "sync")
        sync_with_remote
        ;;
    "status")
        show_status
        ;;
    "help"|"--help"|"-h"|"")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac