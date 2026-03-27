#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
国际化支持模块
提供完整的多语言切换功能
"""

import os
from typing import Dict, Optional, List
from pathlib import Path
import logging
logger = logging.getLogger(__name__)


class I18n:
    """
    国际化管理器
    
    支持多语言切换，完整UI翻译
    """
    
    # 支持的语言
    SUPPORTED_LANGUAGES = {
        "zh-CN": "简体中文",
        "zh-TW": "繁體中文",
        "en-US": "English",
        "ja-JP": "日本語",
        "ko-KR": "한국어",
    }
    
    def __init__(self, locale: str = "zh-CN"):
        self._locale = locale
        self._translations: Dict[str, str] = {}
        self._fallback: Dict[str, str] = {}
        self._load_translations()
        
    def _load_translations(self):
        """加载翻译文件"""
        builtins = self._get_builtin_translations()
        self._fallback = builtins.get("en-US", {})
        
        if self._locale in builtins:
            self._translations = builtins[self._locale]
        else:
            self._translations = self._fallback
    
    def _get_builtin_translations(self) -> Dict[str, Dict]:
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
                "home.welcome": "欢迎使用 ClipFlowCut",
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
                
                # ===== AI 创作 =====
                "ai.commentary": "视频解说",
                "ai.commentary.desc": "AI 自动生成配音和字幕",
                "ai.mashup": "视频混剪",
                "ai.mashup.desc": "多素材智能混剪",
                "ai.monologue": "第一人称独白",
                "ai.monologue.desc": "情感化 AI 独白",
                "ai.generate": "生成",
                "ai.generating": "生成中...",
                "ai.cancel": "取消",
                "ai.progress": "进度",
                "ai.settings": "AI 设置",
                "ai.provider": "AI 提供商",
                "ai.model": "模型",
                "ai.temperature": "创意度",
                "ai.max_tokens": "最大令牌",
                
                # ===== 导出 =====
                "export.title": "导出",
                "export.format": "格式",
                "export.quality": "质量",
                "export.resolution": "分辨率",
                "export.fps": "帧率",
                "export.bitrate": "码率",
                "export.start": "开始导出",
                "export.exporting": "导出中...",
                "export.complete": "导出完成",
                "export.failed": "导出失败",
                "export.preset": "预设",
                "export.custom": "自定义",
                
                # ===== 设置 =====
                "settings.title": "设置",
                "settings.general": "通用",
                "settings.appearance": "外观",
                "settings.shortcuts": "快捷键",
                "settings.cache": "缓存",
                "settings.language": "语言",
                "settings.theme": "主题",
                "settings.dark": "深色",
                "settings.light": "浅色",
                "settings.auto": "自动",
                "settings.font": "字体",
                "settings.font_size": "字体大小",
                "settings.ffmpeg_path": "FFmpeg 路径",
                "settings.temp_dir": "临时目录",
                "settings.auto_save": "自动保存",
                "settings.auto_save_interval": "自动保存间隔",
                
                # ===== 通用 =====
                "common.save": "保存",
                "common.cancel": "取消",
                "common.confirm": "确认",
                "common.delete": "删除",
                "common.edit": "编辑",
                "common.search": "搜索",
                "common.loading": "加载中...",
                "common.success": "成功",
                "common.error": "错误",
                "common.warning": "警告",
                "common.info": "提示",
                "common.close": "关闭",
                "common.back": "返回",
                "common.next": "下一步",
                "common.previous": "上一步",
                "common.start": "开始",
                "common.stop": "停止",
                "common.pause": "暂停",
                "common.resume": "继续",
                "common.refresh": "刷新",
                "common.upload": "上传",
                "common.download": "下载",
                "common.select": "选择",
                "common.select_all": "全选",
                "common.select_none": "取消全选",
                "common.yes": "是",
                "common.no": "否",
                "common.ok": "确定",
                "common.apply": "应用",
                "common.reset": "重置",
                "common.browse": "浏览",
                "common.name": "名称",
                "common.type": "类型",
                "common.date": "日期",
                "common.status": "状态",
                "common.version": "版本",
                
                # ===== 消息 =====
                "msg.saved": "已保存",
                "msg.deleted": "已删除",
                "msg.copied": "已复制",
                "msg.cut": "已剪切",
                "msg.pasted": "已粘贴",
                "msg.undo_success": "撤销成功",
                "msg.redo_success": "重做成功",
                "msg.no_changes": "没有更改",
                "msg.unsaved_changes": "有未保存的更改",
                "msg.confirm_delete": "确定要删除吗？",
                "msg.confirm_overwrite": "文件已存在，是否覆盖？",
                
                # ===== 错误 =====
                "err.file_not_found": "文件未找到",
                "err.invalid_format": "无效的格式",
                "err.too_large": "文件过大",
                "err.network": "网络错误",
                "err.api_key": "API 密钥无效",
                "err.rate_limit": "请求过于频繁，请稍后重试",
                "err.unknown": "未知错误",
                "err.ffmpeg_not_found": "未找到 FFmpeg",
                "err.permission_denied": "权限不足",
                
                # ===== 提示 =====
                "tip.new_project": "创建新项目",
                "tip.import_video": "导入视频",
                "tip.export_video": "导出视频",
                "tip.ai_create": "AI 智能创作",
                "tip.quick_edit": "快速剪辑",
            },
            
            "en-US": {
                # ===== Navigation =====
                "nav.home": "Home",
                "nav.projects": "Projects",
                "nav.editor": "Editor",
                "nav.ai_create": "AI Create",
                "nav.ai_chat": "AI Chat",
                "nav.settings": "Settings",
                "nav.plugins": "Plugins",
                "nav.about": "About",
                
                # ===== Home =====
                "home.welcome": "Welcome to ClipFlowCut",
                "home.subtitle": "AI-Powered Video Creation Platform",
                "home.new_project": "New Project",
                "home.import": "Import Media",
                "home.recent": "Recent",
                "home.templates": "Templates",
                "home.quick_start": "Quick Start",
                "home.features": "Features",
                
                # ===== Project =====
                "project.new": "New Project",
                "project.open": "Open Project",
                "project.save": "Save Project",
                "project.save_as": "Save As",
                "project.delete": "Delete Project",
                "project.export": "Export Project",
                "project.import": "Import Project",
                "project.duplicate": "Duplicate",
                "project.rename": "Rename",
                "project.settings": "Project Settings",
                "project.info": "Project Info",
                "project.last_modified": "Last Modified",
                "project.duration": "Duration",
                "project.size": "Size",
                
                # ===== Editor =====
                "editor.timeline": "Timeline",
                "editor.preview": "Preview",
                "editor.properties": "Properties",
                "editor.assets": "Assets",
                "editor.effects": "Effects",
                "editor.transitions": "Transitions",
                "editor.text": "Text",
                "editor.audio": "Audio",
                "editor.cut": "Cut",
                "editor.copy": "Copy",
                "editor.paste": "Paste",
                "editor.undo": "Undo",
                "editor.redo": "Redo",
                "editor.zoom_in": "Zoom In",
                "editor.zoom_out": "Zoom Out",
                "editor.fit": "Fit to Window",
                
                # ===== AI Create =====
                "ai.commentary": "Video Commentary",
                "ai.commentary.desc": "AI auto-generates voiceover and subtitles",
                "ai.mashup": "Video Mashup",
                "ai.mashup.desc": "Intelligent multi-clip editing",
                "ai.monologue": "First-Person Monologue",
                "ai.monologue.desc": "Emotional AI monologue",
                "ai.generate": "Generate",
                "ai.generating": "Generating...",
                "ai.cancel": "Cancel",
                "ai.progress": "Progress",
                "ai.settings": "AI Settings",
                "ai.provider": "Provider",
                "ai.model": "Model",
                "ai.temperature": "Temperature",
                "ai.max_tokens": "Max Tokens",
                
                # ===== Export =====
                "export.title": "Export",
                "export.format": "Format",
                "export.quality": "Quality",
                "export.resolution": "Resolution",
                "export.fps": "Frame Rate",
                "export.bitrate": "Bitrate",
                "export.start": "Start Export",
                "export.exporting": "Exporting...",
                "export.complete": "Export Complete",
                "export.failed": "Export Failed",
                "export.preset": "Preset",
                "export.custom": "Custom",
                
                # ===== Settings =====
                "settings.title": "Settings",
                "settings.general": "General",
                "settings.appearance": "Appearance",
                "settings.shortcuts": "Shortcuts",
                "settings.cache": "Cache",
                "settings.language": "Language",
                "settings.theme": "Theme",
                "settings.dark": "Dark",
                "settings.light": "Light",
                "settings.auto": "Auto",
                "settings.font": "Font",
                "settings.font_size": "Font Size",
                "settings.ffmpeg_path": "FFmpeg Path",
                "settings.temp_dir": "Temp Directory",
                "settings.auto_save": "Auto Save",
                "settings.auto_save_interval": "Auto Save Interval",
                
                # ===== Common =====
                "common.save": "Save",
                "common.cancel": "Cancel",
                "common.confirm": "Confirm",
                "common.delete": "Delete",
                "common.edit": "Edit",
                "common.search": "Search",
                "common.loading": "Loading...",
                "common.success": "Success",
                "common.error": "Error",
                "common.warning": "Warning",
                "common.info": "Info",
                "common.close": "Close",
                "common.back": "Back",
                "common.next": "Next",
                "common.previous": "Previous",
                "common.start": "Start",
                "common.stop": "Stop",
                "common.pause": "Pause",
                "common.resume": "Resume",
                "common.refresh": "Refresh",
                "common.upload": "Upload",
                "common.download": "Download",
                "common.select": "Select",
                "common.select_all": "Select All",
                "common.select_none": "Select None",
                "common.yes": "Yes",
                "common.no": "No",
                "common.ok": "OK",
                "common.apply": "Apply",
                "common.reset": "Reset",
                "common.browse": "Browse",
                "common.name": "Name",
                "common.type": "Type",
                "common.date": "Date",
                "common.status": "Status",
                "common.version": "Version",
                
                # ===== Messages =====
                "msg.saved": "Saved",
                "msg.deleted": "Deleted",
                "msg.copied": "Copied",
                "msg.cut": "Cut",
                "msg.pasted": "Pasted",
                "msg.undo_success": "Undo successful",
                "msg.redo_success": "Redo successful",
                "msg.no_changes": "No changes",
                "msg.unsaved_changes": "Unsaved changes",
                "msg.confirm_delete": "Are you sure you want to delete?",
                "msg.confirm_overwrite": "File exists, overwrite?",
                
                # ===== Errors =====
                "err.file_not_found": "File not found",
                "err.invalid_format": "Invalid format",
                "err.too_large": "File too large",
                "err.network": "Network error",
                "err.api_key": "Invalid API key",
                "err.rate_limit": "Rate limit exceeded, please try again later",
                "err.unknown": "Unknown error",
                "err.ffmpeg_not_found": "FFmpeg not found",
                "err.permission_denied": "Permission denied",
                
                # ===== Tips =====
                "tip.new_project": "Create new project",
                "tip.import_video": "Import video",
                "tip.export_video": "Export video",
                "tip.ai_create": "AI intelligent creation",
                "tip.quick_edit": "Quick edit",
            },
            
            "ja-JP": {
                # ===== Navigation =====
                "nav.home": "ホーム",
                "nav.projects": "プロジェクト",
                "nav.editor": "エディター",
                "nav.ai_create": "AI作成",
                "nav.ai_chat": "AIチャット",
                "nav.settings": "設定",
                "nav.plugins": "プラグイン",
                "nav.about": "概要",
                
                # ===== Home =====
                "home.welcome": "ClipFlowCutへようこそ",
                "home.subtitle": "AI搭載の動画作成プラットフォーム",
                "home.new_project": "新規プロジェクト",
                "home.import": "メディアをインポート",
                "home.recent": "最近",
                "home.templates": "テンプレート",
                "home.quick_start": "クイックスタート",
                "home.features": "機能",
                
                # ===== Common =====
                "common.save": "保存",
                "common.cancel": "キャンセル",
                "common.confirm": "確認",
                "common.delete": "削除",
                "common.edit": "編集",
                "common.search": "検索",
                "common.loading": "読み込み中...",
                "common.success": "成功",
                "common.error": "エラー",
                "common.warning": "警告",
                "common.info": "情報",
                "common.close": "閉じる",
                "common.back": "戻る",
                "common.next": "次へ",
                "common.previous": "前へ",
                "common.start": "開始",
                "common.stop": "停止",
                "common.pause": "一時停止",
                "common.resume": "再開",
                "common.refresh": "更新",
                "common.upload": "アップロード",
                "common.download": "ダウンロード",
                "common.select": "選択",
                "common.select_all": "すべて選択",
                "common.select_none": "選択解除",
                "common.yes": "はい",
                "common.no": "いいえ",
                "common.ok": "OK",
                "common.apply": "適用",
                "common.reset": "リセット",
                "common.browse": "参照",
                "common.name": "名前",
                "common.type": "タイプ",
                "common.date": "日付",
                "common.status": "ステータス",
                "common.version": "バージョン",
                
                # ===== Errors =====
                "err.file_not_found": "ファイルが見つかりません",
                "err.invalid_format": "無効な形式",
                "err.too_large": "ファイルが大きすぎます",
                "err.network": "ネットワークエラー",
                "err.api_key": "無効なAPIキー",
                "err.rate_limit": "リクエスト过多です",
                "err.unknown": "不明なエラー",
                "err.ffmpeg_not_found": "FFmpegが見つかりません",
                "err.permission_denied": "権限がありません",
            },
            
            "ko-KR": {
                # ===== Navigation =====
                "nav.home": "홈",
                "nav.projects": "프로젝트",
                "nav.editor": "편집기",
                "nav.ai_create": "AI 생성",
                "nav.ai_chat": "AI 채팅",
                "nav.settings": "설정",
                "nav.plugins": "플러그인",
                "nav.about": "정보",
                
                # ===== Home =====
                "home.welcome": "ClipFlowCut에 오신 것을 환영합니다",
                "home.subtitle": "AI 기반 비디오 제작 플랫폼",
                "home.new_project": "새 프로젝트",
                "home.import": "미디어 가져오기",
                "home.recent": "최근",
                "home.templates": "템플릿",
                "home.quick_start": "빠른 시작",
                "home.features": "기능",
                
                # ===== Common =====
                "common.save": "저장",
                "common.cancel": "취소",
                "common.confirm": "확인",
                "common.delete": "삭제",
                "common.edit": "편집",
                "common.search": "검색",
                "common.loading": "로딩 중...",
                "common.success": "성공",
                "common.error": "오류",
                "common.warning": "경고",
                "common.info": "정보",
                "common.close": "닫기",
                "common.back": "뒤로",
                "common.next": "다음",
                "common.previous": "이전",
                "common.start": "시작",
                "common.stop": "중지",
                "common.pause": "일시정지",
                "common.resume": "재개",
                "common.refresh": "새로고침",
                "common.upload": "업로드",
                "common.download": "다운로드",
                "common.select": "선택",
                "common.select_all": "모두 선택",
                "common.select_none": "선택 해제",
                "common.yes": "예",
                "common.no": "아니오",
                "common.ok": "확인",
                "common.apply": "적용",
                "common.reset": "초기화",
                "common.browse": "찾아보기",
                "common.name": "이름",
                "common.type": "유형",
                "common.date": "날짜",
                "common.status": "상태",
                "common.version": "버전",
                
                # ===== Errors =====
                "err.file_not_found": "파일을 찾을 수 없습니다",
                "err.invalid_format": "잘못된 형식",
                "err.too_large": "파일이 너무 큽니다",
                "err.network": "네트워크 오류",
                "err.api_key": "잘못된 API 키",
                "err.rate_limit": "요청이 너무 많습니다",
                "err.unknown": "알 수 없는 오류",
                "err.ffmpeg_not_found": "FFmpeg를 찾을 수 없습니다",
                "err.permission_denied": "권한이 없습니다",
            },
            
            "zh-TW": {
                # ===== 導航 =====
                "nav.home": "首頁",
                "nav.projects": "專案管理",
                "nav.editor": "影片剪輯",
                "nav.ai_create": "AI創作",
                "nav.ai_chat": "AI對話",
                "nav.settings": "設定",
                "nav.plugins": "外掛",
                "nav.about": "關於",
                
                # ===== 首頁 =====
                "home.welcome": "歡迎使用 ClipFlowCut",
                "home.subtitle": "AI 驅動的專業影片創作平台",
                "home.new_project": "新建專案",
                "home.import": "匯入素材",
                "home.recent": "最近創作",
                
                # ===== 通用 =====
                "common.save": "儲存",
                "common.cancel": "取消",
                "common.confirm": "確認",
                "common.delete": "刪除",
                "common.edit": "編輯",
                "common.search": "搜尋",
                "common.loading": "載入中...",
                "common.success": "成功",
                "common.error": "錯誤",
                "common.warning": "警告",
                "common.info": "提示",
                "common.close": "關閉",
                "common.back": "返回",
                "common.next": "下一步",
                "common.previous": "上一步",
            },
        }
    
    def set_locale(self, locale: str):
        """设置语言"""
        if locale in self.SUPPORTED_LANGUAGES:
            self._locale = locale
            self._load_translations()
    
    def get_locale(self) -> str:
        """获取当前语言"""
        return self._locale
    
    def t(self, key: str, **kwargs) -> str:
        """翻译文本"""
        text = self._translations.get(key) or self._fallback.get(key) or key
        
        if kwargs:
            try:
                text = text.format(**kwargs)
            except Exception:
                logger.debug("Operation failed")
                
        return text
    
    def get_available_locales(self) -> Dict[str, str]:
        """获取可用语言列表"""
        return self.SUPPORTED_LANGUAGES.copy()
    
    def get_all_keys(self) -> List[str]:
        """获取所有翻译键"""
        return list(self._fallback.keys())


# 全局实例
_i18n = I18n()


def t(key: str, **kwargs) -> str:
    """快捷翻译函数"""
    return _i18n.t(key, **kwargs)


def set_locale(locale: str):
    """设置语言"""
    _i18n.set_locale(locale)


def get_locale() -> str:
    """获取当前语言"""
    return _i18n.get_locale()


def get_available_locales() -> Dict[str, str]:
    """获取可用语言"""
    return _i18n.get_available_locales()
