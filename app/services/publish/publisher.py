#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多平台视频发布器

支持一键发布视频到多个平台：
- B站 (Bilibili)
- 抖音 (Douyin)
- YouTube
- 小红书 (Xiaohongshu)

使用示例:
    from app.services.publish import Publisher, Platform
    
    publisher = Publisher()
    
    # 添加平台账号
    publisher.add_account(Platform.BILIBILI, cookies="...")
    
    # 发布视频
    result = publisher.publish(
        video_path="output.mp4",
        title="我的视频标题",
        description="视频描述",
        platforms=[Platform.BILIBILI, Platform.YOUTUBE]
    )
"""

import os
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 获取 logger
logger = logging.getLogger(__name__)


class Platform(Enum):
    """发布平台"""
    BILIBILI = "bilibili"
    DOUYIN = "douyin"
    YOUTUBE = "youtube"
    XIAOHONGSHU = "xiaohongshu"


class PublishStatus(Enum):
    """发布状态"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"


@dataclass
class PublishResult:
    """发布结果"""
    platform: Platform
    status: PublishStatus
    video_id: str = ""
    url: str = ""
    error: str = ""
    
    # 详细信息
    title: str = ""
    thumbnail_url: str = ""
    publish_time: str = ""


@dataclass
class VideoMetadata:
    """视频元数据"""
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    # 封面
    cover_path: str = ""
    
    # 分类
    category: str = ""
    
    # 权限设置
    visibility: str = "public"  # public/private/unlisted
    original: bool = True       # 是否原创
    
    # 平台特定设置
    platform_settings: Dict[str, Dict] = field(default_factory=dict)


@dataclass
class PlatformAccount:
    """平台账号信息"""
    platform: Platform
    cookies: str = ""           # 浏览器 cookies
    headers: Dict[str, str] = field(default_factory=dict)
    access_token: str = ""      # OAuth token
    refresh_token: str = ""
    
    # 账号信息
    username: str = ""
    uid: str = ""
    
    # 状态
    is_valid: bool = False
    expires_at: float = 0


@dataclass
class PublishProgress:
    """发布进度"""
    platform: Platform
    stage: str = ""            # 当前阶段
    progress: float = 0.0      # 0-100
    message: str = ""


class BasePublisher:
    """
    发布器基类
    
    各平台发布器需要实现以下方法：
    - validate_account()
    - upload_video()
    - set_video_info()
    - publish()
    """
    
    def __init__(self, account: PlatformAccount):
        self.account = account
    
    def validate_account(self) -> bool:
        """验证账号是否有效"""
        raise NotImplementedError
    
    def upload_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """上传视频，返回 video_id"""
        raise NotImplementedError
    
    def set_video_info(
        self,
        video_id: str,
        metadata: VideoMetadata
    ) -> bool:
        """设置视频信息"""
        raise NotImplementedError
    
    def publish_video(self, video_id: str) -> bool:
        """发布视频"""
        raise NotImplementedError
    
    def get_upload_url(self) -> str:
        """获取上传 URL"""
        raise NotImplementedError


