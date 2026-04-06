"""
视频缩略图缓存服务
提供视频缩略图预加载和缓存功能，优化大视频加载速度
"""

import os
import asyncio
import json
import hashlib
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import ffmpeg

logger = logging.getLogger(__name__)


@dataclass
class ThumbnailInfo:
    """缩略图信息"""
    video_path: str
    thumbnail_path: str
    timestamp: float  # 截图时间点（秒）
    width: int
    height: int
    size: int  # 文件大小
    mtime: float  # 文件修改时间，用于 LRU 排序


class VideoThumbnailCache:
    """视频缩略图缓存管理器"""

    # 缓存索引文件名
    INDEX_FILE = "thumbnail_index.json"

    def __init__(self, cache_dir: str = None, max_cache_size: int = 500 * 1024 * 1024):
        """
        初始化缩略图缓存

        Args:
            cache_dir: 缓存目录，默认 ~/.cache/narrafiilm/thumbnails
            max_cache_size: 最大缓存大小，默认 500MB
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.cache/narrafiilm/thumbnails")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size

        # 内存缓存
        self._memory_cache: Dict[str, ThumbnailInfo] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)

        # 加载已有缓存索引
        self._load_cache_index()

    def _get_video_hash(self, video_path: str) -> str:
        """获取视频文件哈希"""
        stat = os.stat(video_path)
        key = f"{video_path}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cache_path(self, video_hash: str, timestamp: float) -> str:
        """获取缩略图缓存路径"""
        filename = f"{video_hash}_{int(timestamp * 1000)}.jpg"
        return str(self.cache_dir / filename)

    def _get_index_path(self) -> str:
        """获取缓存索引文件路径"""
        return str(self.cache_dir / self.INDEX_FILE)

    def _load_cache_index(self) -> None:
        """从 JSON 索引文件加载缓存，fallback 到磁盘扫描"""
        index_path = self._get_index_path()

        # 优先从索引文件加载
        if os.path.exists(index_path):
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                for key, info_dict in raw.items():
                    # 验证文件仍然存在
                    if os.path.exists(info_dict["thumbnail_path"]):
                        self._memory_cache[key] = ThumbnailInfo(**info_dict)
                logger.info(f"从索引加载了 {len(self._memory_cache)} 个缩略图缓存")
                return
            except Exception as e:
                logger.warning(f"加载缓存索引失败: {e}，回退到磁盘扫描")

        # Fallback：扫描磁盘（老版本兼容）
        for file in self.cache_dir.glob("*.jpg"):
            try:
                stat = file.stat()
                self._memory_cache[file.stem] = ThumbnailInfo(
                    video_path="",
                    thumbnail_path=str(file),
                    timestamp=0,
                    width=0,
                    height=0,
                    size=stat.st_size,
                    mtime=stat.st_mtime,
                )
            except Exception:
                pass
        logger.info(f"磁盘扫描加载了 {len(self._memory_cache)} 个缩略图缓存")

    def _save_cache_index(self) -> None:
        """将内存缓存持久化到 JSON 索引文件"""
        index_path = self._get_index_path()
        try:
            serializable = {
                key: asdict(info) for key, info in self._memory_cache.items()
            }
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"保存缓存索引失败: {e}")

    def _check_cache_size(self) -> None:
        """检查并清理缓存（基于 LRU：按 mtime 从旧到新）"""
        total_size = sum(info.size for info in self._memory_cache.values())

        if total_size > self.max_cache_size:
            # 按 mtime 升序排列（最旧的在前）→ 正确实现 LRU
            sorted_cache = sorted(
                self._memory_cache.items(),
                key=lambda x: x[1].mtime
            )

            # 删除 20% 的最旧缓存
            delete_count = max(1, len(sorted_cache) // 5)
            deleted = 0
            for key, info in sorted_cache[:delete_count]:
                try:
                    if os.path.exists(info.thumbnail_path):
                        os.remove(info.thumbnail_path)
                    del self._memory_cache[key]
                    deleted += 1
                except Exception:
                    pass

            logger.info(f"清理了 {deleted} 个旧缩略图缓存（LRU）")
            self._save_cache_index()

    def generate_thumbnail(
        self,
        video_path: str,
        timestamp: float = 1.0,
        width: int = 320,
        height: int = 180
    ) -> Optional[str]:
        """
        生成视频缩略图（同步，调用方负责在线程池执行）

        Args:
            video_path: 视频路径
            timestamp: 截图时间点（秒）
            width: 缩略图宽度
            height: 缩略图高度

        Returns:
            缩略图路径，失败返回 None
        """
        try:
            video_hash = self._get_video_hash(video_path)
            cache_path = self._get_cache_path(video_hash, timestamp)

            # 检查缓存是否存在
            if os.path.exists(cache_path):
                # 更新 mtime 以标记最近使用
                os.utime(cache_path, None)
                return cache_path

            # 生成缩略图
            (
                ffmpeg
                .input(video_path, ss=timestamp)
                .filter('scale', width, height)
                .output(cache_path, vwarning=0, **{'q:v': 2})
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )

            # 更新缓存
            if os.path.exists(cache_path):
                stat = os.stat(cache_path)
                self._memory_cache[os.path.basename(cache_path).replace(".jpg", "")] = ThumbnailInfo(
                    video_path=video_path,
                    thumbnail_path=cache_path,
                    timestamp=timestamp,
                    width=width,
                    height=height,
                    size=stat.st_size,
                    mtime=stat.st_mtime,
                )

                # 检查缓存大小（按需清理）
                self._check_cache_size()
                # 每生成 10 个缩略图才写一次索引，避免 IO 过于频繁
                if len(self._memory_cache) % 10 == 0:
                    self._save_cache_index()

                return cache_path

        except Exception as e:
            logger.warning(f"生成缩略图失败: {video_path}, {e}")

        return None

    async def generate_thumbnail_async(
        self,
        video_path: str,
        timestamp: float = 1.0,
        width: int = 320,
        height: int = 180
    ) -> Optional[str]:
        """
        异步生成视频缩略图（在线程池中执行，await 等待结果）

        Returns:
            缩略图路径，失败返回 None
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self.generate_thumbnail(video_path, timestamp, width, height)
        )

    def preload_thumbnails(
        self,
        video_path: str,
        count: int = 10,
        interval: float = None
    ) -> List[str]:
        """
        预加载多个缩略图

        Args:
            video_path: 视频路径
            count: 预加载数量
            interval: 间隔秒数，默认自动计算

        Returns:
            缩略图路径列表
        """
        # 获取视频时长
        try:
            probe = ffmpeg.probe(video_path)
            duration = float(probe['format']['duration'])
        except Exception:
            return []

        # 计算间隔
        if interval is None:
            interval = max(1.0, duration / (count + 1))

        # 生成时间点
        timestamps = [interval * (i + 1) for i in range(count)]

        # 并行生成（使用同步方法，直接提交到线程池）
        futures = [
            self._executor.submit(self.generate_thumbnail, video_path, ts)
            for ts in timestamps
        ]

        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception:
                pass

        return results

    def get_thumbnail(self, video_path: str, timestamp: float = 1.0) -> Optional[str]:
        """
        获取视频缩略图（优先使用缓存）

        Args:
            video_path: 视频路径
            timestamp: 截图时间点

        Returns:
            缩略图路径（缓存命中时），未命中时触发异步生成并返回 None
        """
        video_hash = self._get_video_hash(video_path)
        cache_path = self._get_cache_path(video_hash, timestamp)

        if os.path.exists(cache_path):
            # 更新 mtime 标记访问
            try:
                os.utime(cache_path, None)
            except Exception:
                pass
            return cache_path

        # 异步生成（fire-and-forget）
        self._executor.submit(self.generate_thumbnail, video_path, timestamp)
        return None

    def clear_cache(self) -> int:
        """
        清理所有缓存

        Returns:
            清理的文件数量
        """
        count = len(self._memory_cache)

        for info in self._memory_cache.values():
            try:
                if os.path.exists(info.thumbnail_path):
                    os.remove(info.thumbnail_path)
            except Exception:
                pass

        self._memory_cache.clear()

        # 删除索引文件
        try:
            index_path = self._get_index_path()
            if os.path.exists(index_path):
                os.remove(index_path)
        except Exception:
            pass

        logger.info(f"清理了 {count} 个缩略图缓存")
        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_size = sum(info.size for info in self._memory_cache.values())

        return {
            "count": len(self._memory_cache),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_size_mb": self.max_cache_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir)
        }

    def shutdown(self) -> None:
        """关闭线程池（应用退出时调用）"""
        self._save_cache_index()
        self._executor.shutdown(wait=True)


# 全局实例
_thumbnail_cache: Optional[VideoThumbnailCache] = None


def get_thumbnail_cache() -> VideoThumbnailCache:
    """获取全局缩略图缓存实例"""
    global _thumbnail_cache
    if _thumbnail_cache is None:
        _thumbnail_cache = VideoThumbnailCache()
    return _thumbnail_cache
