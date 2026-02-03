"""
转场效果库 (Transition Effects)

提供丰富的视频转场效果，支持在混剪中使用。

支持效果:
- 淡入淡出 (Fade)
- 溶解 (Dissolve)
- 擦除 (Wipe)
- 缩放 (Zoom)
- 滑动 (Slide)
- 旋转 (Spin)
- 模糊过渡 (Blur)

使用示例:
    from app.services.video import TransitionEffects
    
    effects = TransitionEffects()
    output = effects.apply_transition(
        video1="clip1.mp4",
        video2="clip2.mp4",
        effect="fade",
        duration=0.5,
        output_path="output.mp4"
    )
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class TransitionType(Enum):
    """转场类型"""
    # 基础转场
    CUT = "cut"                    # 硬切（无转场）
    FADE = "fade"                  # 淡入淡出
    FADE_BLACK = "fade_black"      # 黑场淡入淡出
    FADE_WHITE = "fade_white"      # 白场淡入淡出
    
    # 溶解类
    DISSOLVE = "dissolve"          # 交叉溶解
    
    # 擦除类
    WIPE_LEFT = "wipe_left"        # 向左擦除
    WIPE_RIGHT = "wipe_right"      # 向右擦除
    WIPE_UP = "wipe_up"            # 向上擦除
    WIPE_DOWN = "wipe_down"        # 向下擦除
    
    # 滑动类
    SLIDE_LEFT = "slide_left"      # 左滑
    SLIDE_RIGHT = "slide_right"    # 右滑
    SLIDE_UP = "slide_up"          # 上滑
    SLIDE_DOWN = "slide_down"      # 下滑
    
    # 缩放类
    ZOOM_IN = "zoom_in"            # 放大进入
    ZOOM_OUT = "zoom_out"          # 缩小退出
    
    # 特效类
    BLUR = "blur"                  # 模糊过渡
    RADIAL = "radial"              # 径向展开
    CIRCLE_OPEN = "circle_open"    # 圆形打开
    CIRCLE_CLOSE = "circle_close"  # 圆形关闭


@dataclass
class TransitionConfig:
    """转场配置"""
    type: TransitionType = TransitionType.FADE
    duration: float = 0.5          # 转场时长（秒）
    easing: str = "easeInOut"      # 缓动函数
    
    # 高级选项
    blur_strength: float = 10.0    # 模糊强度
    zoom_factor: float = 1.5       # 缩放倍数
    direction: str = "left"        # 方向


class TransitionEffects:
    """
    视频转场效果处理器
    
    使用 FFmpeg 实现各种转场效果
    
    使用示例:
        effects = TransitionEffects()
        
        # 应用淡入淡出
        effects.apply_fade("video1.mp4", "video2.mp4", "output.mp4")
        
        # 应用自定义转场
        effects.apply_transition(
            video1="video1.mp4",
            video2="video2.mp4",
            config=TransitionConfig(type=TransitionType.WIPE_LEFT, duration=0.8)
        )
    """
    
    def __init__(self):
        self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> None:
        """检查 FFmpeg 是否可用"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
            if result.returncode != 0:
                raise RuntimeError("FFmpeg 不可用")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg 未安装")
    
    def apply_transition(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: Optional[TransitionConfig] = None,
    ) -> str:
        """
        在两个视频之间应用转场效果
        
        Args:
            video1: 第一个视频路径
            video2: 第二个视频路径
            output_path: 输出路径
            config: 转场配置
            
        Returns:
            输出视频路径
        """
        config = config or TransitionConfig()
        
        # 根据类型选择处理方法
        handlers = {
            TransitionType.CUT: self._apply_cut,
            TransitionType.FADE: self._apply_fade,
            TransitionType.FADE_BLACK: self._apply_fade_black,
            TransitionType.FADE_WHITE: self._apply_fade_white,
            TransitionType.DISSOLVE: self._apply_dissolve,
            TransitionType.WIPE_LEFT: lambda *a: self._apply_wipe(*a, "left"),
            TransitionType.WIPE_RIGHT: lambda *a: self._apply_wipe(*a, "right"),
            TransitionType.WIPE_UP: lambda *a: self._apply_wipe(*a, "up"),
            TransitionType.WIPE_DOWN: lambda *a: self._apply_wipe(*a, "down"),
            TransitionType.SLIDE_LEFT: lambda *a: self._apply_slide(*a, "left"),
            TransitionType.SLIDE_RIGHT: lambda *a: self._apply_slide(*a, "right"),
            TransitionType.ZOOM_IN: self._apply_zoom_in,
            TransitionType.ZOOM_OUT: self._apply_zoom_out,
            TransitionType.BLUR: self._apply_blur,
            TransitionType.CIRCLE_OPEN: self._apply_circle,
        }
        
        handler = handlers.get(config.type, self._apply_fade)
        return handler(video1, video2, output_path, config)
    
    def _get_video_info(self, video_path: str) -> Tuple[float, int, int]:
        """获取视频信息（时长、宽、高）"""
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration:stream=width,height',
            '-of', 'csv=p=0:s=x',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                parts = result.stdout.strip().split('\n')
                # 解析输出
                if len(parts) >= 2:
                    dims = parts[0].split('x') if 'x' in parts[0] else ['1920', '1080']
                    duration = float(parts[-1]) if parts[-1] else 10.0
                    width = int(dims[0]) if dims[0] else 1920
                    height = int(dims[1]) if len(dims) > 1 and dims[1] else 1080
                    return duration, width, height
        except Exception:
            pass
        
        return 10.0, 1920, 1080  # 默认值
    
    def _apply_cut(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: TransitionConfig,
    ) -> str:
        """硬切（直接拼接）"""
        # 创建拼接列表
        list_file = Path(output_path).parent / "concat.txt"
        with open(list_file, 'w') as f:
            f.write(f"file '{video1}'\n")
            f.write(f"file '{video2}'\n")
        
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', str(list_file),
            '-c', 'copy',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        list_file.unlink(missing_ok=True)
        
        return output_path
    
    def _apply_fade(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: TransitionConfig,
    ) -> str:
        """淡入淡出转场"""
        dur1, w, h = self._get_video_info(video1)
        dur2, _, _ = self._get_video_info(video2)
        
        fade_duration = config.duration
        offset = dur1 - fade_duration
        
        # 使用 xfade 滤镜
        cmd = [
            'ffmpeg', '-y',
            '-i', video1,
            '-i', video2,
            '-filter_complex',
            f"[0:v][1:v]xfade=transition=fade:duration={fade_duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={fade_duration}[a]",
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # 降级到简单拼接
            return self._apply_cut(video1, video2, output_path, config)
        
        return output_path
    
    def _apply_fade_black(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: TransitionConfig,
    ) -> str:
        """黑场淡入淡出"""
        dur1, w, h = self._get_video_info(video1)
        
        fade_duration = config.duration
        offset = dur1 - fade_duration
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video1,
            '-i', video2,
            '-filter_complex',
            f"[0:v][1:v]xfade=transition=fadeblack:duration={fade_duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={fade_duration}[a]",
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            return self._apply_fade(video1, video2, output_path, config)
        
        return output_path
    
    def _apply_fade_white(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: TransitionConfig,
    ) -> str:
        """白场淡入淡出"""
        dur1, w, h = self._get_video_info(video1)
        
        fade_duration = config.duration
        offset = dur1 - fade_duration
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video1,
            '-i', video2,
            '-filter_complex',
            f"[0:v][1:v]xfade=transition=fadewhite:duration={fade_duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={fade_duration}[a]",
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            return self._apply_fade(video1, video2, output_path, config)
        
        return output_path
    
    def _apply_dissolve(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: TransitionConfig,
    ) -> str:
        """交叉溶解"""
        dur1, _, _ = self._get_video_info(video1)
        
        fade_duration = config.duration
        offset = dur1 - fade_duration
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video1,
            '-i', video2,
            '-filter_complex',
            f"[0:v][1:v]xfade=transition=dissolve:duration={fade_duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={fade_duration}[a]",
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            return self._apply_fade(video1, video2, output_path, config)
        
        return output_path
    
    def _apply_wipe(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: TransitionConfig,
        direction: str = "left",
    ) -> str:
        """擦除转场"""
        dur1, _, _ = self._get_video_info(video1)
        
        fade_duration = config.duration
        offset = dur1 - fade_duration
        
        # 根据方向选择转场类型
        wipe_map = {
            "left": "wipeleft",
            "right": "wiperight",
            "up": "wipeup",
            "down": "wipedown",
        }
        wipe_type = wipe_map.get(direction, "wipeleft")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video1,
            '-i', video2,
            '-filter_complex',
            f"[0:v][1:v]xfade=transition={wipe_type}:duration={fade_duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={fade_duration}[a]",
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            return self._apply_fade(video1, video2, output_path, config)
        
        return output_path
    
    def _apply_slide(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: TransitionConfig,
        direction: str = "left",
    ) -> str:
        """滑动转场"""
        dur1, _, _ = self._get_video_info(video1)
        
        fade_duration = config.duration
        offset = dur1 - fade_duration
        
        slide_map = {
            "left": "slideleft",
            "right": "slideright",
            "up": "slideup",
            "down": "slidedown",
        }
        slide_type = slide_map.get(direction, "slideleft")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video1,
            '-i', video2,
            '-filter_complex',
            f"[0:v][1:v]xfade=transition={slide_type}:duration={fade_duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={fade_duration}[a]",
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            return self._apply_fade(video1, video2, output_path, config)
        
        return output_path
    
    def _apply_zoom_in(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: TransitionConfig,
    ) -> str:
        """放大进入转场"""
        dur1, _, _ = self._get_video_info(video1)
        
        fade_duration = config.duration
        offset = dur1 - fade_duration
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video1,
            '-i', video2,
            '-filter_complex',
            f"[0:v][1:v]xfade=transition=zoomin:duration={fade_duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={fade_duration}[a]",
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            return self._apply_fade(video1, video2, output_path, config)
        
        return output_path
    
    def _apply_zoom_out(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: TransitionConfig,
    ) -> str:
        """缩小退出转场"""
        dur1, _, _ = self._get_video_info(video1)
        
        fade_duration = config.duration
        offset = dur1 - fade_duration
        
        # FFmpeg 没有 zoomout，使用 smoothleft 替代
        cmd = [
            'ffmpeg', '-y',
            '-i', video1,
            '-i', video2,
            '-filter_complex',
            f"[0:v][1:v]xfade=transition=smoothleft:duration={fade_duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={fade_duration}[a]",
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            return self._apply_fade(video1, video2, output_path, config)
        
        return output_path
    
    def _apply_blur(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: TransitionConfig,
    ) -> str:
        """模糊过渡"""
        dur1, _, _ = self._get_video_info(video1)
        
        fade_duration = config.duration
        offset = dur1 - fade_duration
        
        # 使用 pixelize 作为模糊效果的替代
        cmd = [
            'ffmpeg', '-y',
            '-i', video1,
            '-i', video2,
            '-filter_complex',
            f"[0:v][1:v]xfade=transition=pixelize:duration={fade_duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={fade_duration}[a]",
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            return self._apply_fade(video1, video2, output_path, config)
        
        return output_path
    
    def _apply_circle(
        self,
        video1: str,
        video2: str,
        output_path: str,
        config: TransitionConfig,
    ) -> str:
        """圆形展开转场"""
        dur1, _, _ = self._get_video_info(video1)
        
        fade_duration = config.duration
        offset = dur1 - fade_duration
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video1,
            '-i', video2,
            '-filter_complex',
            f"[0:v][1:v]xfade=transition=circleopen:duration={fade_duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={fade_duration}[a]",
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            return self._apply_fade(video1, video2, output_path, config)
        
        return output_path
    
    def apply_batch_transitions(
        self,
        videos: List[str],
        output_path: str,
        transition_type: TransitionType = TransitionType.FADE,
        transition_duration: float = 0.5,
    ) -> str:
        """
        批量应用转场效果
        
        Args:
            videos: 视频列表
            output_path: 输出路径
            transition_type: 转场类型
            transition_duration: 转场时长
            
        Returns:
            输出视频路径
        """
        if len(videos) < 2:
            if videos:
                # 只有一个视频，直接复制
                subprocess.run(['cp', videos[0], output_path], capture_output=True)
            return output_path
        
        config = TransitionConfig(type=transition_type, duration=transition_duration)
        
        # 逐个应用转场
        temp_dir = Path(output_path).parent / "temp_transitions"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        current = videos[0]
        
        for i, video in enumerate(videos[1:], 1):
            temp_output = str(temp_dir / f"step_{i}.mp4")
            self.apply_transition(current, video, temp_output, config)
            current = temp_output
        
        # 复制最终结果
        subprocess.run(['cp', current, output_path], capture_output=True)
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return output_path
    
    @staticmethod
    def list_available_transitions() -> List[str]:
        """列出所有可用的转场效果"""
        return [t.value for t in TransitionType]
    
    @staticmethod
    def get_xfade_transitions() -> List[str]:
        """
        获取 FFmpeg xfade 支持的所有转场类型
        
        参考: https://ffmpeg.org/ffmpeg-filters.html#xfade
        """
        return [
            "fade", "fadeblack", "fadewhite",
            "wipeleft", "wiperight", "wipeup", "wipedown",
            "slideleft", "slideright", "slideup", "slidedown",
            "smoothleft", "smoothright", "smoothup", "smoothdown",
            "circlecrop", "rectcrop", "circleopen", "circleclose",
            "dissolve", "pixelize", "radial", "hblur", "vblur",
            "zoomin", "diagtl", "diagtr", "diagbl", "diagbr",
            "hlslice", "hrslice", "vuslice", "vdslice",
            "horzopen", "horzclose", "vertopen", "vertclose",
            "squeezeh", "squeezev",
        ]


def demo_transitions():
    """演示转场效果"""
    print("=" * 50)
    print("转场效果库演示")
    print("=" * 50)
    
    effects = TransitionEffects()
    
    print("\n可用转场效果:")
    for trans in effects.list_available_transitions():
        print(f"  - {trans}")
    
    print("\n\nFFmpeg xfade 支持的转场:")
    xfade_list = effects.get_xfade_transitions()
    for i, trans in enumerate(xfade_list, 1):
        print(f"  {i:2d}. {trans}")


if __name__ == '__main__':
    demo_transitions()
