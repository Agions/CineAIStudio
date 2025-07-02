#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import subprocess
import platform
import os
from typing import List, Dict, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal


class OllamaManager(QObject):
    """Ollama本地模型管理器"""
    
    # 信号
    service_status_changed = pyqtSignal(bool)  # 服务状态变化
    model_list_updated = pyqtSignal(list)      # 模型列表更新
    model_pulled = pyqtSignal(str, bool)       # 模型拉取完成(模型名, 是否成功)
    model_deleted = pyqtSignal(str, bool)      # 模型删除完成(模型名, 是否成功)
    
    def __init__(self, api_url: str = "http://localhost:11434"):
        super().__init__()
        
        self.api_url = api_url
        self.session = None
        self.is_service_running = False
        self.available_models = []
        
        # 推荐的模型列表
        self.recommended_models = [
            {
                "name": "llama2",
                "display_name": "Llama 2 (7B)",
                "description": "Meta的开源大语言模型，适合通用对话",
                "size": "3.8GB"
            },
            {
                "name": "llama2:13b",
                "display_name": "Llama 2 (13B)",
                "description": "更大的Llama 2模型，性能更强",
                "size": "7.3GB"
            },
            {
                "name": "codellama",
                "display_name": "Code Llama",
                "description": "专门用于代码生成的模型",
                "size": "3.8GB"
            },
            {
                "name": "mistral",
                "display_name": "Mistral 7B",
                "description": "高效的开源模型，速度快",
                "size": "4.1GB"
            },
            {
                "name": "qwen:7b",
                "display_name": "通义千问 7B",
                "description": "阿里巴巴的中文大模型",
                "size": "4.0GB"
            },
            {
                "name": "chatglm3",
                "display_name": "ChatGLM3",
                "description": "清华大学的中文对话模型",
                "size": "4.2GB"
            }
        ]
    
    async def initialize(self):
        """初始化Ollama管理器"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # 检查服务状态
        await self.check_service_status()
        
        # 如果服务运行，获取模型列表
        if self.is_service_running:
            await self.refresh_model_list()
    
    async def check_service_status(self) -> bool:
        """检查Ollama服务状态"""
        try:
            if not self.session:
                return False
            
            url = f"{self.api_url}/api/tags"
            async with self.session.get(url) as response:
                self.is_service_running = response.status == 200
                self.service_status_changed.emit(self.is_service_running)
                return self.is_service_running
                
        except Exception:
            self.is_service_running = False
            self.service_status_changed.emit(False)
            return False
    
    async def refresh_model_list(self) -> List[str]:
        """刷新模型列表"""
        try:
            if not self.is_service_running:
                return []
            
            url = f"{self.api_url}/api/tags"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_models = [model['name'] for model in data.get('models', [])]
                    self.model_list_updated.emit(self.available_models)
                    return self.available_models
                else:
                    return []
                    
        except Exception as e:
            print(f"获取Ollama模型列表失败: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """拉取模型"""
        try:
            if not self.is_service_running:
                return False
            
            data = {"name": model_name}
            url = f"{self.api_url}/api/pull"
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    # 刷新模型列表
                    await self.refresh_model_list()
                    self.model_pulled.emit(model_name, True)
                    return True
                else:
                    self.model_pulled.emit(model_name, False)
                    return False
                    
        except Exception as e:
            print(f"拉取模型失败: {e}")
            self.model_pulled.emit(model_name, False)
            return False
    
    async def delete_model(self, model_name: str) -> bool:
        """删除模型"""
        try:
            if not self.is_service_running:
                return False
            
            data = {"name": model_name}
            url = f"{self.api_url}/api/delete"
            
            async with self.session.delete(url, json=data) as response:
                if response.status == 200:
                    # 刷新模型列表
                    await self.refresh_model_list()
                    self.model_deleted.emit(model_name, True)
                    return True
                else:
                    self.model_deleted.emit(model_name, False)
                    return False
                    
        except Exception as e:
            print(f"删除模型失败: {e}")
            self.model_deleted.emit(model_name, False)
            return False
    
    def get_recommended_models(self) -> List[Dict[str, str]]:
        """获取推荐模型列表"""
        return self.recommended_models
    
    def get_available_models(self) -> List[str]:
        """获取已安装的模型列表"""
        return self.available_models
    
    def is_model_installed(self, model_name: str) -> bool:
        """检查模型是否已安装"""
        return model_name in self.available_models
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, str]]:
        """获取模型信息"""
        for model in self.recommended_models:
            if model["name"] == model_name:
                return model
        return None
    
    def start_ollama_service(self) -> bool:
        """启动Ollama服务"""
        try:
            system = platform.system().lower()
            
            if system == "windows":
                # Windows系统
                subprocess.Popen(["ollama", "serve"], shell=True)
            elif system == "darwin":
                # macOS系统
                subprocess.Popen(["ollama", "serve"])
            elif system == "linux":
                # Linux系统
                subprocess.Popen(["ollama", "serve"])
            else:
                return False
            
            return True
            
        except Exception as e:
            print(f"启动Ollama服务失败: {e}")
            return False
    
    def is_ollama_installed(self) -> bool:
        """检查Ollama是否已安装"""
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_installation_instructions(self) -> Dict[str, str]:
        """获取安装说明"""
        system = platform.system().lower()
        
        instructions = {
            "windows": {
                "title": "Windows安装说明",
                "steps": [
                    "1. 访问 https://ollama.ai/download",
                    "2. 下载Windows版本的安装包",
                    "3. 运行安装程序并按照提示完成安装",
                    "4. 重启应用程序"
                ]
            },
            "darwin": {
                "title": "macOS安装说明",
                "steps": [
                    "1. 访问 https://ollama.ai/download",
                    "2. 下载macOS版本的安装包",
                    "3. 拖拽到Applications文件夹",
                    "4. 或使用Homebrew: brew install ollama"
                ]
            },
            "linux": {
                "title": "Linux安装说明",
                "steps": [
                    "1. 运行安装脚本:",
                    "   curl -fsSL https://ollama.ai/install.sh | sh",
                    "2. 或从 https://ollama.ai/download 下载对应版本",
                    "3. 启动服务: ollama serve"
                ]
            }
        }
        
        return instructions.get(system, instructions["linux"])
    
    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def __del__(self):
        """析构函数"""
        if self.session and not self.session.closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    loop.run_until_complete(self.close())
            except:
                pass
