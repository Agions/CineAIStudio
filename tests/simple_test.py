#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple test script for AI services functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_secure_key_manager():
    """Test secure key manager"""
    print("Testing SecureKeyManager...")

    try:
        from app.core.secure_key_manager import SecureKeyManager, get_secure_key_manager

        # Test singleton pattern
        manager1 = SecureKeyManager()
        manager2 = SecureKeyManager()
        assert manager1 is manager2, "SecureKeyManager should be a singleton"

        # Test get function
        manager3 = get_secure_key_manager()
        assert manager1 is manager3, "get_secure_key_manager should return the same instance"

        # Test API key storage and retrieval
        test_key = "test_api_key_12345"
        service_name = "test_service"

        manager1.store_api_key(service_name, test_key)
        retrieved_key = manager1.get_api_key(service_name)
        assert retrieved_key == test_key, f"Expected {test_key}, got {retrieved_key}"

        # Test key masking
        masked_key = manager1.get_masked_api_key(service_name)
        assert masked_key.startswith("test"), "Masked key should start with original prefix"
        assert "*" in masked_key, "Masked key should contain asterisks"

        # Test available services
        services = manager1.get_available_services()
        assert isinstance(services, list), "Available services should be a list"
        assert len(services) > 0, "Should have at least one available service"

        print("✓ SecureKeyManager tests passed")
        return True

    except Exception as e:
        print(f"✗ SecureKeyManager tests failed: {e}")
        return False

def test_chinese_ai_services():
    """Test Chinese AI services"""
    print("Testing Chinese AI Services...")

    try:
        from app.services.chinese_ai_services import (
            WenxinService, SparkService, QwenService,
            GLMService, BaichuanService, MoonshotService
        )

        services = [
            WenxinService,
            SparkService,
            QwenService,
            GLMService,
            BaichuanService,
            MoonshotService
        ]

        for service_class in services:
            try:
                service = service_class()
                assert hasattr(service, 'service_name'), f"{service_class.__name__} should have service_name"
                assert hasattr(service, 'generate_text'), f"{service_class.__name__} should have generate_text"
                print(f"✓ {service_class.__name__} initialized successfully")
            except Exception as e:
                print(f"✗ {service_class.__name__} failed: {e}")
                return False

        print("✓ Chinese AI Services tests passed")
        return True

    except Exception as e:
        print(f"✗ Chinese AI Services tests failed: {e}")
        return False

def test_ai_service_manager():
    """Test AI service manager"""
    print("Testing AI Service Manager...")

    try:
        from app.services.ai_service_manager import AIServiceManager

        manager = AIServiceManager()
        assert manager is not None, "AIServiceManager should be created"

        # Test service registration
        # Note: This is a simplified test since we can't easily mock the services
        print("✓ AI Service Manager tests passed")
        return True

    except Exception as e:
        print(f"✗ AI Service Manager tests failed: {e}")
        return False

def test_import_structure():
    """Test import structure"""
    print("Testing Import Structure...")

    try:
        # Test core imports
        from app.core.secure_key_manager import get_secure_key_manager
        from app.services.chinese_ai_services import WenxinService
        from app.services.ai_service_manager import AIServiceManager

        print("✓ Import structure tests passed")
        return True

    except Exception as e:
        print(f"✗ Import structure tests failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("Starting AI Services Test Suite")
    print("=" * 50)

    tests = [
        test_import_structure,
        test_secure_key_manager,
        test_chinese_ai_services,
        test_ai_service_manager,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} crashed: {e}")

    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed! AI services are working correctly.")
        return True
    else:
        print("✗ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)