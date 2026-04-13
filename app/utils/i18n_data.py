#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
国际化翻译数据

包含所有内置翻译字符串。
自动生成，禁止手动修改。
"""

from typing import Dict


def get_translations() -> Dict[str, Dict]:
    """获取内置完整翻译"""
    return {
        "zh-CN": {
            # ===== 导航 =====
            "nav.home": "首页",
            "nav.projects": "项目管理",
            "nav.editor": "视频剪辑",
            "nav.ai_create": "AI创作",
            "nav.ai_chat": "AI对话",
            "nav.settings": "设置",
            "nav.plugins": "插件管理",
            "nav.about": "关于",

            # ===== 首页 =====
            "home.welcome": "欢迎使用 Narrafiilm",
            "home.subtitle": "AI 驱动的专业视频创作平台",
            "home.new_project": "新建项目",
            "home.import": "导入素材",
            "home.recent": "最近创作",
            "home.templates": "项目模板",
            "home.quick_start": "快速开始",
            "home.features": "功能介绍",

            # ===== 项目 =====
            "project.new": "新建项目",
            "project.open": "打开项目",
            "project.save": "保存项目",
            "project.save_as": "另存为",
            "project.delete": "删除项目",
            "project.export": "导出项目",
            "project.import": "导入项目",
            "project.duplicate": "复制项目",
            "project.rename": "重命名",
            "project.settings": "项目设置",
            "project.info": "项目信息",
            "project.last_modified": "最后修改",
            "project.duration": "时长",
            "project.size": "大小",

            # ===== 编辑器 =====
            "editor.timeline": "时间轴",
            "editor.preview": "预览",
            "editor.properties": "属性",
            "editor.assets": "素材库",
            "editor.effects": "特效",
            "editor.transitions": "转场",
            "editor.text": "字幕",
            "editor.audio": "音频",
            "editor.cut": "剪切",
            "editor.copy": "复制",
            "editor.paste": "粘贴",
            "editor.undo": "撤销",
            "editor.redo": "重做",
            "editor.zoom_in": "放大",
            "editor.zoom_out": "缩小",
            "editor.fit": "适应窗口",
            "editor.fullscreen": "全屏",

            # ===== 时间轴 =====
            "timeline.add_track": "添加轨道",
            "timeline.delete_track": "删除轨道",
            "timeline.track_video": "视频轨道",
            "timeline.track_audio": "音频轨道",
            "timeline.track_text": "字幕轨道",
            "timeline.track_effect": "特效轨道",

            # ===== 预览 =====
            "preview.play": "播放",
            "preview.pause": "暂停",
            "preview.stop": "停止",
            "preview.forward": "快进",
            "preview.backward": "快退",
            "preview.next_frame": "下一帧",
            "preview.prev_frame": "上一帧",
            "preview.loop": "循环",

            # ===== 素材库 =====
            "assets.video": "视频",
            "assets.audio": "音频",
            "assets.image": "图片",
            "assets.text": "文字",
            "assets.effect": "特效",
            "assets.transition": "转场",
            "assets.import": "导入素材",
            "assets.delete": "删除素材",
            "assets.rename": "重命名",

            # ===== 导出 =====
            "export.title": "导出视频",
            "export.format": "格式",
            "export.resolution": "分辨率",
            "export.fps": "帧率",
            "export.bitrate": "码率",
            "export.start": "开始导出",
            "export.cancel": "取消导出",
            "export.progress": "导出进度",
            "export.success": "导出成功",
            "export.failed": "导出失败",

            # ===== AI 功能 =====
            "ai.analyze": "AI 分析",
            "ai.generate": "AI 生成",
            "ai.enhance": "AI 增强",
            "ai.subtitle": "AI 字幕",
            "ai.voiceover": "AI 配音",
            "ai.script": "AI 文案",
            "ai.scene": "场景识别",

            # ===== 设置 =====
            "settings.general": "通用设置",
            "settings.appearance": "外观",
            "settings.shortcuts": "快捷键",
            "settings.audio": "音频设置",
            "settings.video": "视频设置",
            "settings.export": "导出设置",
            "settings.ai": "AI 设置",
            "settings.about": "关于",
            "settings.language": "语言",
            "settings.theme": "主题",
            "settings.theme.dark": "深色",
            "settings.theme.light": "浅色",
            "settings.theme.auto": "自动",

            # ===== 通用 =====
            "common.ok": "确定",
            "common.cancel": "取消",
            "common.save": "保存",
            "common.delete": "删除",
            "common.edit": "编辑",
            "common.close": "关闭",
            "common.back": "返回",
            "common.next": "下一步",
            "common.previous": "上一步",
            "common.search": "搜索",
            "common.filter": "筛选",
            "common.sort": "排序",
            "common.refresh": "刷新",
            "common.loading": "加载中...",
            "common.no_data": "暂无数据",
            "common.confirm": "确认",
            "common.yes": "是",
            "common.no": "否",
            "common.error": "错误",
            "common.success": "成功",
            "common.warning": "警告",
            "common.info": "提示",

            # ===== 错误消息 =====
            "error.file_not_found": "文件未找到",
            "error.permission_denied": "权限不足",
            "error.network_error": "网络错误",
            "error.unknown": "未知错误",
            "error.project_load_failed": "项目加载失败",
            "error.project_save_failed": "项目保存失败",
            "error.export_failed": "导出失败",
            "error.ai_request_failed": "AI 请求失败",

            # ===== 提示消息 =====
            "tip.welcome": "欢迎使用 Narrafiilm",
            "tip.quick_start": "点击「新建项目」开始创作",
            "tip.drag_to_import": "拖拽文件到此处导入",
            "tip.keyboard_shortcuts": "使用快捷键提升效率",
            "tip.auto_save": "项目会自动保存",

            # ===== 对话框 =====
            "dialog.new_project.title": "新建项目",
            "dialog.open_project.title": "打开项目",
            "dialog.save_project.title": "保存项目",
            "dialog.export.title": "导出",
            "dialog.settings.title": "设置",
            "dialog.about.title": "关于 Narrafiilm",

            # ===== 状态 =====
            "status.ready": "就绪",
            "status.processing": "处理中",
            "status.saving": "保存中",
            "status.loading": "加载中",
            "status.exporting": "导出中",
            "status.analyzing": "分析中",
            "status.generating": "生成中",

            # ===== 项目模板 =====
            "template.blank": "空白项目",
            "template.vlog": "日常 Vlog",
            "template.travel": "旅行记录",
            "template.food": "美食记录",
            "template.music": "音乐视频",
            "template.tutorial": "教程视频",
            "template.comedy": "搞笑视频",
            "template.sports": "体育视频",
            "template.fashion": "时尚美妆",
            "template.education": "教育培训",
            "template.business": "商务宣传",
            "template.personal": "个人简历",

            # ===== 项目类型 =====
            "project_type.video_editing": "视频剪辑",
            "project_type.ai_enhancement": "AI 增强",
            "project_type.compilation": "混剪合成",
            "project_type.commentary": "AI 解说",
            "project_type.story_analysis": "剧情分析",
            "project_type.multimedia": "多媒体",

            # ===== 情感标签 =====
            "emotion.neutral": "中性",
            "emotion.happy": "开心",
            "emotion.sad": "伤感",
            "emotion.excited": "兴奋",
            "emotion.calm": "平静",
            "emotion.curious": "好奇",
            "emotion.grateful": "感恩",
            "emotion.nostalgic": "怀旧",
            "emotion.motivated": "励志",
            "emotion.anxious": "焦虑",
            "emotion.peaceful": "释然",

            # ===== 字幕样式 =====
            "caption_style.cinematic": "电影感",
            "caption_style.minimal": "简约",
            "caption_style.modern": "现代",
            "caption_style.classic": "经典",
            "caption_style.expressive": "动感",

            # ===== 导出格式 =====
            "export.format.mp4": "MP4 视频",
            "export.format.mov": "MOV 视频",
            "export.format.webm": "WebM 视频",
            "export.format AVI": "AVI 视频",
            "export.format.mkv": "MKV 视频",

            # ===== 视频质量 =====
            "quality.low": "低",
            "quality.medium": "中",
            "quality.high": "高",
            "quality.ultra": "超清",

            # ===== 视频比例 =====
            "ratio.9_16": "9:16 竖屏",
            "ratio.16_9": "16:9 横屏",
            "ratio.1_1": "1:1 方屏",
            "ratio.4_3": "4:3 传统",
            "ratio.21_9": "21:9 电影",

            # ===== 高级设置 =====
            "advanced.codec": "编码器",
            "advanced.bitrate": "码率控制",
            "advanced.crf": "质量控制",
            "advanced.preset": "编码预设",
            "advanced.profile": "编码配置",
            "advanced.level": "编码级别",

            # ===== 音频设置 =====
            "audio.volume": "音量",
            "audio.mute": "静音",
            "audio.solo": "独奏",
            "audio.fade_in": "淡入",
            "audio.fade_out": "淡出",

            # ===== 快捷键提示 =====
            "shortcut.new_project": "新建项目",
            "shortcut.open_project": "打开项目",
            "shortcut.save_project": "保存项目",
            "shortcut.export": "导出",
            "shortcut.undo": "撤销",
            "shortcut.redo": "重做",
            "shortcut.cut": "剪切",
            "shortcut.copy": "复制",
            "shortcut.paste": "粘贴",
            "shortcut.delete": "删除",
            "shortcut.play": "播放",
            "shortcut.pause": "暂停",
            "shortcut.import": "导入",
        },
    }


__all__ = ["get_translations"]
