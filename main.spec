# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

block_cipher = None

# 项目根目录
project_root = Path(__file__).parent

def get_hidden_imports():
    """获取所有隐藏导入"""
    hidden_imports = [
        # PySide6 核心
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        # AI 服务
        'app.services.ai.story_analyzer',
        'app.services.ai.cut_template',
        'app.services.ai.batch_story_processor',
        'app.services.ai.cut_preview',
        'app.services.ai.llm_manager',
        'app.services.ai.scene_analyzer',
        'app.services.ai.video_content_analyzer',
        'app.services.ai.video_summarizer',
        'app.services.ai.video_understanding',
        'app.services.ai.script_generator',
        'app.services.ai.voice_generator',
        'app.services.ai.vision_providers',
        'app.services.ai.providers.openai',
        'app.services.ai.providers.claude',
        'app.services.ai.providers.gemini',
        'app.services.ai.providers.qwen',
        'app.services.ai.providers.kimi',
        'app.services.ai.providers.glm5',
        'app.services.ai.providers.deepseek',
        'app.services.ai.providers.local',
        # 视频服务
        'app.services.video',
        'app.services.video.commentary_maker',
        'app.services.video.mashup_maker',
        'app.services.video.monologue_maker',
        'app.services.video.highlight_detector',
        'app.services.video.quality_analyzer',
        'app.services.video.transition_effects',
        'app.services.video.thumbnail_cache',
        # 导出服务
        'app.services.export',
        'app.services.export.jianying_exporter',
        'app.services.export.premiere_exporter',
        'app.services.export.finalcut_exporter',
        'app.services.export.davinci_exporter',
        'app.services.export.edl_exporter',
        'app.services.export.direct_video_exporter',
        # 核心模块
        'app.core.application',
        'app.core.config_manager',
        'app.core.logger',
        'app.core.event_bus',
        'app.core.project_manager',
        'app.core.project_settings_manager',
        'app.core.project_template_manager',
        'app.core.icon_manager',
        'app.core.secure_key_manager',
        'app.core.plugin_service',
        'app.core.service_registry',
        # UI 模块
        'app.ui.main.main_window',
        'app.ui.main.pages.home_page',
        'app.ui.main.pages.projects_page',
        'app.ui.main.pages.video_editor_page',
        'app.ui.main.pages.ai_video_creator_page',
        'app.ui.main.pages.ai_config_page',
        'app.ui.main.pages.ai_chat_page',
        'app.ui.main.pages.story_analysis_page',
        'app.ui.main.pages.template_editor_page',
        'app.ui.components',
        # 其他
        'app.utils.version',
        'app.utils.config',
        'app.utils.error_handler',
        'app.utils.i18n',
    ]
    
    # 动态添加所有 app/ 下的模块
    app_dir = project_root / 'app'
    for py_file in app_dir.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue
        module_path = py_file.relative_to(project_root).with_suffix('')
        module_name = str(module_path).replace('/', '.').replace('\\', '.')
        if module_name not in hidden_imports:
            hidden_imports.append(module_name)
    
    return hidden_imports


a = Analysis(
    ['app/main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # 主题和资源
        (str(project_root / 'app/ui/theme'), 'app/ui/theme'),
        (str(project_root / 'app/core/templates'), 'app/core/templates'),
        (str(project_root / 'resources'), 'resources'),
    ],
    hiddenimports=get_hidden_imports(),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'scipy', 
        'PIL', 'cv2', 'torch', 'tensorflow'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VideoForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI 应用，设为 True 可看到调试输出
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可设置图标: icon='resources/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VideoForge',
)
