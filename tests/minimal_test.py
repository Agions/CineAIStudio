#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal test for AI services integration
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_basic_imports():
    """Test basic imports"""
    print("Testing basic imports...")

    try:
        # Test secure key manager
        from app.core.secure_key_manager import get_secure_key_manager
        print("✓ Secure key manager imported successfully")

        # Test that we can create an instance
        key_manager = get_secure_key_manager()
        print("✓ Key manager instance created")

        # Test basic functionality
        services = key_manager.get_available_services()
        print(f"✓ Available services: {len(services)}")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_ai_services_structure():
    """Test AI services structure"""
    print("Testing AI services structure...")

    try:
        # Check if files exist
        ai_files = [
            'app/services/ai_service_manager.py',
            'app/services/chinese_ai_services.py',
            'app/services/base_ai_service.py',
            'app/ui/components/ai_content_generator.py',
            'app/ui/components/ai_demo_widget.py'
        ]

        for file_path in ai_files:
            if os.path.exists(file_path):
                print(f"✓ {file_path} exists")
            else:
                print(f"✗ {file_path} missing")
                return False

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_file_syntax():
    """Test file syntax"""
    print("Testing file syntax...")

    try:
        import ast

        # Test base AI service
        with open('app/services/base_ai_service.py', 'r') as f:
            ast.parse(f.read())
        print("✓ base_ai_service.py syntax OK")

        # Test secure key manager
        with open('app/core/secure_key_manager.py', 'r') as f:
            ast.parse(f.read())
        print("✓ secure_key_manager.py syntax OK")

        # Test UI components
        with open('app/ui/components/ai_content_generator.py', 'r') as f:
            ast.parse(f.read())
        print("✓ ai_content_generator.py syntax OK")

        return True

    except SyntaxError as e:
        print(f"✗ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run tests"""
    print("AI Services Integration Test")
    print("=" * 40)

    tests = [
        test_file_syntax,
        test_ai_services_structure,
        test_basic_imports,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ {test.__name__} crashed: {e}")
            print()

    print("=" * 40)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)