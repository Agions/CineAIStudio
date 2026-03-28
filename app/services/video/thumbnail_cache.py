"""
视频缩略图缓存服务
提供视频缩略图预加载和缓存功能，优化大视频加载速度
"""

import os
import hashlib
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
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


class VideoThumbnailCache:
    """视频缩略图缓存管理器"""

    def __init__(self, cache_dir: str = None, max_cache_size: int = 500 * 1024 * 1024):
        """
        初始化缩略图缓存
        
        Args:
            cache_dir: 缓存目录，默认 ~/.cache/videoforge/thumbnails
            max_cache_size: 最大缓存大小，默认 500MB
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.cache/videoforge/thumbnails")
        
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
        # 使用文件路径 + 修改时间 + 文件大小
        stat = os.stat(video_path)
        key = f"{video_path}_{stat.st_mtime}_{stat.st_size}"
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cache_path(self, video_hash: str, timestamp: float) -> str:
        """获取缩略图缓存路径"""
        filename = f"{video_hash}_{int(timestamp * 1000)}.jpg"
        return str(self.cache_dir / filename)

    def _load_cache_index(self) -> None:
        """加载缓存索引"""
        try:
            for file in self.cache_dir.glob("*.jpg"):
                # 从文件名解析视频信息
                parts = file.stem.split("_")
                if len(parts) >= 2:
                    # 简化处理：只记录文件
                    self._memory_cache[file.stem] = ThumbnailInfo(
                        video_path="",
                        thumbnail_path=str(file),
                        timestamp=0,
                        width=0,
                        height=0,
                        size=file.stat().st_size
                    )
            logger.info(f"加载了 {len(self._memory_cache)} 个缩略图缓存")
        except Exception as e:
            logger.warning(f"加载缓存索引失败: {e}")

    def _check_cache_size(self) -> None:
        """检查并清理缓存"""
        total_size = sum(info.size for info in self._memory_cache.values())
        
        if total_size > self.max_cache_size:
            # 删除最旧的缓存
            sorted_cache = sorted(
                self._memory_cache.items(),
                key=lambda x: x[1].thumbnail_path
            )
            
            # 删除 20% 的最旧缓存
            delete_count = len(sorted_cache) // 5
            for key, info in sorted_cache[:delete_count]:
                try:
                    os.remove(info.thumbnail_path)
                    del self._memory_cache[key]
                except Exception:
                    logger.debug(f"Operation failed")
                    
            logger.info(f"清理了 {delete_count} 个旧缩略图缓存")

    async def generate_thumbnail(
        self, 
        video_path: str, 
        timestamp: float = 1.0,
        width: int = 320,
        height: int = 180
    ) -> Optional[str]:
        """
        生成视频缩略图
        
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
                self._memory_cache[os.path.basename(cache_path).replace(".jpg", "")] = ThumbnailInfo(
                    video_path=video_path,
                    thumbnail_path=cache_path,
                    timestamp=timestamp,
                    width=width,
                    height=height,
                    size=os.path.getsize(cache_path)
                )
                
                # 检查缓存大小
                self._check_cache_size()
                
                return cache_path
                
        except Exception as e:
            logger.warning(f"生成缩略图失败: {video_path}, {e}")
            
        return None

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
        
        # 并行生成
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
                logger.debug(f"Operation failed")
                
        return results

    def get_thumbnail(self, video_path: str, timestamp: float = 1.0) -> Optional[str]:
        """
        获取视频缩略图（优先使用缓存）
        
        Args:
            video_path: 视频路径
            timestamp: 截图时间点
            
        Returns:
            缩略图路径
        """
        video_hash = self._get_video_hash(video_path)
        cache_path = self._get_cache_path(video_hash, timestamp)
        
        if os.path.exists(cache_path):
            return cache_path
        
        # 异步生成
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
                logger.debug(f"Operation failed")
        
        self._memory_cache.clear()
        
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


# 全局实例
_thumbnail_cache: Optional[VideoThumbnailCache] = None


def get_thumbnail_cache() -> VideoThumbnailCache:
    """获取全局缩略图缓存实例"""
    global _thumbnail_cache
    if _thumbnail_cache is None:
        _thumbnail_cache = VideoThumbnailCache()
    return _thumbnail_cache
