#!/usr/bin/env python3
"""
Dependency verification script to check if all packages are installed with correct versions.
Run this script to verify that the installation was successful.
"""

import sys
import pkg_resources
from typing import Dict, List, Tuple

# Expected versions (keep in sync with requirements.txt)
EXPECTED_VERSIONS = {
    'streamlit': '1.32.0',
    'httpx': '0.24.1', 
    'requests': '2.31.0',
    'openai': '1.12.0',
    'elasticsearch': '8.11.0',
    'python-dotenv': '1.0.1'
}

def check_package_version(package_name: str, expected_version: str) -> Tuple[bool, str]:
    """Check if a package is installed with the expected version."""
    try:
        installed_version = pkg_resources.get_distribution(package_name).version
        if installed_version == expected_version:
            return True, installed_version
        else:
            return False, installed_version
    except pkg_resources.DistributionNotFound:
        return False, "NOT_INSTALLED"

def verify_dependencies() -> bool:
    """Verify all dependencies are installed with correct versions."""
    print("🔍 Verifying package dependencies...")
    print("=" * 50)
    
    all_correct = True
    
    for package, expected_version in EXPECTED_VERSIONS.items():
        is_correct, actual_version = check_package_version(package, expected_version)
        
        if is_correct:
            print(f"✅ {package}: {actual_version}")
        else:
            print(f"❌ {package}: expected {expected_version}, got {actual_version}")
            all_correct = False
    
    print("=" * 50)
    
    if all_correct:
        print("🎉 All dependencies are correctly installed!")
        return True
    else:
        print("⚠️  Some dependencies have version conflicts!")
        print("\nTo fix, run:")
        print("pip uninstall openai httpx httpcore elasticsearch")
        print("pip install httpcore==0.18.0 httpx==0.24.1 openai==1.12.0 elasticsearch==8.11.0")
        return False

def test_imports() -> bool:
    """Test if all required packages can be imported."""
    print("\n🧪 Testing package imports...")
    print("=" * 50)
    
    import_tests = [
        ('streamlit', 'import streamlit as st'),
        ('httpx', 'import httpx'),
        ('requests', 'import requests'),
        ('openai', 'from openai import OpenAI'),
        ('elasticsearch', 'from elasticsearch import Elasticsearch'),
        ('dotenv', 'from dotenv import load_dotenv')
    ]
    
    all_imports_ok = True
    
    for package_name, import_statement in import_tests:
        try:
            exec(import_statement)
            print(f"✅ {package_name}: import successful")
        except Exception as e:
            print(f"❌ {package_name}: import failed - {e}")
            all_imports_ok = False
    
    print("=" * 50)
    return all_imports_ok

if __name__ == "__main__":
    print("🔧 Dependency Verification Tool")
    print(f"Python version: {sys.version}")
    print()
    
    versions_ok = verify_dependencies()
    imports_ok = test_imports()
    
    if versions_ok and imports_ok:
        print("\n🎯 All checks passed! Your environment is ready.")
        sys.exit(0)
    else:
        print("\n💥 Some checks failed! Please fix the issues above.")
        sys.exit(1) 