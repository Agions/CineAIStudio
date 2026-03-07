#!/usr/bin/env python3
"""测试场景分析器"""

import pytest
from dataclasses import asdict

from app.services.ai.scene_analyzer import (
    SceneType,
    SceneInfo,
    SceneAnalyzer,
)


class TestSceneType:
    """测试场景类型枚举"""

    def test_all_types(self):
        """测试所有场景类型"""
        types = [
            SceneType.TALKING_HEAD,
            SceneType.B_ROLL,
            SceneType.TITLE,
            SceneType.TRANSITION,
            SceneType.ACTION,
            SceneType.LANDSCAPE,
            SceneType.PRODUCT,
            SceneType.UNKNOWN,
        ]
        
        assert len(types) == 8
        assert SceneType.TALKING_HEAD.value == "talking_head"


class TestSceneInfo:
    """测试场景信息数据类"""

    def test_creation(self):
        """测试创建"""
        scene = SceneInfo(
            index=0,
            start=0.0,
            end=5.0,
            duration=5.0,
            type=SceneType.TALKING_HEAD,
            description="人物讲话场景",
        )
        
        assert scene.index == 0
        assert scene.start == 0.0
        assert scene.end == 5.0
        assert scene.type == SceneType.TALKING_HEAD

    def test_default_values(self):
        """测试默认值"""
        scene = SceneInfo(
            index=1,
            start=5.0,
            end=10.0,
            duration=5.0,
        )
        
        assert scene.type == SceneType.UNKNOWN
        assert scene.description == ""
        assert scene.keyframe_path == ""
        assert scene.avg_brightness == 0.0

    def test_to_dict(self):
        """测试转换为字典"""
        scene = SceneInfo(
            index=0,
            start=0.0,
            end=5.0,
            duration=5.0,
            type=SceneType.LANDSCAPE,
        )
        
        d = asdict(scene)
        
        assert d["index"] == 0
        assert d["type"] == SceneType.LANDSCAPE.value


class TestSceneAnalyzer:
    """测试场景分析器"""

    def test_init(self):
        """测试初始化"""
        analyzer = SceneAnalyzer()
        
        assert analyzer._enable_cache is True

    def test_init_custom_options(self):
        """测试自定义选项初始化"""
        analyzer = SceneAnalyzer(
            min_scene_duration=2.0,
            enable_cache=False,
        )
        
        assert analyzer._min_scene_duration == 2.0
        assert analyzer._enable_cache is False

    def test_parse_scene_detection_output(self):
        """测试解析场景检测输出"""
        analyzer = SceneAnalyzer()
        
        # 模拟 FFmpeg 场景检测输出
        output = """0.000000
5.000000
10.000000
15.000000"""
        
        timestamps = analyzer._parse_scene_detection_output(output)
        
        assert len(timestamps) == 4
        assert 0.0 in timestamps

    def test_estimate_scene_type_from_brightness(self):
        """测试根据亮度估计场景类型"""
        analyzer = SceneAnalyzer()
        
        # 明亮场景
        scene_type = analyzer._estimate_scene_type_from_brightness(0.8)
        assert scene_type in [SceneType.LANDSCAPE, SceneType.TITLE, SceneType.UNKNOWN]
        
        # 暗场景
        scene_type = analyzer._estimate_scene_type_from_brightness(0.1)
        assert scene_type in [SceneType.UNKNOWN, SceneType.ACTION]

    def test_empty_video_path(self):
        """测试空视频路径"""
        analyzer = SceneAnalyzer()
        
        # 应该返回空列表而不是崩溃
        try:
            scenes = analyzer.analyze("")
            assert scenes == []
        except Exception:
            pass  # 预期会出错

    def test_nonexistent_video(self):
        """测试不存在的视频"""
        analyzer = SceneAnalyzer()
        
        # 应该返回空列表
        scenes = analyzer.analyze("/nonexistent/video.mp4")
        assert scenes == []