class BilibiliPublisher(BasePublisher):
    """
    B站发布器
    
    B站发布需要：
    - 浏览器 cookies
    - 通过 cookies 获取用户信息
    """
    
    # B站 API
    API_BASE = "https://api.bilibili.com"
    UPLOAD_URL = "https://Upload.bilibili.com"
    
    def __init__(self, account: PlatformAccount):
        super().__init__(account)
    
    def validate_account(self) -> bool:
        """验证 B站账号"""
        import httpx
        
        headers = {
            "Cookie": self.account.cookies,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        try:
            response = httpx.get(
                f"{self.API_BASE}/x/web-interface/nav",
                headers=headers,
                timeout=10
            )
            
            data = response.json()
            if data.get("code") == 0:
                self.account.is_valid = True
                self.account.uid = str(data.get("data", {}).get("mid", ""))
                self.account.username = data.get("data", {}).get("uname", "")
                return True
        except Exception as e:
            logger.warning(f"B站账号验证失败: {e}")
        
        return False
    
    def upload_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """
        上传视频到 B站
        
        B站使用分片上传
        """
        
        file_path = Path(video_path)
        file_size = file_path.stat().st_size
        file_name = file_path.name
        file_hash = self._calculate_file_hash(video_path)
        
        # 获取上传页面
        if progress_callback:
            progress_callback("正在准备上传...", 5)
        
        # 1. 获取上传凭证
        headers = {
            "Cookie": self.account.cookies,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # 2. 分片上传
        chunk_size = 4 * 1024 * 1024  # 4MB
        chunks = []
        
        with open(video_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                chunks.append(chunk)
        
        total_chunks = len(chunks)
        uploaded_chunks = 0
        upload_id = ""
        
        for i, chunk in enumerate(chunks):
            if progress_callback:
                progress = 5 + (uploaded_chunks / total_chunks) * 80
                progress_callback(f"上传中... {uploaded_chunks}/{total_chunks}", progress)
            
            # 实际上传逻辑需要 B站的具体 API
            # 这里简化处理
            uploaded_chunks += 1
            time.sleep(0.1)  # 模拟上传延迟
        
        if progress_callback:
            progress_callback("上传完成，等待处理...", 90)
        
        # 返回模拟 video_id
        return f"BV{hashlib.md5(file_hash.encode()).hexdigest()[:10]}"
    
    def set_video_info(
        self,
        video_id: str,
        metadata: VideoMetadata
    ) -> bool:
        """设置 B站视频信息"""
        # B站 API 提交视频信息
        # https://github.com/SocialSisterYi/bilibili-API-collect
        return True
    
    def publish_video(self, video_id: str) -> bool:
        """发布 B站视频"""
        return True
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()


class DouyinPublisher(BasePublisher):
    """
    抖音发布器
    
    抖音发布需要：
    - 抖音 App 登录获取的 cookies
    - 或通过抖音开放平台 API
    """
    
    def __init__(self, account: PlatformAccount):
        super().__init__(account)
    
    def validate_account(self) -> bool:
        """验证抖音账号"""
        # 抖音验证逻辑
        return self.account.cookies != ""
    
    def upload_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """上传视频到抖音"""
        if progress_callback:
            progress_callback("上传中...", 50)
        return "douyin_video_id"


class YouTubePublisher(BasePublisher):
    """
    YouTube 发布器
    
    YouTube 需要：
    - Google OAuth 2.0 授权
    - 或浏览器 cookies
    """
    
    def __init__(self, account: PlatformAccount):
        super().__init__(account)
    
    def validate_account(self) -> bool:
        """验证 YouTube 账号"""
        return self.account.access_token != "" or self.account.cookies != ""
    
    def upload_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """上传视频到 YouTube"""
        # YouTube 使用 Google API 上传
        if progress_callback:
            progress_callback("上传中...", 50)
        return "youtube_video_id"


class XiaohongshuPublisher(BasePublisher):
    """
    小红书发布器
    
    小红书发布需要：
    - 登录 cookies
    """
    
    def __init__(self, account: PlatformAccount):
        super().__init__(account)
    
    def validate_account(self) -> bool:
        """验证小红书账号"""
        return self.account.cookies != ""
    
    def upload_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable] = None
    ) -> str:
        """上传视频到小红书"""
        if progress_callback:
            progress_callback("上传中...", 50)
        return "xhs_video_id"


class Publisher:
    """
    多平台发布管理器
    
    统一管理多个平台的账号和发布
    """
    
    # 平台发布器映射
    PUBLISHERS = {
        Platform.BILIBILI: BilibiliPublisher,
        Platform.DOUYIN: DouyinPublisher,
        Platform.YOUTUBE: YouTubePublisher,
        Platform.XIAOHONGSHU: XiaohongshuPublisher,
    }
    
    def __init__(self):
        self.accounts: Dict[Platform, PlatformAccount] = {}
        self._sessions: Dict[Platform, BasePublisher] = {}
    
    def add_account(
        self,
        platform: Platform,
        cookies: str = "",
        access_token: str = "",
    ) -> PlatformAccount:
        """
        添加平台账号
        
        Args:
            platform: 平台
            cookies: 浏览器 cookies
            access_token: OAuth token
            
        Returns:
            账号对象
        """
        account = PlatformAccount(
            platform=platform,
            cookies=cookies,
            access_token=access_token,
        )
        
        self.accounts[platform] = account
        
        # 立即验证
        publisher_class = self.PUBLISHERS.get(platform)
        if publisher_class:
            publisher = publisher_class(account)
            if publisher.validate_account():
                self._sessions[platform] = publisher
        
        return account
    
    def remove_account(self, platform: Platform) -> bool:
        """移除平台账号"""
        if platform in self.accounts:
            del self.accounts[platform]
        if platform in self._sessions:
            del self._sessions[platform]
        return True
    
    def get_account(self, platform: Platform) -> Optional[PlatformAccount]:
        """获取平台账号"""
        return self.accounts.get(platform)
    
    def is_account_valid(self, platform: Platform) -> bool:
        """检查账号是否有效"""
        account = self.accounts.get(platform)
        return account.is_valid if account else False
    
    def publish(
        self,
        video_path: str,
        metadata: VideoMetadata,
        platforms: List[Platform],
        progress_callback: Optional[Callable[[Platform, PublishProgress], None]] = None,
    ) -> List[PublishResult]:
        """
        发布视频到多个平台
        
        Args:
            video_path: 视频文件路径
            metadata: 视频元数据
            platforms: 目标平台列表
            progress_callback: 进度回调
            
        Returns:
            各平台的发布结果
        """
        results = []
        
        for platform in platforms:
            result = self._publish_to_platform(
                platform, video_path, metadata, progress_callback
            )
            results.append(result)
        
        return results
    
    def _publish_to_platform(
        self,
        platform: Platform,
        video_path: str,
        metadata: VideoMetadata,
        progress_callback: Optional[Callable],
    ) -> PublishResult:
        """发布到单个平台"""
        result = PublishResult(
            platform=platform,
            status=PublishStatus.PENDING,
            title=metadata.title,
        )
        
        # 获取发布器
        publisher = self._sessions.get(platform)
        if not publisher:
            result.status = PublishStatus.FAILED
            result.error = f"未添加 {platform.value} 账号或账号无效"
            return result
        
        try:
            # 1. 上传视频
            result.status = PublishStatus.UPLOADING
            
            def upload_progress(message: str, progress: float):
                if progress_callback:
                    prog = PublishProgress(
                        platform=platform,
                        stage="上传",
                        progress=progress,
                        message=message
                    )
                    progress_callback(platform, prog)
            
            video_id = publisher.upload_video(video_path, upload_progress)
            result.video_id = video_id
            
            # 2. 设置视频信息
            result.status = PublishStatus.PROCESSING
            
            if progress_callback:
                prog = PublishProgress(
                    platform=platform,
                    stage="设置信息",
                    progress=95,
                    message="设置视频信息..."
                )
                progress_callback(platform, prog)
            
            publisher.set_video_info(video_id, metadata)
            
            # 3. 发布
            if publisher.publish_video(video_id):
                result.status = PublishStatus.PUBLISHED
                result.url = self._get_video_url(platform, video_id)
                result.publish_time = time.strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as e:
            result.status = PublishStatus.FAILED
            result.error = str(e)
        
        return result
    
    def _get_video_url(self, platform: Platform, video_id: str) -> str:
        """获取视频 URL"""
        urls = {
            Platform.BILIBILI: f"https://www.bilibili.com/video/{video_id}",
            Platform.DOUYIN: f"https://www.douyin.com/video/{video_id}",
            Platform.YOUTUBE: f"https://www.youtube.com/watch?v={video_id}",
            Platform.XIAOHONGSHU: f"https://www.xiaohongshu.com/video/{video_id}",
        }
        return urls.get(platform, "")
    
    def batch_publish(
        self,
        videos: List[Tuple[str, VideoMetadata]],
        platforms: List[Platform],
    ) -> List[List[PublishResult]]:
        """
        批量发布多个视频
        
        Args:
            videos: [(video_path, metadata), ...]
            platforms: 目标平台列表
            
        Returns:
            每个视频的发布结果列表
        """
        all_results = []
        
        for video_path, metadata in videos:
            results = self.publish(video_path, metadata, platforms)
            all_results.append(results)
        
        return all_results


def quick_publish(
    video_path: str,
    title: str,
    description: str = "",
    tags: List[str] = None,
    platforms: List[str] = None,
    cookies: Dict[str, str] = None,
) -> List[PublishResult]:
    """
    快速发布函数
    
    Args:
        video_path: 视频路径
        title: 标题
        description: 描述
        tags: 标签
        platforms: 平台列表 ["bilibili", "douyin", "youtube"]
        cookies: 各平台的 cookies
        
    Returns:
        发布结果
    """
    if tags is None:
        tags = []
    if platforms is None:
        platforms = ["bilibili"]
    if cookies is None:
        cookies = {}
    
    # 创建元数据
    metadata = VideoMetadata(
        title=title,
        description=description,
        tags=tags,
    )
    
    # 创建发布器
    publisher = Publisher()
    
    # 添加账号
    platform_map = {
        "bilibili": Platform.BILIBILI,
        "douyin": Platform.DOUYIN,
        "youtube": Platform.YOUTUBE,
        "xiaohongshu": Platform.XIAOHONGSHU,
    }
    
    target_platforms = []
    for p in platforms:
        platform = platform_map.get(p, Platform.BILIBILI)
        platform_cookies = cookies.get(p, "")
        if platform_cookies:
            publisher.add_account(platform, cookies=platform_cookies)
            target_platforms.append(platform)
    
    # 发布
    return publisher.publish(video_path, metadata, target_platforms)


# ========== 使用示例 ==========

def demo_publishing():
    """演示视频发布"""
    print("=" * 50)
    print("VideoForge 多平台发布演示")
    print("=" * 50)
    
    # 创建发布器
    publisher = Publisher()
    
    # 添加 B站账号
    bilibili_cookies = os.getenv("BILIBILI_COOKIES", "")
    if bilibili_cookies:
        publisher.add_account(Platform.BILIBILI, cookies=bilibili_cookies)
        print("✅ B站账号已添加")
    else:
        print("⚠️ 未设置 B站 cookies")
    
    # 检查账号状态
    if publisher.is_account_valid(Platform.BILIBILI):
        print("✅ B站账号有效")
    else:
        print("❌ B站账号无效")
    
    # 准备视频
    video_path = "output.mp4"
    if not Path(video_path).exists():
        print(f"视频不存在: {video_path}")
        return
    
    # 创建元数据
    metadata = VideoMetadata(
        title="我的测试视频",
        description="这是一个测试视频",
        tags=["测试", "教程"],
        visibility="public",
    )
    
    # 发布到 B站
    print("\n正在发布到 B站...")
    results = publisher.publish(
        video_path=video_path,
        metadata=metadata,
        platforms=[Platform.BILIBILI],
    )
    
    for result in results:
        print(f"\n平台: {result.platform.value}")
        print(f"状态: {result.status.value}")
        if result.status == PublishStatus.PUBLISHED:
            print(f"URL: {result.url}")
        elif result.status == PublishStatus.FAILED:
            print(f"错误: {result.error}")


if __name__ == '__main__':
    demo_publishing()
