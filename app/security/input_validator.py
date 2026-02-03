#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineAIStudio 输入验证器
提供全面的输入验证和数据清理功能
"""

import re
import os
import json
import html
import hashlib
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

from ..core.logger import Logger


class ValidationLevel(Enum):
    """验证级别"""
    NONE = "none"                    # 不验证
    BASIC = "basic"                  # 基础验证
    STRICT = "strict"                # 严格验证
    PARANOID = "paranoid"            # 偏执级验证


class ValidationType(Enum):
    """验证类型"""
    REQUIRED = "required"            # 必填
    OPTIONAL = "optional"            # 可选
    SANITIZE = "sanitize"            # 清理


@dataclass
class ValidationRule:
    """验证规则"""
    name: str
    type: ValidationType
    level: ValidationLevel
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    forbidden_values: Optional[List[Any]] = None
    custom_validator: Optional[callable] = None
    error_message: Optional[str] = None


class InputValidator:
    """输入验证器"""

    def __init__(self, logger: Logger):
        self.logger = logger
        self._validation_errors: List[str] = []

        # 预定义验证模式
        self.patterns = {
            "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            "url": r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$',
            "filename": r'^[a-zA-Z0-9._-]+$',
            "path": r'^[a-zA-Z0-9/._-]+$',
            "username": r'^[a-zA-Z0-9._-]{3,32}$',
            "password": r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
            "phone": r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$',
            "ip_address": r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
            "port": r'^[0-9]{1,5}$',
            "uuid": r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
            "semantic_version": r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$',
            "json_path": r'^\$\.([a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*|\*|\[\d+\]|\[\*\])*$',
            "api_key": r'^[a-zA-Z0-9]{16,64}$',
            "session_token": r'^[a-zA-Z0-9+/]{32,64}={0,2}$'
        }

        # 危险模式
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',           # XSS
            r'javascript:',                        # JavaScript
            r'vbscript:',                          # VBScript
            r'onload\s*=',                        # 事件处理
            r'onerror\s*=',                       # 事件处理
            r'onclick\s*=',                       # 事件处理
            r'eval\s*\(',                         # eval函数
            r'exec\s*\(',                         # exec函数
            r'system\s*\(',                       # system函数
            r'shell_exec\s*\(',                   # shell_exec函数
            r'passthru\s*\(',                     # passthru函数
            r'file_get_contents\s*\(',            # 文件读取
            r'file_put_contents\s*\(',            # 文件写入
            r'unlink\s*\(',                       # 文件删除
            r'mkdir\s*\(',                        # 目录创建
            r'rmdir\s*\(',                        # 目录删除
            r'fopen\s*\(',                        # 文件打开
            r'\.\./',                             # 路径遍历
            r'\.\.\\',                            # 路径遍历
            r'^\/\.\.',                           # 绝对路径遍历
            r'<\?php',                            # PHP标签
            r'<%',                                # ASP标签
            r'<!--.*?-->',                        # HTML注释
            r'union\s+select',                    # SQL注入
            r'drop\s+table',                      # SQL注入
            r'delete\s+from',                     # SQL注入
            r'insert\s+into',                     # SQL注入
            r'update\s+.+\s+set',                 # SQL注入
            r'select\s+.+\s+from',                # SQL注入
        ]

        # 危险扩展名
        self.dangerous_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js', '.jar',
            '.app', '.deb', '.pkg', '.dmg', '.rpm', '.msi', '.msp', '.msm',
            '.php', '.asp', '.aspx', '.jsp', '.cgi', '.pl', '.py', '.rb',
            '.sh', '.ps1', '.bash', '.zsh', '.csh', '.tcsh', '.ksh',
            '.sql', '.db', '.mdb', '.sqlite', '.sqlite3', '.bin', '.dat'
        }

        # 允许的MIME类型
        self.allowed_mime_types = {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
            'video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/flv',
            'video/webm', 'video/mkv', 'audio/mp3', 'audio/wav', 'audio/flac',
            'audio/aac', 'audio/ogg', 'text/plain', 'text/csv', 'text/xml',
            'text/html', 'application/json', 'application/pdf', 'application/zip',
            'application/xml', 'application/x-yaml'
        }

    def validate_string(self, value: str, rules: List[ValidationRule],
                       level: ValidationLevel = ValidationLevel.STRICT) -> Tuple[bool, str]:
        """验证字符串"""
        self._validation_errors.clear()

        for rule in rules:
            if not self._apply_rule(value, rule, level):
                return False, rule.error_message or f"Validation failed for rule: {rule.name}"

        return True, ""

    def validate_dict(self, data: Dict[str, Any], schema: Dict[str, ValidationRule],
                     level: ValidationLevel = ValidationLevel.STRICT) -> Tuple[bool, Dict[str, str]]:
        """验证字典数据"""
        self._validation_errors.clear()
        errors = {}

        # 检查必填字段
        for field_name, rule in schema.items():
            if rule.type == ValidationType.REQUIRED and field_name not in data:
                errors[field_name] = "Field is required"
                continue

            if field_name not in data:
                continue

            # 验证字段值
            value = data[field_name]
            is_valid, error = self._apply_validation(field_name, value, rule, level)
            if not is_valid:
                errors[field_name] = error

        return len(errors) == 0, errors

    def validate_file_path(self, file_path: str, allowed_extensions: Optional[List[str]] = None,
                          max_depth: int = 10) -> Tuple[bool, str]:
        """验证文件路径"""
        try:
            # 规范化路径
            normalized_path = os.path.normpath(file_path)

            # 检查路径遍历
            if '..' in normalized_path:
                return False, "Path traversal detected"

            # 检查路径深度
            path_parts = normalized_path.split(os.sep)
            if len(path_parts) > max_depth:
                return False, f"Path depth exceeds maximum ({max_depth})"

            # 检查文件扩展名
            if allowed_extensions:
                _, ext = os.path.splitext(normalized_path)
                if ext.lower() not in allowed_extensions:
                    return False, f"File extension {ext} not allowed"

            # 检查危险扩展名
            _, ext = os.path.splitext(normalized_path)
            if ext.lower() in self.dangerous_extensions:
                return False, f"Dangerous file extension: {ext}"

            return True, ""

        except Exception as e:
            return False, f"Invalid file path: {e}"

    def validate_url(self, url: str, allowed_schemes: Optional[List[str]] = None) -> Tuple[bool, str]:
        """验证URL"""
        try:
            parsed = urlparse(url)

            # 检查协议
            schemes = allowed_schemes or ['http', 'https']
            if parsed.scheme.lower() not in schemes:
                return False, f"URL scheme not allowed: {parsed.scheme}"

            # 检查主机名
            if not parsed.hostname:
                return False, "Invalid URL hostname"

            # 检查本地主机
            if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
                return False, "Localhost URLs not allowed"

            # 检查私有网络
            if self._is_private_ip(parsed.hostname):
                return False, "Private IP addresses not allowed"

            return True, ""

        except Exception as e:
            return False, f"Invalid URL: {e}"

    def validate_html(self, html_content: str, allowed_tags: Optional[List[str]] = None,
                     allowed_attributes: Optional[List[str]] = None) -> Tuple[bool, str]:
        """验证HTML内容"""
        try:
            import bleach

            # 默认允许的标签和属性
            default_allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'a']
            default_allowed_attrs = {'a': ['href', 'title']}

            # 清理HTML
            cleaned_html = bleach.clean(
                html_content,
                tags=allowed_tags or default_allowed_tags,
                attributes=allowed_attributes or default_allowed_attrs,
                strip=True
            )

            # 检查是否有危险内容被移除
            if len(cleaned_html) < len(html_content) * 0.5:
                return False, "HTML contains potentially dangerous content"

            return True, cleaned_html

        except ImportError:
            # 如果没有安装bleach，使用基础清理
            return self._sanitize_html_basic(html_content)

    def validate_json(self, json_str: str, schema: Optional[Dict] = None) -> Tuple[bool, Any]:
        """验证JSON数据"""
        try:
            data = json.loads(json_str)

            # 如果提供了schema，进行验证
            if schema:
                is_valid, errors = self._validate_json_schema(data, schema)
                if not is_valid:
                    return False, errors

            return True, data

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"

    def sanitize_input(self, value: str, level: ValidationLevel = ValidationLevel.STRICT) -> str:
        """清理输入"""
        if not value:
            return value

        # HTML实体编码
        sanitized = html.escape(value)

        # 移除危险内容
        for pattern in self.dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)

        # 根据级别进行额外清理
        if level in [ValidationLevel.STRICT, ValidationLevel.PARANOID]:
            # 移除控制字符
            sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')

            if level == ValidationLevel.PARANOID:
                # 移除所有非ASCII字符
                sanitized = ''.join(char for char in sanitized if ord(char) < 128)

        return sanitized.strip()

    def generate_csrf_token(self, secret_key: str, session_id: str) -> str:
        """生成CSRF令牌"""
        timestamp = str(int(time.time()))
        message = f"{secret_key}:{session_id}:{timestamp}"
        return hashlib.sha256(message.encode()).hexdigest()

    def validate_csrf_token(self, token: str, secret_key: str, session_id: str,
                           max_age: int = 3600) -> bool:
        """验证CSRF令牌"""
        try:
            # 检查令牌格式
            if not re.match(r'^[a-f0-9]{64}$', token):
                return False

            # 生成当前时间窗口内的有效令牌
            current_time = int(time.time())
            for offset in range(-300, 301, 60):  # 5分钟窗口，每分钟检查
                timestamp = str(current_time + offset)
                message = f"{secret_key}:{session_id}:{timestamp}"
                expected_token = hashlib.sha256(message.encode()).hexdigest()

                if token == expected_token:
                    return True

            return False

        except Exception:
            return False

    def validate_api_key(self, api_key: str, service: str) -> bool:
        """验证API密钥格式"""
        patterns = {
            "openai": r'^sk-[A-Za-z0-9]{48}$',
            "anthropic": r'^sk-ant-[A-Za-z0-9_-]{95}$',
            "google": r'^[A-Za-z0-9_-]{39}$',
            "baidu": r'^[A-Za-z0-9]{24}$',
            "alibaba": r'^sk-[A-Za-z0-9]{32}$'
        }

        pattern = patterns.get(service.lower(), self.patterns["api_key"])
        return bool(re.match(pattern, api_key))

    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """哈希密码"""
        if salt is None:
            salt = os.urandom(32).hex()

        # 使用PBKDF2进行密码哈希
        import hashlib
        iterations = 100000
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), iterations)
        return dk.hex(), salt

    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """验证密码"""
        expected_hash, _ = self.hash_password(password, salt)
        return expected_hash == hashed

    def _apply_rule(self, value: str, rule: ValidationRule, level: ValidationLevel) -> bool:
        """应用验证规则"""
        # 检查必填性
        if rule.type == ValidationType.REQUIRED and not value:
            return False

        # 空值检查
        if not value and rule.type == ValidationType.OPTIONAL:
            return True

        # 长度检查
        if rule.min_length is not None and len(value) < rule.min_length:
            return False

        if rule.max_length is not None and len(value) > rule.max_length:
            return False

        # 模式检查
        if rule.pattern:
            if not re.match(rule.pattern, value):
                return False

        # 允许值检查
        if rule.allowed_values and value not in rule.allowed_values:
            return False

        # 禁止值检查
        if rule.forbidden_values and value in rule.forbidden_values:
            return False

        # 自定义验证器
        if rule.custom_validator:
            return rule.custom_validator(value)

        return True

    def _apply_validation(self, field_name: str, value: Any, rule: ValidationRule,
                         level: ValidationLevel) -> Tuple[bool, str]:
        """应用验证"""
        # 类型检查
        if not isinstance(value, str):
            return False, f"Expected string, got {type(value).__name__}"

        # 应用规则
        if not self._apply_rule(value, rule, level):
            return False, rule.error_message or f"Validation failed for field: {field_name}"

        # 清理输入
        if rule.type == ValidationType.SANITIZE:
            sanitized_value = self.sanitize_input(value, level)
            if sanitized_value != value:
                self.logger.warning(f"Input sanitized for field: {field_name}")

        return True, ""

    def _sanitize_html_basic(self, html_content: str) -> Tuple[bool, str]:
        """基础HTML清理"""
        # 移除所有标签
        cleaned = re.sub(r'<[^>]+>', '', html_content)
        # HTML实体解码
        cleaned = html.unescape(cleaned)
        return True, cleaned

    def _is_private_ip(self, hostname: str) -> bool:
        """检查是否为私有IP"""
        try:
            import ipaddress
            ip = ipaddress.ip_address(hostname)
            return ip.is_private
        except ValueError:
            return False

    def _validate_json_schema(self, data: Any, schema: Dict) -> Tuple[bool, List[str]]:
        """验证JSON schema"""
        errors = []

        # 简化的schema验证
        # 实际实现应该使用jsonschema库
        def validate_value(value, schema_part, path=""):
            if isinstance(schema_part, dict):
                if "type" in schema_part:
                    expected_type = schema_part["type"]
                    if expected_type == "string" and not isinstance(value, str):
                        errors.append(f"{path}: Expected string, got {type(value).__name__}")
                    elif expected_type == "number" and not isinstance(value, (int, float)):
                        errors.append(f"{path}: Expected number, got {type(value).__name__}")
                    elif expected_type == "boolean" and not isinstance(value, bool):
                        errors.append(f"{path}: Expected boolean, got {type(value).__name__}")
                    elif expected_type == "array" and not isinstance(value, list):
                        errors.append(f"{path}: Expected array, got {type(value).__name__}")
                    elif expected_type == "object" and not isinstance(value, dict):
                        errors.append(f"{path}: Expected object, got {type(value).__name__}")

                if "required" in schema_part:
                    for field in schema_part["required"]:
                        if field not in value:
                            errors.append(f"{path}.{field}: Required field missing")

                if "properties" in schema_part:
                    for field, field_schema in schema_part["properties"].items():
                        if field in value:
                            validate_value(value[field], field_schema, f"{path}.{field}")

        validate_value(data, schema)
        return len(errors) == 0, errors

    @property
    def validation_errors(self) -> List[str]:
        """获取验证错误"""
        return self._validation_errors.copy()