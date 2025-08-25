#!/usr/bin/env python3
"""
Setup Script for Advanced Crypto CTF Framework
Initializes directories and downloads initial training data
"""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """Create necessary directory structure"""
    directories = [
        "challenges/uploaded",
        "challenges/extracted", 
        "challenges/solved",
        "data/expert_writeups",
        "data/expert_knowledge",
        "data/professional_writeups",
        "data/sekai_writeups",
        "data/models",
        "data/training_data",
        "data/knowledge_base",
        "models/expert",
        "logs",
        "temp"
    ]
    
    print("Creating directory structure...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\\nChecking dependencies...")
    
    required_packages = [
        "numpy",
        "scikit-learn", 
        "pandas",
        "requests",
        "beautifulsoup4",
        "pycryptodome",
        "gmpy2"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    return True

def initialize_expert_ml():
    """Initialize Expert ML system"""
    print("\\nInitializing Expert ML system...")
    
    try:
        from framework.ml.expert_ml_framework import ExpertMLFramework
        framework = ExpertMLFramework()
        print("  ✓ Expert ML Framework initialized")
        return True
    except Exception as e:
        print(f"  ✗ Error initializing Expert ML: {e}")
        return False

def main():
    """Main setup function"""
    print("=== Advanced Crypto CTF Framework Setup ===")
    print("Initializing framework components...")
    
    # Create directories
    create_directory_structure()
    
    # Check dependencies
    deps_ok = check_dependencies()
    if not deps_ok:
        print("\\n❌ Setup incomplete - missing dependencies")
        sys.exit(1)
    
    # Initialize Expert ML
    ml_ok = initialize_expert_ml()
    if not ml_ok:
        print("\\n⚠️  Expert ML initialization failed")
    
    print("\\n🎉 Setup completed successfully!")
    print("\\nNext steps:")
    print("1. Add writeup URLs to challenges/uploaded/writeupsSolutions.txt")
    print("2. Run: python main.py")
    print("3. Select option 10 to auto-update Expert ML")
    print("4. Start solving challenges!")

if __name__ == "__main__":
    main()