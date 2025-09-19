#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path
from typing import Dict, Optional
from cryptography.fernet import Fernet
import base64


class APIKeyManager:
    """API密钥管理器 - 提供加密存储和安全访问"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 密钥文件路径
        self.key_file = self.config_dir / ".key"
        self.api_keys_file = self.config_dir / ".api_keys"
        
        # 初始化加密密钥
        self._init_encryption_key()
        
        # 加载API密钥
        self._api_keys = {}
        self._load_api_keys()
    
    def _init_encryption_key(self):
        """初始化加密密钥"""
        if self.key_file.exists():
            # 读取现有密钥
            with open(self.key_file, 'rb') as f:
                key_data = f.read()
            self._fernet = Fernet(key_data)
        else:
            # 生成新密钥
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # 设置文件权限（仅所有者可读写）
            os.chmod(self.key_file, 0o600)
            self._fernet = Fernet(key)
    
    def _load_api_keys(self):
        """加载API密钥"""
        try:
            if self.api_keys_file.exists():
                with open(self.api_keys_file, 'rb') as f:
                    encrypted_data = f.read()
                
                if encrypted_data:
                    # 解密数据
                    decrypted_data = self._fernet.decrypt(encrypted_data)
                    self._api_keys = json.loads(decrypted_data.decode('utf-8'))
                else:
                    self._api_keys = {}
            else:
                self._api_keys = {}
        except Exception as e:
            print(f"加载API密钥失败: {e}")
            self._api_keys = {}
    
    def _save_api_keys(self):
        """保存API密钥"""
        try:
            # 序列化并加密数据
            json_data = json.dumps(self._api_keys, ensure_ascii=False)
            encrypted_data = self._fernet.encrypt(json_data.encode('utf-8'))
            
            # 写入文件
            with open(self.api_keys_file, 'wb') as f:
                f.write(encrypted_data)
            
            # 设置文件权限（仅所有者可读写）
            os.chmod(self.api_keys_file, 0o600)
            
        except Exception as e:
            print(f"保存API密钥失败: {e}")
    
    def set_api_key(self, provider: str, api_key: str):
        """设置API密钥"""
        if not api_key.strip():
            # 如果密钥为空，则删除
            self.remove_api_key(provider)
            return
        
        self._api_keys[provider] = api_key.strip()
        self._save_api_keys()
    
    def get_api_key(self, provider: str) -> str:
        """获取API密钥"""
        return self._api_keys.get(provider, "")
    
    def get_masked_api_key(self, provider: str) -> str:
        """获取掩码显示的API密钥"""
        api_key = self._api_keys.get(provider, "")
        if not api_key:
            return ""
        
        if len(api_key) <= 8:
            return "*" * len(api_key)
        else:
            # 显示前4位和后4位，中间用*代替
            return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    
    def has_api_key(self, provider: str) -> bool:
        """检查是否有API密钥"""
        return provider in self._api_keys and bool(self._api_keys[provider].strip())
    
    def remove_api_key(self, provider: str):
        """移除API密钥"""
        if provider in self._api_keys:
            del self._api_keys[provider]
            self._save_api_keys()
    
    def get_all_providers(self) -> list:
        """获取所有已配置的提供商"""
        return list(self._api_keys.keys())
    
    def clear_all_keys(self):
        """清空所有API密钥"""
        self._api_keys = {}
        self._save_api_keys()
    
    def validate_key_format(self, provider: str, api_key: str) -> bool:
        """验证API密钥格式"""
        if not api_key.strip():
            return False
        
        # 基础格式验证
        key = api_key.strip()
        
        # OpenAI格式验证
        if provider.lower() in ['openai', 'chatgpt']:
            return key.startswith('sk-') and len(key) > 20
        
        # 通义千问格式验证
        elif provider.lower() in ['qianwen', '通义千问']:
            return len(key) > 10  # 基础长度检查
        
        # 文心一言格式验证
        elif provider.lower() in ['wenxin', '文心一言']:
            return len(key) > 10  # 基础长度检查
        
        # 其他提供商的基础验证
        else:
            return len(key) > 5
    
    def export_keys(self, export_path: str, include_keys: bool = False) -> bool:
        """导出密钥配置"""
        try:
            export_data = {}
            for provider in self._api_keys:
                if include_keys:
                    export_data[provider] = self._api_keys[provider]
                else:
                    export_data[provider] = self.get_masked_api_key(provider)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"导出密钥配置失败: {e}")
            return False
