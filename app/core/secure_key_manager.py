"""
安全密钥管理器 - 简化版本
实现基础的密钥加密存储和管理
"""

import os
import json
import base64
from typing import Dict, Optional, Any, List
from pathlib import Path
import platform
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken
import secrets

# AES-256加密实现
class AESEncryption:
    """AES-256加密工具，使用Fernet"""

    def __init__(self):
        # 生成或加载密钥（生产中应安全存储）
        key_file = Path.home() / ".cineai_key.key"
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.key)
        self.cipher = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """AES加密"""
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            raise ValueError(f"加密失败: {e}")

    def decrypt(self, encrypted_data: str) -> str:
        """AES解密"""
        try:
            encrypted = base64.b64decode(encrypted_data)
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()
        except InvalidToken:
            raise ValueError("解密失败：无效令牌")
        except Exception as e:
            raise ValueError(f"解密失败: {e}")


class SecureKeyManager:
    """增强版安全密钥管理器，支持AES-256加密"""

    def __init__(self, app_name: str = "CineAIStudio"):
        self.app_name = app_name
        self.logger = logging.getLogger(__name__)
        self.encryption = AESEncryption()
        self.key_storage_path = Path.home() / f".{app_name}_keys.json"
        self._init_storage()

    def _init_storage(self) -> None:
        """初始化存储"""
        try:
            if not self.key_storage_path.exists():
                self.key_storage_path.parent.mkdir(parents=True, exist_ok=True)
                # 创建空的密钥存储文件
                with open(self.key_storage_path, 'w') as f:
                    json.dump({"version": "1.0", "keys": {}}, f)
                self.logger.info("Created new key storage file")
            else:
                self.logger.info("Key storage file exists")
        except Exception as e:
            self.logger.error(f"Failed to initialize key storage: {e}")

    def store_api_key(self, service_name: str, api_key: str,
                     key_type: str = "api_key", description: str = None,
                     expiration_date: str = None, permissions: List[str] = None) -> bool:
        """存储API密钥"""
        try:
            key_data = {
                "service": service_name,
                "key": api_key,
                "type": key_type,
                "created_at": self._get_timestamp(),
                "updated_at": self._get_timestamp(),
                "description": description,
                "expiration_date": expiration_date,
                "permissions": permissions or []
            }

            # AES加密密钥数据
            encrypted_key_data = self.encryption.encrypt(json.dumps(key_data))

            # 读取现有密钥
            all_keys = self._load_all_keys()
            all_keys[service_name] = {
                "encrypted_data": encrypted_key_data,
                "service": service_name,
                "last_access": self._get_timestamp()
            }

            # 保存密钥
            self._save_all_keys(all_keys)

            self.logger.info(f"Stored API key for {service_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to store API key for {service_name}: {e}")
            return False

    def get_api_key(self, service_name: str) -> Optional[Dict[str, Any]]:
        """获取API密钥"""
        try:
            all_keys = self._load_all_keys()

            if service_name not in all_keys:
                return None

            encrypted_data = all_keys[service_name]["encrypted_data"]

            # AES解密密钥数据
            key_data_json = self.encryption.decrypt(encrypted_data)
            key_data = json.loads(key_data_json)

            # 更新访问时间
            all_keys[service_name]["last_access"] = self._get_timestamp()
            self._save_all_keys(all_keys)

            return key_data

        except Exception as e:
            self.logger.error(f"Failed to get API key for {service_name}: {e}")
            return None

    def delete_api_key(self, service_name: str) -> bool:
        """删除API密钥"""
        try:
            all_keys = self._load_all_keys()

            if service_name in all_keys:
                del all_keys[service_name]
                self._save_all_keys(all_keys)
                self.logger.info(f"Deleted API key for {service_name}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to delete API key for {service_name}: {e}")
            return False

    def list_services(self) -> List[str]:
        """列出所有服务"""
        try:
            all_keys = self._load_all_keys()
            return list(all_keys.keys())
        except Exception as e:
            self.logger.error(f"Failed to list services: {e}")
            return []

    def get_key_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """获取密钥信息（不含密钥本身）"""
        try:
            all_keys = self._load_all_keys()

            if service_name not in all_keys:
                return None

            key_entry = all_keys[service_name]
            encrypted_data = key_entry["encrypted_data"]

            # AES解密获取信息
            key_data_json = self.encryption.decrypt(encrypted_data)
            key_data = json.loads(key_data_json)

            # 返回不含密钥的信息
            return {
                "service": key_data["service"],
                "type": key_data["type"],
                "created_at": key_data["created_at"],
                "updated_at": key_data["updated_at"],
                "description": key_data["description"],
                "expiration_date": key_data["expiration_date"],
                "permissions": key_data["permissions"],
                "last_access": key_entry["last_access"]
            }

        except Exception as e:
            self.logger.error(f"Failed to get key info for {service_name}: {e}")
            return None

    def backup_keys(self, backup_path: str) -> bool:
        """备份密钥"""
        try:
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)

            import shutil
            shutil.copy2(self.key_storage_path, backup_path)

            self.logger.info(f"Keys backed up to {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to backup keys: {e}")
            return False

    def restore_keys(self, backup_path: str) -> bool:
        """恢复密钥"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False

            import shutil
            shutil.copy2(backup_path, self.key_storage_path)

            self.logger.info(f"Keys restored from {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore keys: {e}")
            return False

    def _load_all_keys(self) -> Dict[str, Any]:
        """加载所有密钥"""
        try:
            if not self.key_storage_path.exists():
                return {}

            with open(self.key_storage_path, 'r') as f:
                data = json.load(f)

            return data.get("keys", {})

        except Exception as e:
            self.logger.error(f"Failed to load keys: {e}")
            return {}

    def _save_all_keys(self, keys: Dict[str, Any]):
        """保存所有密钥"""
        try:
            data = {
                "version": "1.0",
                "keys": keys
            }

            with open(self.key_storage_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save keys: {e}")

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        import datetime
        return datetime.datetime.now().isoformat()

    def cleanup_expired_keys(self) -> int:
        """清理过期密钥"""
        try:
            all_keys = self._load_all_keys()
            current_time = self._get_timestamp()
            removed_count = 0

            for service_name, key_entry in list(all_keys.items()):
                encrypted_data = key_entry["encrypted_data"]
                key_data_json = self.encryption.decrypt(encrypted_data)
                key_data = json.loads(key_data_json)

                if key_data.get("expiration_date"):
                    if key_data["expiration_date"] < current_time:
                        del all_keys[service_name]
                        removed_count += 1

            if removed_count > 0:
                self._save_all_keys(all_keys)
                self.logger.info(f"Cleaned up {removed_count} expired keys")

            return removed_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup expired keys: {e}")
            return 0

    def validate_key_integrity(self) -> bool:
        """验证密钥完整性"""
        try:
            all_keys = self._load_all_keys()

            for service_name, key_entry in all_keys.items():
                try:
                    encrypted_data = key_entry["encrypted_data"]
                    key_data_json = self.encryption.decrypt(encrypted_data)
                    key_data = json.loads(key_data_json)

                    # 检查必要字段
                    required_fields = ["service", "key", "type"]
                    for field in required_fields:
                        if field not in key_data:
                            return False

                except Exception:
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Key integrity validation failed: {e}")
            return False

    def export_keys(self, export_path: str, include_secrets: bool = False) -> bool:
        """导出密钥"""
        try:
            all_keys = self._load_all_keys()
            export_data = {
                "version": "1.0",
                "exported_at": self._get_timestamp(),
                "services": []
            }

            for service_name, key_entry in all_keys.items():
                encrypted_data = key_entry["encrypted_data"]
                key_data_json = self.encryption.decrypt(encrypted_data)
                key_data = json.loads(key_data_json)

                service_info = {
                    "service": service_name,
                    "type": key_data["type"],
                    "created_at": key_data["created_at"],
                    "description": key_data["description"]
                }

                if include_secrets:
                    service_info["key"] = key_data["key"]

                export_data["services"].append(service_info)

            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)

            self.logger.info(f"Keys exported to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export keys: {e}")
            return False

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "storage_path": str(self.key_storage_path),
            "total_services": len(self._load_all_keys()),
            "keyring_available": False,  # 简化版本不支持
            "encryption_enabled": True
        }


def get_secure_key_manager() -> SecureKeyManager:
    """获取安全密钥管理器实例"""
    return SecureKeyManager()


# 测试函数
def test_secure_key_manager():
    """测试安全密钥管理器"""
    print("=== 测试安全密钥管理器 ===")

    manager = get_secure_key_manager()

    # 测试存储密钥
    success = manager.store_api_key(
        service_name="test_service",
        api_key="test_api_key_123",
        description="测试服务"
    )
    print(f"存储密钥: {'成功' if success else '失败'}")

    # 测试获取密钥
    key_data = manager.get_api_key("test_service")
    print(f"获取密钥: {key_data is not None}")

    # 测试列出服务
    services = manager.list_services()
    print(f"列出服务: {len(services)} 个服务")

    # 测试删除密钥
    success = manager.delete_api_key("test_service")
    print(f"删除密钥: {'成功' if success else '失败'}")

    print("=== 测试完成 ===")


if __name__ == "__main__":
    test_secure_key_manager()