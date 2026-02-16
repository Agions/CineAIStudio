"""
Viral Video Creator - 爆款视频创建示例
演示如何使用 CineFlow 的爆款视频工具链

工作流程:
1. 静音检测与移除 -> 保持紧凑节奏
2. 节奏分析 -> 评估爆款潜力
3. 字幕生成 -> 添加动态字幕
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.viral_video.silence_remover import SilenceRemover, RemovalResult
from app.services.viral_video.pace_analyzer import PaceAnalyzer, PaceLevel
from app.services.viral_video.caption_generator import (
    CaptionGenerator,
    CaptionConfig,
    CaptionStyle
)


def create_viral_video(
    input_video: str,
    output_video: str,
    caption_text: str = None,
    enable_silence_removal: bool = True,
    target_style: CaptionStyle = CaptionStyle.VIRAL
):
    """
    创建爆款视频
    
    Args:
        input_video: 输入视频路径
        output_video: 输出视频路径
        caption_text: 字幕文本（可选）
        enable_silence_removal: 是否移除静音
        target_style: 字幕样式
    """
    print("🎬 开始创建爆款视频...")
    print(f"📂 输入: {input_video}")
    print(f"📂 输出: {output_video}")
    print()
    
    # ==================== 步骤1: 节奏分析 ====================
    print("📊 步骤 1: 分析视频节奏...")
    analyzer = PaceAnalyzer()
    
    try:
        pace_result = analyzer.analyze(input_video)
        
        print(f"  ✓ 视频时长: {pace_result.video_duration:.1f}秒")
        print(f"  ✓ 节奏等级: {pace_result.metrics.pace_level.value}")
        print(f"  ✓ CPM (每分钟剪辑): {pace_result.metrics.cuts_per_minute:.1f}")
        print(f"  ✓ 爆款分数: {pace_result.metrics.viral_score:.1f}/100")
        print(f"  ✓ 钩子质量: {pace_result.hook_quality:.1f}/100")
        print()
        
        if pace_result.recommendations:
            print("  💡 优化建议:")
            for rec in pace_result.recommendations:
                print(f"     {rec}")
            print()
        
    except Exception as e:
        print(f"  ⚠️  节奏分析失败: {e}")
        print("  → 继续后续步骤...\n")
    
    # ==================== 步骤2: 静音移除 ====================
    if enable_silence_removal:
        print("✂️  步骤 2: 检测并移除静音...")
        remover = SilenceRemover(
            silence_threshold_db=-35.0,
            min_silence_duration=0.8,
            padding_duration=0.15
        )
        
        try:
            # 检测静音
            silence_segments = remover.detect_silence(input_video)
            print(f"  ✓ 检测到 {len(silence_segments)} 个静音片段")
            
            if silence_segments:
                # 移除静音
                temp_output = output_video.replace('.mp4', '_no_silence.mp4')
                removal_result = remover.remove_silence(
                    input_video,
                    temp_output,
                    silence_segments
                )
                
                print(f"  ✓ 原时长: {removal_result.original_duration:.1f}秒")
                print(f"  ✓ 新时长: {removal_result.new_duration:.1f}秒")
                print(f"  ✓ 压缩比: {removal_result.compression_ratio:.1%}")
                print(f"  ✓ 移除了 {len(removal_result.removed_segments)} 个静音段")
                
                # 更新输入视频为移除静音后的版本
                input_video = temp_output
                print()
            else:
                print("  → 未检测到明显静音，跳过移除步骤\n")
                
        except Exception as e:
            print(f"  ⚠️  静音移除失败: {e}")
            print("  → 继续后续步骤...\n")
    
    # ==================== 步骤3: 字幕生成 ====================
    if caption_text:
        print("📝 步骤 3: 生成动态字幕...")
        
        config = CaptionConfig(
            style=target_style,
            font_family="PingFang SC",
            base_font_size=48,
            keyword_font_size=64,
            enable_word_highlight=True
        )
        
        generator = CaptionGenerator(config)
        
        try:
            # 生成字幕
            caption = generator.generate_from_text(caption_text)
            
            print(f"  ✓ 字幕文本: {caption.text}")
            print(f"  ✓ 字数: {len(caption.text)}")
            print(f"  ✓ 关键词数: {sum(1 for w in caption.words if w.is_keyword)}")
            print(f"  ✓ 时长: {caption.end_time - caption.start_time:.1f}秒")
            
            # 导出字幕文件
            srt_path = output_video.replace('.mp4', '.srt')
            ass_path = output_video.replace('.mp4', '.ass')
            
            generator.to_srt_format([caption], srt_path)
            generator.to_ass_format([caption], ass_path)
            
            print(f"  ✓ SRT 字幕: {srt_path}")
            print(f"  ✓ ASS 字幕: {ass_path}")
            print()
            
        except Exception as e:
            print(f"  ⚠️  字幕生成失败: {e}\n")
    
    # ==================== 完成 ====================
    print("✅ 爆款视频创建完成！")
    print(f"📹 输出文件: {output_video}")
    
    if caption_text:
        print(f"📄 字幕文件: {srt_path}, {ass_path}")
    
    print("\n💡 下一步建议:")
    print("  1. 使用视频编辑软件导入字幕文件")
    print("  2. 根据节奏分析建议进一步优化")
    print("  3. 添加背景音乐和音效")
    print("  4. 导出并发布到短视频平台")


def demo_silence_removal():
    """演示静音移除功能"""
    print("=" * 60)
    print("演示: 静音检测与移除")
    print("=" * 60)
    print()
    
    remover = SilenceRemover(
        silence_threshold_db=-40.0,
        min_silence_duration=0.5,
        padding_duration=0.1
    )
    
    print("配置:")
    print(f"  - 静音阈值: {remover.silence_threshold_db} dB")
    print(f"  - 最小静音时长: {remover.min_silence_duration} 秒")
    print(f"  - 缓冲时长: {remover.padding_duration} 秒")
    print()
    
    # 此处需要实际视频文件
    # silence_segments = remover.detect_silence('your_video.mp4')
    # result = remover.remove_silence('your_video.mp4', 'output.mp4')
    
    print("✓ 演示完成")
    print()


def demo_pace_analysis():
    """演示节奏分析功能"""
    print("=" * 60)
    print("演示: 视频节奏分析")
    print("=" * 60)
    print()
    
    analyzer = PaceAnalyzer()
    
    print("爆款视频标准:")
    for key, value in analyzer.VIRAL_THRESHOLDS.items():
        print(f"  - {key}: {value}")
    print()
    
    # 此处需要实际视频文件
    # result = analyzer.analyze('your_video.mp4')
    # print(f"节奏等级: {result.metrics.pace_level.value}")
    # print(f"爆款分数: {result.metrics.viral_score}/100")
    
    print("✓ 演示完成")
    print()


def demo_caption_generation():
    """演示字幕生成功能"""
    print("=" * 60)
    print("演示: 动态字幕生成")
    print("=" * 60)
    print()
    
    generator = CaptionGenerator()
    
    # 生成字幕
    caption = generator.generate_from_text(
        "这个方法太牛逼了！震惊全网的爆款技巧大揭秘！",
        start_time=0.0
    )
    
    print(f"字幕文本: {caption.text}")
    print(f"开始时间: {caption.start_time:.2f}秒")
    print(f"结束时间: {caption.end_time:.2f}秒")
    print(f"总字数: {len(caption.text)}")
    print()
    
    print("分词结果:")
    for i, word in enumerate(caption.words[:10]):  # 只显示前10个
        marker = "🔥" if word.is_keyword else "  "
        print(f"  {marker} '{word.text}' [{word.start_time:.2f}s - {word.end_time:.2f}s]")
    
    if len(caption.words) > 10:
        print(f"  ... (还有 {len(caption.words) - 10} 个词)")
    
    print()
    print("✓ 演示完成")
    print()


if __name__ == '__main__':
    print("🎬 CineFlow - 爆款视频创建工具")
    print("=" * 60)
    print()
    
    # 运行演示
    demo_silence_removal()
    demo_pace_analysis()
    demo_caption_generation()
    
    print()
    print("💡 完整使用示例:")
    print()
    print("  create_viral_video(")
    print("      input_video='input.mp4',")
    print("      output_video='output.mp4',")
    print("      caption_text='你的字幕文本',")
    print("      enable_silence_removal=True")
    print("  )")
    print()
    print("=" * 60)
