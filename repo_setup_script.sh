#!/bin/bash

# VirtuAI Office - Git Setup Troubleshooting Script

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 VirtuAI Office - Git Setup Troubleshooting${NC}"
echo "=============================================="
echo ""

# Check current directory
echo -e "${YELLOW}📍 Current Directory Check:${NC}"
echo "Current directory: $(pwd)"
echo "Contents:"
ls -la
echo ""

# Check if Git is installed
echo -e "${YELLOW}🔍 Git Installation Check:${NC}"
if command -v git &> /dev/null; then
    echo -e "${GREEN}✅ Git is installed: $(git --version)${NC}"
else
    echo -e "${RED}❌ Git is not installed${NC}"
    echo "Install Git first:"
    echo "  macOS: brew install git"
    echo "  Ubuntu: sudo apt install git"
    echo "  Windows: Download from git-scm.com"
    exit 1
fi
echo ""

# Check if we're in a git repository
echo -e "${YELLOW}📁 Git Repository Check:${NC}"
if [ -d ".git" ]; then
    echo -e "${GREEN}✅ This is a Git repository${NC}"
    echo "Git status:"
    git status --short
else
    echo -e "${RED}❌ This is NOT a Git repository${NC}"
    echo ""
    echo "Options to fix:"
    echo "1. Initialize Git repository here: git init"
    echo "2. Clone existing repository: git clone <URL>"
    echo "3. Navigate to correct directory: cd <repo-directory>"
fi
echo ""

# Check Git configuration
echo -e "${YELLOW}⚙️ Git Configuration Check:${NC}"
if git config user.name >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Git user name: $(git config user.name)${NC}"
else
    echo -e "${RED}❌ Git user name not set${NC}"
    echo "Set with: git config --global user.name 'Your Name'"
fi

if git config user.email >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Git user email: $(git config user.email)${NC}"
else
    echo -e "${RED}❌ Git user email not set${NC}"
    echo "Set with: git config --global user.email 'your.email@example.com'"
fi
echo ""

# Check GitHub CLI
echo -e "${YELLOW}🐙 GitHub CLI Check:${NC}"
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✅ GitHub CLI is installed: $(gh --version | head -1)${NC}"
    if gh auth status >/dev/null 2>&1; then
        echo -e "${GREEN}✅ GitHub CLI is authenticated${NC}"
    else
        echo -e "${YELLOW}⚠️ GitHub CLI is not authenticated${NC}"
        echo "Run: gh auth login"
    fi
else
    echo -e "${YELLOW}⚠️ GitHub CLI is not installed (optional)${NC}"
    echo "Install with: brew install gh (macOS) or see cli.github.com"
fi
echo ""

# Provide quick fix commands
echo -e "${BLUE}🚀 Quick Fix Commands:${NC}"
echo ""

echo "1. If 'not a git directory' error:"
echo "   git init"
echo "   git config user.name 'Your Name'"
echo "   git config user.email 'your.email@example.com'"
echo ""

echo "2. If you have source files to add:"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo ""

echo "3. If you need to connect to GitHub:"
echo "   git remote add origin https://github.com/USERNAME/REPO.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""

echo "4. If starting fresh:"
echo "   rm -rf .git"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo ""

# Interactive fix option
echo -e "${YELLOW}🛠️ Would you like to initialize Git here? (y/n):${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo ""
    echo "Setting up Git repository..."
    
    # Remove existing .git if present
    if [ -d ".git" ]; then
        echo "Removing existing .git directory..."
        rm -rf .git
    fi
    
    # Initialize
    echo "Initializing Git repository..."
    git init
    
    # Get user info if not set
    if ! git config user.name >/dev/null 2>&1; then
        echo -n "Enter your name: "
        read -r user_name
        git config user.name "$user_name"
    fi
    
    if ! git config user.email >/dev/null 2>&1; then
        echo -n "Enter your email: "
        read -r user_email
        git config user.email "$user_email"
    fi
    
    # Add files if any exist
    if [ "$(ls -A)" ]; then
        echo "Adding files..."
        git add .
        git commit -m "Initial commit"
        echo -e "${GREEN}✅ Git repository initialized successfully!${NC}"
    else
        echo -e "${YELLOW}⚠️ No files to commit. Add some files first.${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🎯 Repository setup troubleshooting complete!${NC}"
