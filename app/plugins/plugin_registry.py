#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlow 插件注册表
管理插件的注册、发现和元数据
"""

import os
import json
import time
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict

from .plugin_interface import PluginInfo, PluginType, PluginStatus


@dataclass
class PluginRegistryEntry:
    """插件注册表条目"""
    info: PluginInfo
    plugin_path: str
    entry_point: str
    status: PluginStatus = PluginStatus.UNLOADED
    load_time: float = 0.0
    error_message: Optional[str] = None
    last_used: float = 0.0
    use_count: int = 0
    rating: float = 0.0
    review_count: int = 0
    file_size: int = 0
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginRegistry:
    """插件注册表"""

    def __init__(self, registry_path: str = "plugins/registry.json"):
        self.registry_path = registry_path
        self._plugins: Dict[str, PluginRegistryEntry] = {}
        self._type_index: Dict[PluginType, List[str]] = defaultdict(list)
        self._dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)

        # 确保注册表目录存在
        Path(registry_path).parent.mkdir(parents=True, exist_ok=True)

        # 加载注册表
        self._load_registry()

    def register_plugin(self, entry: PluginRegistryEntry) -> bool:
        """注册插件"""
        try:
            # 验证插件信息
            if not self._validate_plugin_info(entry.info):
                return False

            # 检查依赖
            if not self._check_dependencies(entry.info.dependencies):
                entry.status = PluginStatus.ERROR
                entry.error_message = "Missing dependencies"
                return False

            # 注册插件
            plugin_id = entry.info.id
            self._plugins[plugin_id] = entry

            # 更新索引
            plugin_type = entry.info.plugin_type
            if plugin_id not in self._type_index[plugin_type]:
                self._type_index[plugin_type].append(plugin_id)

            # 更新依赖图
            for dep in entry.info.dependencies:
                self._dependency_graph[plugin_id].add(dep)
                self._reverse_dependency_graph[dep].add(plugin_id)

            # 保存注册表
            self._save_registry()

            return True

        except Exception as e:
            entry.error_message = f"Registration failed: {e}"
            return False

    def unregister_plugin(self, plugin_id: str) -> bool:
        """注销插件"""
        if plugin_id not in self._plugins:
            return False

        entry = self._plugins[plugin_id]

        # 检查是否有其他插件依赖此插件
        if self._reverse_dependency_graph[plugin_id]:
            dependent_plugins = list(self._reverse_dependency_graph[plugin_id])
            entry.error_message = f"Cannot unregister: required by {dependent_plugins}"
            return False

        # 从注册表中移除
        del self._plugins[plugin_id]

        # 更新索引
        plugin_type = entry.info.plugin_type
        if plugin_id in self._type_index[plugin_type]:
            self._type_index[plugin_type].remove(plugin_id)

        # 更新依赖图
        for dep in entry.info.dependencies:
            self._dependency_graph[plugin_id].discard(dep)
            self._reverse_dependency_graph[dep].discard(plugin_id)
        self._dependency_graph.pop(plugin_id, None)
        self._reverse_dependency_graph.pop(plugin_id, None)

        # 保存注册表
        self._save_registry()

        return True

    def get_plugin_info(self, plugin_id: str) -> Optional[PluginRegistryEntry]:
        """获取插件信息"""
        return self._plugins.get(plugin_id)

    def get_all_plugins(self) -> Dict[str, PluginRegistryEntry]:
        """获取所有插件"""
        return self._plugins.copy()

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginRegistryEntry]:
        """按类型获取插件"""
        plugin_ids = self._type_index.get(plugin_type, [])
        return [self._plugins[pid] for pid in plugin_ids if pid in self._plugins]

    def get_plugins_by_status(self, status: PluginStatus) -> List[PluginRegistryEntry]:
        """按状态获取插件"""
        return [entry for entry in self._plugins.values() if entry.status == status]

    def get_active_plugins(self) -> List[PluginRegistryEntry]:
        """获取激活的插件"""
        return self.get_plugins_by_status(PluginStatus.ACTIVE)

    def get_dependencies(self, plugin_id: str) -> Set[str]:
        """获取插件依赖"""
        return self._dependency_graph.get(plugin_id, set()).copy()

    def get_dependents(self, plugin_id: str) -> Set[str]:
        """获取依赖此插件的其他插件"""
        return self._reverse_dependency_graph.get(plugin_id, set()).copy()

    def update_plugin_status(self, plugin_id: str, status: PluginStatus,
                           error_message: Optional[str] = None) -> bool:
        """更新插件状态"""
        if plugin_id not in self._plugins:
            return False

        entry = self._plugins[plugin_id]
        entry.status = status

        if error_message:
            entry.error_message = error_message

        # 更新使用统计
        if status == PluginStatus.ACTIVE:
            entry.last_used = time.time()
            entry.use_count += 1

        # 保存注册表
        self._save_registry()

        return True

    def update_plugin_rating(self, plugin_id: str, rating: float) -> bool:
        """更新插件评分"""
        if plugin_id not in self._plugins:
            return False

        entry = self._plugins[plugin_id]
        # 计算新的平均评分
        total_score = entry.rating * entry.review_count + rating
        entry.review_count += 1
        entry.rating = total_score / entry.review_count

        # 保存注册表
        self._save_registry()

        return True

    def search_plugins(self, query: str, plugin_type: Optional[PluginType] = None) -> List[PluginRegistryEntry]:
        """搜索插件"""
        query = query.lower()
        results = []

        for entry in self._plugins.values():
            # 类型过滤
            if plugin_type and entry.info.plugin_type != plugin_type:
                continue

            # 文本搜索
            searchable_text = f"{entry.info.name} {entry.info.description} {entry.info.author}"
            searchable_text += " ".join(entry.info.tags or [])
            searchable_text = searchable_text.lower()

            if query in searchable_text:
                results.append(entry)

        # 按评分排序
        results.sort(key=lambda x: x.rating, reverse=True)

        return results

    def get_popular_plugins(self, limit: int = 10) -> List[PluginRegistryEntry]:
        """获取热门插件"""
        # 按使用次数和评分排序
        sorted_plugins = sorted(
            self._plugins.values(),
            key=lambda x: (x.use_count, x.rating),
            reverse=True
        )
        return sorted_plugins[:limit]

    def get_recent_plugins(self, limit: int = 10) -> List[PluginRegistryEntry]:
        """获取最近使用的插件"""
        sorted_plugins = sorted(
            self._plugins.values(),
            key=lambda x: x.last_used,
            reverse=True
        )
        return sorted_plugins[:limit]

    def validate_plugin_integrity(self, plugin_id: str) -> bool:
        """验证插件完整性"""
        if plugin_id not in self._plugins:
            return False

        entry = self._plugins[plugin_id]

        # 检查文件是否存在
        if not os.path.exists(entry.plugin_path):
            entry.status = PluginStatus.ERROR
            entry.error_message = "Plugin file not found"
            return False

        # 计算文件校验和
        try:
            current_checksum = self._calculate_checksum(entry.plugin_path)
            if entry.checksum and entry.checksum != current_checksum:
                entry.status = PluginStatus.ERROR
                entry.error_message = "Plugin file corrupted or modified"
                return False
        except Exception:
            return False

        return True

    def scan_plugin_directory(self, plugin_dir: str) -> List[str]:
        """扫描插件目录，发现新插件"""
        discovered_plugins = []

        if not os.path.exists(plugin_dir):
            return discovered_plugins

        for item in os.listdir(plugin_dir):
            plugin_path = os.path.join(plugin_dir, item)

            if os.path.isdir(plugin_path):
                # 检查是否有plugin.json
                manifest_path = os.path.join(plugin_path, "plugin.json")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)

                        # 创建插件信息
                        plugin_info = PluginInfo(
                            id=manifest.get("id", item),
                            name=manifest.get("name", item),
                            version=manifest.get("version", "1.0.0"),
                            description=manifest.get("description", ""),
                            author=manifest.get("author", "Unknown"),
                            email=manifest.get("email"),
                            website=manifest.get("website"),
                            plugin_type=PluginType(manifest.get("type", "utility")),
                            dependencies=manifest.get("dependencies", []),
                            min_app_version=manifest.get("min_app_version", "1.0.0"),
                            max_app_version=manifest.get("max_app_version"),
                            license=manifest.get("license", "MIT"),
                            tags=manifest.get("tags", []),
                            icon_path=manifest.get("icon_path"),
                            config_schema=manifest.get("config_schema")
                        )

                        # 创建注册表条目
                        entry = PluginRegistryEntry(
                            info=plugin_info,
                            plugin_path=plugin_path,
                            entry_point=manifest.get("entry_point", "main.py"),
                            file_size=self._get_directory_size(plugin_path),
                            checksum=self._calculate_checksum(plugin_path)
                        )

                        # 如果插件尚未注册，则添加到发现列表
                        if plugin_info.id not in self._plugins:
                            discovered_plugins.append(entry)

                    except Exception:
                        continue

        return discovered_plugins

    def export_registry(self, export_path: str) -> bool:
        """导出注册表"""
        try:
            export_data = {
                "version": "1.0",
                "export_time": time.time(),
                "plugins": {}
            }

            for plugin_id, entry in self._plugins.items():
                export_data["plugins"][plugin_id] = {
                    "info": entry.info.__dict__,
                    "plugin_path": entry.plugin_path,
                    "entry_point": entry.entry_point,
                    "status": entry.status.value,
                    "use_count": entry.use_count,
                    "rating": entry.rating,
                    "review_count": entry.review_count,
                    "last_used": entry.last_used,
                    "metadata": entry.metadata
                }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception:
            return False

    def import_registry(self, import_path: str, merge: bool = True) -> bool:
        """导入注册表"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if not merge:
                # 清空现有注册表
                self._plugins.clear()
                self._type_index.clear()
                self._dependency_graph.clear()
                self._reverse_dependency_graph.clear()

            for plugin_id, plugin_data in import_data.get("plugins", {}).items():
                # 重建插件信息
                info_dict = plugin_data["info"]
                info = PluginInfo(
                    id=info_dict["id"],
                    name=info_dict["name"],
                    version=info_dict["version"],
                    description=info_dict["description"],
                    author=info_dict["author"],
                    email=info_dict.get("email"),
                    website=info_dict.get("website"),
                    plugin_type=PluginType(info_dict["plugin_type"]),
                    dependencies=info_dict.get("dependencies", []),
                    min_app_version=info_dict.get("min_app_version", "1.0.0"),
                    max_app_version=info_dict.get("max_app_version"),
                    license=info_dict.get("license", "MIT"),
                    tags=info_dict.get("tags", []),
                    icon_path=info_dict.get("icon_path"),
                    config_schema=info_dict.get("config_schema")
                )

                # 创建注册表条目
                entry = PluginRegistryEntry(
                    info=info,
                    plugin_path=plugin_data["plugin_path"],
                    entry_point=plugin_data["entry_point"],
                    status=PluginStatus(plugin_data.get("status", "unloaded")),
                    use_count=plugin_data.get("use_count", 0),
                    rating=plugin_data.get("rating", 0.0),
                    review_count=plugin_data.get("review_count", 0),
                    last_used=plugin_data.get("last_used", 0.0),
                    metadata=plugin_data.get("metadata", {})
                )

                self.register_plugin(entry)

            return True

        except Exception:
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        stats = {
            "total_plugins": len(self._plugins),
            "active_plugins": len(self.get_active_plugins()),
            "error_plugins": len(self.get_plugins_by_status(PluginStatus.ERROR)),
            "plugins_by_type": {},
            "average_rating": 0.0,
            "total_downloads": 0,
            "total_file_size": 0
        }

        # 按类型统计
        for plugin_type in PluginType:
            stats["plugins_by_type"][plugin_type.value] = len(self.get_plugins_by_type(plugin_type))

        # 计算平均评分
        if self._plugins:
            total_rating = sum(entry.rating * entry.review_count for entry in self._plugins.values())
            total_reviews = sum(entry.review_count for entry in self._plugins.values())
            if total_reviews > 0:
                stats["average_rating"] = total_rating / total_reviews

        # 计算总使用次数和文件大小
        stats["total_downloads"] = sum(entry.use_count for entry in self._plugins.values())
        stats["total_file_size"] = sum(entry.file_size for entry in self._plugins.values())

        return stats

    # 私有方法

    def _validate_plugin_info(self, info: PluginInfo) -> bool:
        """验证插件信息"""
        if not info.id or not info.name or not info.version:
            return False

        # 检查ID格式
        if not info.id.replace("-", "").replace("_", "").isalnum():
            return False

        # 检查版本格式
        version_parts = info.version.split(".")
        if len(version_parts) < 2 or not all(part.isdigit() for part in version_parts[:2]):
            return False

        return True

    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查依赖是否满足"""
        for dep in dependencies:
            if dep not in self._plugins:
                return False
        return True

    def _calculate_checksum(self, path: str) -> str:
        """计算文件或目录的校验和"""
        import hashlib

        hash_md5 = hashlib.md5()

        if os.path.isfile(path):
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def _get_directory_size(self, path: str) -> int:
        """获取目录大小"""
        total_size = 0
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except OSError:
                    continue
        return total_size

    def _load_registry(self) -> None:
        """加载注册表"""
        if not os.path.exists(self.registry_path):
            return

        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                registry_data = json.load(f)

            for plugin_id, entry_data in registry_data.get("plugins", {}).items():
                # 重建插件信息
                info_dict = entry_data["info"]
                info = PluginInfo(
                    id=info_dict["id"],
                    name=info_dict["name"],
                    version=info_dict["version"],
                    description=info_dict["description"],
                    author=info_dict["author"],
                    email=info_dict.get("email"),
                    website=info_dict.get("website"),
                    plugin_type=PluginType(info_dict["plugin_type"]),
                    dependencies=info_dict.get("dependencies", []),
                    min_app_version=info_dict.get("min_app_version", "1.0.0"),
                    max_app_version=info_dict.get("max_app_version"),
                    license=info_dict.get("license", "MIT"),
                    tags=info_dict.get("tags", []),
                    icon_path=info_dict.get("icon_path"),
                    config_schema=info_dict.get("config_schema")
                )

                # 创建注册表条目
                entry = PluginRegistryEntry(
                    info=info,
                    plugin_path=entry_data["plugin_path"],
                    entry_point=entry_data["entry_point"],
                    status=PluginStatus(entry_data.get("status", "unloaded")),
                    load_time=entry_data.get("load_time", 0.0),
                    error_message=entry_data.get("error_message"),
                    last_used=entry_data.get("last_used", 0.0),
                    use_count=entry_data.get("use_count", 0),
                    rating=entry_data.get("rating", 0.0),
                    review_count=entry_data.get("review_count", 0),
                    file_size=entry_data.get("file_size", 0),
                    checksum=entry_data.get("checksum"),
                    metadata=entry_data.get("metadata", {})
                )

                self._plugins[plugin_id] = entry

                # 重建索引
                plugin_type = entry.info.plugin_type
                self._type_index[plugin_type].append(plugin_id)

                # 重建依赖图
                for dep in entry.info.dependencies:
                    self._dependency_graph[plugin_id].add(dep)
                    self._reverse_dependency_graph[dep].add(plugin_id)

        except Exception:
            # 如果加载失败，创建空注册表
            self._plugins.clear()
            self._type_index.clear()
            self._dependency_graph.clear()
            self._reverse_dependency_graph.clear()

    def _save_registry(self) -> None:
        """保存注册表"""
        try:
            registry_data = {
                "version": "1.0",
                "last_updated": time.time(),
                "plugins": {}
            }

            for plugin_id, entry in self._plugins.items():
                registry_data["plugins"][plugin_id] = {
                    "info": entry.info.__dict__,
                    "plugin_path": entry.plugin_path,
                    "entry_point": entry.entry_point,
                    "status": entry.status.value,
                    "load_time": entry.load_time,
                    "error_message": entry.error_message,
                    "last_used": entry.last_used,
                    "use_count": entry.use_count,
                    "rating": entry.rating,
                    "review_count": entry.review_count,
                    "file_size": entry.file_size,
                    "checksum": entry.checksum,
                    "metadata": entry.metadata
                }

            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)

        except Exception:
            pass