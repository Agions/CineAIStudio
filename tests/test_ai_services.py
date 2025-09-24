"""
AI Services Test Suite for CineAIStudio
Comprehensive testing framework for AI model integration
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from typing import Dict, Any, List
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.services.ai_service_manager import AIServiceManager
from app.services.chinese_ai_services import (
    WenxinService, SparkService, QwenService,
    GLMService, BaichuanService, MoonshotService
)
from app.core.secure_key_manager import SecureKeyManager, get_secure_key_manager
from app.ui.components.ai_content_generator import AIContentGenerator
from app.ui.components.ai_demo_widget import AIDemoWidget


class TestSecureKeyManager(unittest.TestCase):
    """Test secure key management functionality"""

    def setUp(self):
        """Set up test environment"""
        self.key_manager = SecureKeyManager()

    def test_singleton_pattern(self):
        """Test that SecureKeyManager follows singleton pattern"""
        manager2 = SecureKeyManager()
        self.assertIs(self.key_manager, manager2)

    def test_get_secure_key_manager_function(self):
        """Test the get_secure_key_manager function"""
        manager = get_secure_key_manager()
        self.assertIsInstance(manager, SecureKeyManager)

    def test_api_key_encryption_decryption(self):
        """Test API key encryption and decryption"""
        test_key = "test_api_key_12345"
        service_name = "test_service"

        # Store and retrieve key
        self.key_manager.store_api_key(service_name, test_key)
        retrieved_key = self.key_manager.get_api_key(service_name)

        self.assertEqual(test_key, retrieved_key)

    def test_api_key_masking(self):
        """Test that API keys are properly masked in logs"""
        test_key = "sk-1234567890abcdef"
        service_name = "test_service"

        self.key_manager.store_api_key(service_name, test_key)
        masked_key = self.key_manager.get_masked_api_key(service_name)

        # Key should be masked except for first 4 and last 4 characters
        self.assertTrue(masked_key.startswith("sk-12"))
        self.assertTrue(masked_key.endswith("cdef"))
        self.assertIn("*", masked_key)

    def test_nonexistent_key_retrieval(self):
        """Test retrieval of non-existent keys"""
        result = self.key_manager.get_api_key("nonexistent_service")
        self.assertIsNone(result)

    def test_available_services_detection(self):
        """Test detection of available services"""
        services = self.key_manager.get_available_services()
        self.assertIsInstance(services, list)
        self.assertIn("openai", services)  # Default service


class TestChineseAIServices(unittest.TestCase):
    """Test Chinese AI service implementations"""

    def setUp(self):
        """Set up test environment"""
        self.key_manager = get_secure_key_manager()

    def test_wenxin_service_initialization(self):
        """Test Baidu Wenxin service initialization"""
        with patch('app.services.chinese_ai_services.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"access_token": "test_token"}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            service = WenxinService()
            self.assertIsNotNone(service)
            self.assertEqual(service.service_name, "wenxin")

    def test_spark_service_initialization(self):
        """Test iFlytek Spark service initialization"""
        service = SparkService()
        self.assertIsNotNone(service)
        self.assertEqual(service.service_name, "spark")

    def test_qwen_service_initialization(self):
        """Test Alibaba Qwen service initialization"""
        service = QwenService()
        self.assertIsNotNone(service)
        self.assertEqual(service.service_name, "qwen")

    def test_glm_service_initialization(self):
        """Test Zhipu GLM service initialization"""
        service = GLMService()
        self.assertIsNotNone(service)
        self.assertEqual(service.service_name, "glm")

    def test_baichuan_service_initialization(self):
        """Test Baichuan service initialization"""
        service = BaichuanService()
        self.assertIsNotNone(service)
        self.assertEqual(service.service_name, "baichuan")

    def test_moonshot_service_initialization(self):
        """Test Moonshot service initialization"""
        service = MoonshotService()
        self.assertIsNotNone(service)
        self.assertEqual(service.service_name, "moonshot")

    @patch('app.services.chinese_ai_services.requests.post')
    def test_wenxin_generate_text(self, mock_post):
        """Test Wenxin text generation"""
        # Mock authentication response
        auth_response = Mock()
        auth_response.json.return_value = {"access_token": "test_token"}
        auth_response.raise_for_status.return_value = None

        # Mock generation response
        gen_response = Mock()
        gen_response.json.return_value = {
            "result": "Generated text response",
            "usage": {"total_tokens": 100}
        }
        gen_response.raise_for_status.return_value = None

        mock_post.side_effect = [auth_response, gen_response]

        # Store test API key
        self.key_manager.store_api_key("wenxin", "test_key")

        service = WenxinService()
        result = service.generate_text("Test prompt")

        self.assertEqual(result, "Generated text response")

    @patch('app.services.chinese_ai_services.requests.post')
    def test_spark_generate_text(self, mock_post):
        """Test Spark text generation"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "payload": {
                "choices": {
                    "text": [{"content": "Generated response"}]
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        self.key_manager.store_api_key("spark", "test_key")

        service = SparkService()
        result = service.generate_text("Test prompt")

        self.assertEqual(result, "Generated response")

    @patch('app.services.chinese_ai_services.requests.post')
    def test_qwen_generate_text(self, mock_post):
        """Test Qwen text generation"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "output": {
                "text": "Generated response"
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        self.key_manager.store_api_key("qwen", "test_key")

        service = QwenService()
        result = service.generate_text("Test prompt")

        self.assertEqual(result, "Generated response")


class TestAIServiceManager(unittest.TestCase):
    """Test AI Service Manager coordination"""

    def setUp(self):
        """Set up test environment"""
        self.manager = AIServiceManager()

    def test_manager_initialization(self):
        """Test service manager initialization"""
        self.assertIsNotNone(self.manager)
        self.assertIsInstance(self.manager.services, dict)
        self.assertIsInstance(self_manager.service_status, dict)

    def test_service_registration(self):
        """Test service registration"""
        with patch('app.services.ai_service_manager.WenxinService') as mock_service:
            mock_instance = Mock()
            mock_instance.service_name = "test_service"
            mock_instance.is_available.return_value = True
            mock_service.return_value = mock_instance

            result = self.manager.register_service("test_service", mock_service)
            self.assertTrue(result)
            self.assertIn("test_service", self.manager.services)

    def test_service_availability_check(self):
        """Test service availability checking"""
        with patch('app.services.ai_service_manager.WenxinService') as mock_service:
            mock_instance = Mock()
            mock_instance.service_name = "test_service"
            mock_instance.is_available.return_value = True
            mock_service.return_value = mock_instance

            self.manager.register_service("test_service", mock_service)
            available = self.manager.check_service_availability("test_service")

            self.assertTrue(available)

    def test_fallback_service_selection(self):
        """Test fallback service selection"""
        # Register multiple services
        with patch('app.services.ai_service_manager.WenxinService') as mock_wenxin:
            mock_wenxin.return_value = Mock(service_name="wenxin", is_available=lambda: False)

            with patch('app.services.ai_service_manager.SparkService') as mock_spark:
                mock_spark.return_value = Mock(service_name="spark", is_available=lambda: True)

                self.manager.register_service("wenxin", mock_wenxin)
                self.manager.register_service("spark", mock_spark)

                selected = self.manager.get_available_service()

                self.assertEqual(selected, "spark")

    def test_generate_text_with_fallback(self):
        """Test text generation with service fallback"""
        with patch('app.services.ai_service_manager.WenxinService') as mock_wenxin:
            mock_wenxin_instance = Mock()
            mock_wenxin_instance.service_name = "wenxin"
            mock_wenxin_instance.is_available.return_value = False
            mock_wenxin_instance.generate_text.side_effect = Exception("Service unavailable")
            mock_wenxin.return_value = mock_wenxin_instance

            with patch('app.services.ai_service_manager.SparkService') as mock_spark:
                mock_spark_instance = Mock()
                mock_spark_instance.service_name = "spark"
                mock_spark_instance.is_available.return_value = True
                mock_spark_instance.generate_text.return_value = "Fallback response"
                mock_spark.return_value = mock_spark_instance

                self.manager.register_service("wenxin", mock_wenxin)
                self.manager.register_service("spark", mock_spark)

                result = self.manager.generate_text("Test prompt")

                self.assertEqual(result, "Fallback response")


class TestAIContentGenerator(unittest.TestCase):
    """Test AI content generator UI component"""

    def setUp(self):
        """Set up test environment"""
        with patch('app.ui.components.ai_content_generator.AIServiceManager') as mock_manager_class:
            self.mock_manager = Mock()
            self.mock_manager.get_available_services.return_value = ["wenxin", "spark"]
            self.mock_manager.generate_text.return_value = "Generated content"
            mock_manager_class.return_value = self.mock_manager

            self.generator = AIContentGenerator()

    def test_content_generator_initialization(self):
        """Test content generator initialization"""
        self.assertIsNotNone(self.generator)
        self.assertIsNotNone(self.generator.service_manager)

    def test_generate_content(self):
        """Test content generation"""
        self.generator.prompt_input.setText("Test prompt")
        self.generator.generate_content()

        # Verify manager was called
        self.mock_manager.generate_text.assert_called_once()

    def test_service_selection(self):
        """Test service selection"""
        # Test service selection updates
        available_services = ["wenxin", "spark", "qwen"]
        self.generator.update_service_list(available_services)

        # Verify UI was updated
        self.assertEqual(self.generator.service_selector.count(), len(available_services))


class TestAIDemoWidget(unittest.TestCase):
    """Test AI demo widget"""

    def setUp(self):
        """Set up test environment"""
        with patch('app.ui.components.ai_demo_widget.AIServiceManager') as mock_manager_class:
            self.mock_manager = Mock()
            self.mock_manager.get_available_services.return_value = ["wenxin", "spark"]
            self.mock_manager.generate_text.return_value = "Demo response"
            mock_manager_class.return_value = self.mock_manager

            self.demo_widget = AIDemoWidget()

    def test_demo_widget_initialization(self):
        """Test demo widget initialization"""
        self.assertIsNotNone(self.demo_widget)
        self.assertIsNotNone(self.demo_widget.service_manager)

    def test_demo_generation(self):
        """Test demo generation"""
        self.demo_widget.generate_demo()

        # Verify manager was called
        self.mock_manager.generate_text.assert_called_once()

    def test_error_handling(self):
        """Test error handling in demo widget"""
        self.mock_manager.generate_text.side_effect = Exception("Service error")

        # Should not crash, should handle error gracefully
        self.demo_widget.generate_demo()

        # Verify error was handled
        self.assertTrue(True)  # If we get here, no exception was raised


class TestAIIntegration(unittest.TestCase):
    """Test overall AI integration"""

    def setUp(self):
        """Set up test environment"""
        self.key_manager = get_secure_key_manager()

    def test_all_services_initialization(self):
        """Test that all AI services can be initialized"""
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
                self.assertIsNotNone(service)
                self.assertTrue(hasattr(service, 'service_name'))
                self.assertTrue(hasattr(service, 'generate_text'))
            except Exception as e:
                self.fail(f"Failed to initialize {service_class.__name__}: {e}")

    def test_service_cooperation(self):
        """Test that services can work together"""
        manager = AIServiceManager()

        # Mock services
        with patch('app.services.ai_service_manager.WenxinService') as mock_wenxin:
            mock_wenxin.return_value = Mock(
                service_name="wenxin",
                is_available=lambda: True,
                generate_text=lambda x: "Wenxin response"
            )

            with patch('app.services.ai_service_manager.SparkService') as mock_spark:
                mock_spark.return_value = Mock(
                    service_name="spark",
                    is_available=lambda: True,
                    generate_text=lambda x: "Spark response"
                )

                manager.register_service("wenxin", mock_wenxin)
                manager.register_service("spark", mock_spark)

                # Test both services are available
                self.assertEqual(len(manager.get_available_services()), 2)

                # Test generation works
                result = manager.generate_text("Test")
                self.assertIn(result, ["Wenxin response", "Spark response"])

    def test_error_recovery(self):
        """Test error recovery mechanisms"""
        manager = AIServiceManager()

        # Mock failing service
        with patch('app.services.ai_service_manager.WenxinService') as mock_wenxin:
            mock_wenxin.return_value = Mock(
                service_name="wenxin",
                is_available=lambda: False,
                generate_text=lambda x: (_ for _ in ()).throw(Exception("Service failed"))
            )

            # Mock working service
            with patch('app.services.ai_service_manager.SparkService') as mock_spark:
                mock_spark.return_value = Mock(
                    service_name="spark",
                    is_available=lambda: True,
                    generate_text=lambda x: "Fallback response"
                )

                manager.register_service("wenxin", mock_wenxin)
                manager.register_service("spark", mock_spark)

                # Should fall back to working service
                result = manager.generate_text("Test")
                self.assertEqual(result, "Fallback response")


class TestAIPerformance(unittest.TestCase):
    """Test AI service performance"""

    def test_response_time_measurement(self):
        """Test response time measurement"""
        import time

        manager = AIServiceManager()

        with patch('app.services.ai_service_manager.WenxinService') as mock_service:
            mock_instance = Mock()
            mock_instance.service_name = "wenxin"
            mock_instance.is_available.return_value = True
            # Simulate processing time
            mock_instance.generate_text = lambda x: time.sleep(0.1) or "Response"
            mock_service.return_value = mock_instance

            manager.register_service("wenxin", mock_service)

            start_time = time.time()
            result = manager.generate_text("Test")
            end_time = time.time()

            self.assertGreater(end_time - start_time, 0.1)
            self.assertEqual(result, "Response")

    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        manager = AIServiceManager()

        with patch('app.services.ai_service_manager.WenxinService') as mock_service:
            mock_instance = Mock()
            mock_instance.service_name = "wenxin"
            mock_instance.is_available.return_value = True
            mock_instance.generate_text = lambda x: f"Response to {x}"
            mock_service.return_value = mock_instance

            manager.register_service("wenxin", mock_service)

            # Test multiple requests
            results = []
            for i in range(5):
                result = manager.generate_text(f"Prompt {i}")
                results.append(result)

            self.assertEqual(len(results), 5)
            for i, result in enumerate(results):
                self.assertEqual(result, f"Response to Prompt {i}")


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTest(unittest.makeSuite(TestSecureKeyManager))
    suite.addTest(unittest.makeSuite(TestChineseAIServices))
    suite.addTest(unittest.makeSuite(TestAIServiceManager))
    suite.addTest(unittest.makeSuite(TestAIContentGenerator))
    suite.addTest(unittest.makeSuite(TestAIDemoWidget))
    suite.addTest(unittest.makeSuite(TestAIIntegration))
    suite.addTest(unittest.makeSuite(TestAIPerformance))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print results
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)