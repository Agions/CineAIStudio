#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CineFlow 增强视频能力示例

演示：
- 视频帧提取
- 关键帧检测
- 场景检测
- 增强视觉分析（目标检测、表情识别、情感分析等）
- 时序分析
"""

import asyncio
import json
from pathlib import Path

from app.services.video.video_service import VideoService
from app.services.ai.enhanced_vision_service import EnhancedVisionService


# ==================== 示例配置 ====================

# 视频路径
VIDEO_PATH = "path/to/your/video.mp4"

# 输出目录
OUTPUT_DIR = "./output"

# 配置
CONFIG = {
    "VL": {
        "enabled": True,
        "qwen_vl": {
            "api_key": "${QWEN_VL_API_KEY}",  # 替换为实际 API key
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "default",
        },
    },
}

# ==================== 视频处理示例 ====================

async def example_1_extract_frames():
    """示例 1: 提取视频帧"""
    print("\n" + "=" * 60)
    print("示例 1: 提取视频帧")
    print("=" * 60)

    # 创建视频服务
    video_service = VideoService()

    # 获取视频信息
    info = video_service.get_video_info(VIDEO_PATH)
    print(f"\n视频信息:")
    print(f"  分辨率: {info['resolution']}")
    print(f"  帧率: {info['fps']:.2f} FPS")
    print(f"  总帧数: {info['total_frames']}")
    print(f"  时长: {info['duration']:.2f} 秒")

    # 提取帧（每隔 1 秒）
    print(f"\n提取帧中...（间隔 1 秒）")

    def progress_callback(current, total):
        percent = (current / total) * 100
        print(f"  进度: {percent:.1f}% ({current}/{total})")

    frames = video_service.extract_frames(
        VIDEO_PATH,
        output_dir=f"{OUTPUT_DIR}/frames",
        interval=1.0,
        max_frames=10,  # 最多提取 10 帧用于演示
        progress_callback=progress_callback,
    )

    print(f"\n成功提取 {len(frames)} 帧:")
    for i, frame in enumerate(frames[:5]):  # 只显示前 5 帧
        print(f"  [{i}] {frame}")

    if len(frames) > 5:
        print(f"  ... 还有 {len(frames) - 5} 帧")

    return frames


async def example_2_extract_key_frames():
    """示例 2: 提取关键帧（基于场景变化）"""
    print("\n" + "=" * 60)
    print("示例 2: 提取关键帧")
    print("=" * 60)

    video_service = VideoService()

    print(f"\n提取关键帧中...（场景变化阈值: 30.0）")

    key_frames = video_service.extract_key_frames(
        VIDEO_PATH,
        output_dir=f"{OUTPUT_DIR}/keyframes",
        threshold=30.0,
        min_interval=30,  # 最小间隔 30 帧
        max_frames=20,  # 最多 20 帧
    )

    print(f"\n成功提取 {len(key_frames)} 个关键帧:")
    for kf in key_frames:
        print(f"  {kf['name']}: {kf['timestamp']:.2f}s (变化分数: {kf['diff_score']:.2f})")

    return key_frames


async def example_3_detect_scenes():
    """示例 3: 检测场景变化"""
    print("\n" + "=" * 60)
    print("示例 3: 检测场景变化")
    print("=" * 60)

    video_service = VideoService()

    print(f"\n检测场景中...（阈值: 30.0）")

    scenes = video_service.detect_scenes(
        VIDEO_PATH,
        threshold=30.0,
        min_scene_duration=1.0,  # 最小场景时长 1 秒
    )

    print(f"\n检测到 {len(scenes)} 个场景:")
    for scene in scenes[:10]:  # 只显示前 10 个场景
        print(f"  Scene {scene['id'] + 1}: {scene['start_time']:.2f}s -> {scene['end_time']:.2f}s "
              f"(时长: {scene['duration']:.2f}s)")

    if len(scenes) > 10:
        print(f"  ... 还有 {len(scenes) - 10} 个场景")

    return scenes


async def example_4_analyze_motion():
    """示例 4: 分析运动"""
    print("\n" + "=" * 60)
    print("示例 4: 分析运动")
    print("=" * 60)

    video_service = VideoService()

    print(f"\n分析运动中...")

    motion_analysis = video_service.analyze_motion(
        VIDEO_PATH,
        frame_interval=10,  # 每隔 10 帧分析一次
    )

    if motion_analysis:
        print(f"\n运动分析结果:")
        print(f"  平均运动强度: {motion_analysis['avg_motion']:.2f}")
        print(f"  最大运动强度: {motion_analysis['max_motion']:.2f}")
        print(f"  运动标准差: {motion_analysis['std_motion']:.2f}")
        print(f"  分析间隔: 每 {motion_analysis['frame_interval']} 帧分析一次")

        # 判断视频动态类型
        avg = motion_analysis['avg_motion']
        if avg < 10:
            motion_type = "静态/慢速"
        elif avg < 50:
            motion_type = "中等动态"
        else:
            motion_type = "高动态"

        print(f"  动态类型: {motion_type}")

    return motion_analysis


# ==================== 增强视觉分析示例 ====================

async def example_5_detect_objects():
    """示例 5: 目标检测"""
    print("\n" + "=" * 60)
    print("示例 5: 目标检测")
    print("=" * 60)

    vision_service = EnhancedVisionService(CONFIG)

    frame_path = f"{OUTPUT_DIR}/frames/frame_000000_t0.00s.jpg"

    print(f"\n检测目标中...（帧: {frame_path})")

    result = await vision_service.detect_objects(
        frame_path,
        object_types=None,  # 检测所有类型
    )

    if result["success"]:
        print(f"\n检测结果:")
        print(f"  模型: {result['model']}")
        print(f"  数据: {json.dumps(result['data'], indent=2, ensure_ascii=False)}")

    return result


async def example_6_recognize_faces():
    """示例 6: 人脸识别"""
    print("\n" + "=" * 60)
    print("示例 6: 人脸识别")
    print("=" * 60)

    vision_service = EnhancedVisionService(CONFIG)

    frame_path = f"{OUTPUT_DIR}/frames/frame_000000_t0.00s.jpg"

    print(f"\n识别人物中...（帧: {frame_path})")

    # 人物识别
    person_result = await vision_service.recognize_persons(
        frame_path,
        recognize_faces=True,
    )

    if person_result["success"]:
        print(f"\n人物识别结果:")
        print(f"  {person_result['data']['raw_text']}")

    # 表情识别
    print(f"\n识别表情中...")

    expression_result = await vision_service.recognize_face_expressions(
        frame_path,
    )

    if expression_result["success"]:
        print(f"\n表情识别结果:")
        print(f"  {expression_result['data']['raw_text']}")

    return person_result, expression_result


async def example_7_emotion_analysis():
    """示例 7: 情感分析"""
    print("\n" + "=" * 60)
    print("示例 7: 情感分析")
    print("=" * 60)

    vision_service = EnhancedVisionService(CONFIG)

    frame_path = f"{OUTPUT_DIR}/frames/frame_000000_t0.00s.jpg"

    print(f"\n分析情感中...（帧: {frame_path})")

    result = await vision_service.analyze_emotion(
        frame_path,
        include_context=True,
    )

    if result["success"]:
        print(f"\n情感分析结果:")
        print(f"  {result['data']['raw_text']}")

    return result


async def example_8_depth_light_composition():
    """示例 8: 深度、光照、构图分析"""
    print("\n" + "=" * 60)
    print("示例 8: 深度、光照、构图分析")
    print("=" * 60)

    vision_service = EnhancedVisionService(CONFIG)

    frame_path = f"{OUTPUT_DIR}/frames/frame_000000_t0.00s.jpg"

    # 深度分析
    print(f"\n分析场景深度...")

    depth_result = await vision_service.analyze_depth(frame_path)
    if depth_result["success"]:
        print(f"\n深度分析结果:")
        print(f"  {depth_result['data']['raw_text']}")

    # 光照分析
    print(f"\n分析光照...")

    lighting_result = await vision_service.analyze_lighting(frame_path)
    if lighting_result["success"]:
        print(f"\n光照分析结果:")
        print(f"  {lighting_result['data']['raw_text']}")

    # 构图评分
    print(f"\n评分构图...")

    composition_result = await vision_service.score_composition(frame_path)
    if composition_result["success"]:
        print(f"\n构图评分结果:")
        print(f"  {composition_result['data']['raw_text']}")

    return depth_result, lighting_result, composition_result


# ==================== 综合分析示例 ====================

async def example_9_comprehensive_analysis():
    """示例 9: 综合分析"""
    print("\n" + "=" * 60)
    print("示例 9: 单帧综合分析")
    print("=" * 60)

    vision_service = EnhancedVisionService(CONFIG)

    frame_path = f"{OUTPUT_DIR}/frames/frame_000000_t0.00s.jpg"

    print(f"\n执行综合分析...（帧: {frame_path}）")
    print("(包含所有高级分析，可能需要较长时间)")

    result = await vision_service.comprehensive_analysis(
        frame_path,
        include_all=True,
    )

    if result["success"]:
        print(f"\n综合分析完成:")
        print(f"  分析时间: {result['data']['timestamp']}")
        print(f"  图像: {result['data']['image']}")

        print(f"\n基础分析:")
        basic = result["data"]["basic"]
        print(f"  - 场景描述: {basic['scene']['description'][:100]}...")
        print(f"  - 标签数: {basic['tags']['count']}")

        print(f"\n高级分析:")
        advanced = result["data"]["advanced"]
        if advanced:
            for key, value in advanced.items():
                if value:
                    print(f"  - {key}: ✓")
                else:
                    print(f"  - {key}: ✗")

    return result


async def example_10_video_with_vision():
    """示例 10: 视频+视觉分析联动"""
    print("\n" + "=" * 60)
    print("示例 10: 视频+视觉分析联动")
    print("=" * 60)

    # 初始化服务
    video_service = VideoService()
    vision_service = EnhancedVisionService(CONFIG)

    # 提取关键帧
    print(f"\n提取关键帧...")
    key_frames = video_service.extract_key_frames(
        VIDEO_PATH,
        output_dir=f"{OUTPUT_DIR}/keyframes_analysis",
        threshold=30.0,
        max_frames=5,  # 只分析 5 个关键帧
    )

    # 对每个关键帧进行分析
    print(f"\n对 {len(key_frames)} 个关键帧进行分析...")

    analysis_results = []

    for i, kf in enumerate(key_frames):
        print(f"\n--- 关键帧 {i + 1}: {kf['timestamp']:.2f}s ---")

        try:
            # 目标检测
            obj_result = await vision_service.detect_objects(kf["path"])

            # 情感分析
            emo_result = await vision_service.analyze_emotion(kf["path"])

            analysis_results.append({
                "keyframe": kf,
                "objects": obj_result["data"] if obj_result["success"] else None,
                "emotion": emo_result["data"] if emo_result["success"] else None,
            })

        except Exception as e:
            print(f"  分析失败: {e}")

    # 保存结果
    output_path = Path(OUTPUT_DIR) / "video_vision_analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)

    print(f"\n分析完成，结果已保存到: {output_path}")

    return analysis_results


# ==================== 主函数 ====================

async def main():
    """主函数"""

    # 创建输出目录
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("CineFlow 增强视频能力示例")
    print("=" * 60)

    # 选择要运行的示例
    examples = {
        "1": ("提取视频帧", example_1_extract_frames),
        "2": ("提取关键帧", example_2_extract_key_frames),
        "3": ("检测场景变化", example_3_detect_scenes),
        "4": ("分析运动", example_4_analyze_motion),
        "5": ("目标检测", example_5_detect_objects),
        "6": ("人脸和表情识别", example_6_recognize_faces),
        "7": ("情感分析", example_7_emotion_analysis),
        "8": ("深度、光照、构图分析", example_8_depth_light_composition),
        "9": ("综合分析", example_9_comprehensive_analysis),
        "10": ("视频+视觉分析联动", example_10_video_with_vision),
    }

    print("\n可用的示例:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")

    print(f"\n全部 - 运行所有示例")
    print(f"0 - 退出")

    # 在实际使用中，这里应该是用户输入
    # 为了演示，我们选择几个示例运行
    print("\n提示: 修改代码中的 VIDEO_PATH 指向你的视频文件")
    print("提示: 修改 CONFIG 中的 API_KEY")

    # 如果用户想要运行示例
    print("\n当前设置为运行示例: 1, 3, 10")
    print("(修改此代码选择其他示例)")

    selected = ["1", "3", "10"]

    if "全部" in selected or "all" in selected:
        for key, (name, func) in examples.items():
            try:
                await func()
            except Exception as e:
                print(f"\n错误: {e}")
    else:
        for key in selected:
            if key in examples:
                name, func = examples[key]
                try:
                    await func()
                except Exception as e:
                    print(f"\n示例 {name} 执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
