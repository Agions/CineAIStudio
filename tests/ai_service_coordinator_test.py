#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Service Coordinator Test
Tests the coordination and fallback capabilities of AI services
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_service_manager_creation():
    """Test AI service manager creation"""
    print("Testing AI Service Manager creation...")

    try:
        # Mock the dependencies to avoid import issues
        import unittest.mock as mock

        # Mock the secure key manager
        with mock.patch('app.services.ai_service_manager.get_secure_key_manager') as mock_key_manager:
            mock_key_manager.return_value = mock.MagicMock()

            # Mock the base AI service
            with mock.patch('app.services.ai_service_manager.BaseAIService') as mock_base:
                mock_base.return_value = mock.MagicMock()

                from app.services.ai_service_manager import AIServiceManager

                manager = AIServiceManager()
                assert manager is not None

                print("✓ AI Service Manager created successfully")
                return True

    except Exception as e:
        print(f"✗ Failed to create AI Service Manager: {e}")
        return False

def test_service_registration():
    """Test service registration"""
    print("Testing service registration...")

    try:
        import unittest.mock as mock

        with mock.patch('app.services.ai_service_manager.get_secure_key_manager') as mock_key_manager:
            mock_key_manager.return_value = mock.MagicMock()

            with mock.patch('app.services.ai_service_manager.BaseAIService') as mock_base:
                mock_base.return_value = mock.MagicMock()

                from app.services.ai_service_manager import AIServiceManager

                manager = AIServiceManager()

                # Mock a service
                mock_service_class = mock.MagicMock()
                mock_service_instance = mock.MagicMock()
                mock_service_instance.service_name = "test_service"
                mock_service_instance.is_available.return_value = True
                mock_service_class.return_value = mock_service_instance

                # Test registration
                result = manager.register_service("test_service", mock_service_class)
                assert result == True

                print("✓ Service registration works")
                return True

    except Exception as e:
        print(f"✗ Service registration failed: {e}")
        return False

def test_service_fallback():
    """Test service fallback mechanism"""
    print("Testing service fallback mechanism...")

    try:
        import unittest.mock as mock

        with mock.patch('app.services.ai_service_manager.get_secure_key_manager') as mock_key_manager:
            mock_key_manager.return_value = mock.MagicMock()

            with mock.patch('app.services.ai_service_manager.BaseAIService') as mock_base:
                mock_base.return_value = mock.MagicMock()

                from app.services.ai_service_manager import AIServiceManager

                manager = AIServiceManager()

                # Mock failing service
                mock_failing_service = mock.MagicMock()
                mock_failing_service.service_name = "failing_service"
                mock_failing_service.is_available.return_value = False
                mock_failing_service.generate_text.side_effect = Exception("Service down")

                # Mock working service
                mock_working_service = mock.MagicMock()
                mock_working_service.service_name = "working_service"
                mock_working_service.is_available.return_value = True
                mock_working_service.generate_text.return_value = "Fallback response"

                # Register services
                manager.register_service("failing_service", lambda: mock_failing_service)
                manager.register_service("working_service", lambda: mock_working_service)

                # Test fallback
                result = manager.generate_text("Test prompt")
                assert result == "Fallback response"

                print("✓ Service fallback mechanism works")
                return True

    except Exception as e:
        print(f"✗ Service fallback test failed: {e}")
        return False

def test_service_status_tracking():
    """Test service status tracking"""
    print("Testing service status tracking...")

    try:
        import unittest.mock as mock

        with mock.patch('app.services.ai_service_manager.get_secure_key_manager') as mock_key_manager:
            mock_key_manager.return_value = mock.MagicMock()

            with mock.patch('app.services.ai_service_manager.BaseAIService') as mock_base:
                mock_base.return_value = mock.MagicMock()

                from app.services.ai_service_manager import AIServiceManager

                manager = AIServiceManager()

                # Mock service
                mock_service = mock.MagicMock()
                mock_service.service_name = "test_service"
                mock_service.is_available.return_value = True

                manager.register_service("test_service", lambda: mock_service)

                # Test status tracking
                status = manager.check_service_availability("test_service")
                assert status == True

                print("✓ Service status tracking works")
                return True

    except Exception as e:
        print(f"✗ Service status tracking failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("Testing error handling...")

    try:
        import unittest.mock as mock

        with mock.patch('app.services.ai_service_manager.get_secure_key_manager') as mock_key_manager:
            mock_key_manager.return_value = mock.MagicMock()

            with mock.patch('app.services.ai_service_manager.BaseAIService') as mock_base:
                mock_base.return_value = mock.MagicMock()

                from app.services.ai_service_manager import AIServiceManager

                manager = AIServiceManager()

                # Mock service that throws errors
                mock_service = mock.MagicMock()
                mock_service.service_name = "error_service"
                mock_service.is_available.return_value = True
                mock_service.generate_text.side_effect = Exception("Network error")

                manager.register_service("error_service", lambda: mock_service)

                # Test error handling (should not crash)
                try:
                    result = manager.generate_text("Test prompt")
                    # If we get here, error was handled gracefully
                    print("✓ Error handling works")
                    return True
                except Exception as e:
                    print(f"✗ Error not handled gracefully: {e}")
                    return False

    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

def test_concurrent_requests():
    """Test concurrent request handling"""
    print("Testing concurrent request handling...")

    try:
        import unittest.mock as mock
        import threading
        import time

        with mock.patch('app.services.ai_service_manager.get_secure_key_manager') as mock_key_manager:
            mock_key_manager.return_value = mock.MagicMock()

            with mock.patch('app.services.ai_service_manager.BaseAIService') as mock_base:
                mock_base.return_value = mock.MagicMock()

                from app.services.ai_service_manager import AIServiceManager

                manager = AIServiceManager()

                # Mock service that simulates processing time
                def mock_generate_text(prompt):
                    time.sleep(0.1)  # Simulate processing
                    return f"Response to {prompt}"

                mock_service = mock.MagicMock()
                mock_service.service_name = "slow_service"
                mock_service.is_available.return_value = True
                mock_service.generate_text = mock_generate_text

                manager.register_service("slow_service", lambda: mock_service)

                # Test concurrent requests
                results = []
                threads = []

                def make_request(prompt):
                    result = manager.generate_text(prompt)
                    results.append(result)

                # Start multiple threads
                for i in range(3):
                    thread = threading.Thread(target=make_request, args=[f"Prompt {i}"])
                    threads.append(thread)
                    thread.start()

                # Wait for all threads to complete
                for thread in threads:
                    thread.join()

                # Check results
                assert len(results) == 3
                for i, result in enumerate(results):
                    assert f"Response to Prompt {i}" in result

                print("✓ Concurrent request handling works")
                return True

    except Exception as e:
        print(f"✗ Concurrent request test failed: {e}")
        return False

def main():
    """Run all coordinator tests"""
    print("AI Service Coordinator Test Suite")
    print("=" * 50)

    tests = [
        test_service_manager_creation,
        test_service_registration,
        test_service_fallback,
        test_service_status_tracking,
        test_error_handling,
        test_concurrent_requests,
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

    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All coordinator tests passed!")
        return True
    else:
        print("✗ Some coordinator tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)