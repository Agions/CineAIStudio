#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出系统集成示例
展示如何将导出系统完整集成到应用程序中
"""

import os
import sys
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QTextEdit,
                            QTabWidget, QMessageBox, QSplitter)
from PyQt6.QtCore import QTimer, pyqtSignal

from .export_system import ExportSystem, ExportFormat, ExportQuality
from .jianying_draft_generator import JianyingDraftGenerator
from .performance_optimizer import ExportOptimizer, ExportOptimizationConfig, OptimizationLevel
from ..services.export_service import ExportService, ExportServiceMode
from ..core.logger import Logger
from ..core.event_system import EventSystem


class ExportIntegrationDemo(QMainWindow):
    """导出系统集成演示"""

    def __init__(self):
        super().__init__()
        self.logger = Logger.get_logger(__name__)
        self.export_system = ExportSystem()
        self.export_service = ExportService()
        self.performance_optimizer = ExportOptimizer()
        self.event_system = EventSystem()

        # 启动服务
        self.export_service.start()
        self.performance_optimizer.initialize()

        self.setup_ui()
        self.setup_signals()
        self.setup_demo_data()

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("CineAIStudio 导出系统集成演示")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 标题
        title_label = QLabel("🎬 CineAIStudio 导出系统集成演示")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title_label)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 基础导出演示
        self.basic_tab = self.create_basic_export_tab()
        self.tab_widget.addTab(self.basic_tab, "基础导出")

        # 剪映Draft导出演示
        self.jianying_tab = self.create_jianying_export_tab()
        self.tab_widget.addTab(self.jianying_tab, "剪映Draft")

        # 批量导出演示
        self.batch_tab = self.create_batch_export_tab()
        self.tab_widget.addTab(self.batch_tab, "批量导出")

        # 性能监控演示
        self.performance_tab = self.create_performance_tab()
        self.tab_widget.addTab(self.performance_tab, "性能监控")

        # 模板导出演示
        self.template_tab = self.create_template_export_tab()
        self.tab_widget.addTab(self.template_tab, "模板导出")

        layout.addWidget(self.tab_widget)

        # 状态栏
        self.status_label = QLabel("系统就绪")
        self.statusBar().addWidget(self.status_label)

        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)

    def create_basic_export_tab(self) -> QWidget:
        """创建基础导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明
        info_label = QLabel("基础导出功能演示：支持多种格式导出，包括MP4、AVI、MOV等")
        info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info_label)

        # 快速导出按钮
        buttons_layout = QHBoxLayout()

        self.export_mp4_btn = QPushButton("导出MP4 (H.264)")
        self.export_mp4_btn.clicked.connect(lambda: self.demo_basic_export("mp4_h264"))

        self.export_h265_btn = QPushButton("导出MP4 (H.265)")
        self.export_h265_btn.clicked.connect(lambda: self.demo_basic_export("mp4_h265"))

        self.export_prores_btn = QPushButton("导出MOV (ProRes)")
        self.export_prores_btn.clicked.connect(lambda: self.demo_basic_export("mov_prores"))

        buttons_layout.addWidget(self.export_mp4_btn)
        buttons_layout.addWidget(self.export_h265_btn)
        buttons_layout.addWidget(self.export_prores_btn)

        layout.addLayout(buttons_layout)

        # 导出日志
        self.basic_log = QTextEdit()
        self.basic_log.setReadOnly(True)
        self.basic_log.setMaximumHeight(200)
        layout.addWidget(QLabel("导出日志:"))
        layout.addWidget(self.basic_log)

        return widget

    def create_jianying_export_tab(self) -> QWidget:
        """创建剪映Draft导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明
        info_label = QLabel("剪映Draft导出演示：生成符合剪映草稿格式的JSON文件")
        info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info_label)

        # Draft生成控件
        draft_layout = QHBoxLayout()

        self.generate_draft_btn = QPushButton("生成Draft文件")
        self.generate_draft_btn.clicked.connect(self.demo_jianying_export)

        self.preview_draft_btn = QPushButton("预览Draft内容")
        self.preview_draft_btn.clicked.connect(self.preview_jianying_draft)

        draft_layout.addWidget(self.generate_draft_btn)
        draft_layout.addWidget(self.preview_draft_btn)

        layout.addLayout(draft_layout)

        # Draft内容预览
        self.draft_preview = QTextEdit()
        self.draft_preview.setReadOnly(True)
        self.draft_preview.setMaximumHeight(300)
        layout.addWidget(QLabel("Draft文件内容:"))
        layout.addWidget(self.draft_preview)

        return widget

    def create_batch_export_tab(self) -> QWidget:
        """创建批量导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明
        info_label = QLabel("批量导出演示：同时导出多个项目或多种格式")
        info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info_label)

        # 批量导出按钮
        batch_layout = QHBoxLayout()

        self.batch_mp4_btn = QPushButton("批量导出MP4")
        self.batch_mp4_btn.clicked.connect(lambda: self.demo_batch_export("mp4"))

        self.batch_multi_btn = QPushButton("批量多格式导出")
        self.batch_multi_btn.clicked.connect(lambda: self.demo_batch_export("multi"))

        self.batch_template_btn = QPushButton("批量模板导出")
        self.batch_template_btn.clicked.connect(lambda: self.demo_batch_export("template"))

        batch_layout.addWidget(self.batch_mp4_btn)
        batch_layout.addWidget(self.batch_multi_btn)
        batch_layout.addWidget(self.batch_template_btn)

        layout.addLayout(batch_layout)

        # 批量导出状态
        self.batch_status = QTextEdit()
        self.batch_status.setReadOnly(True)
        self.batch_status.setMaximumHeight(200)
        layout.addWidget(QLabel("批量导出状态:"))
        layout.addWidget(self.batch_status)

        return widget

    def create_performance_tab(self) -> QWidget:
        """创建性能监控标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明
        info_label = QLabel("性能监控演示：实时监控系统资源使用情况和导出性能")
        info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info_label)

        # 性能控制按钮
        perf_layout = QHBoxLayout()

        self.start_monitoring_btn = QPushButton("开始监控")
        self.start_monitoring_btn.clicked.connect(self.start_performance_monitoring)

        self.stop_monitoring_btn = QPushButton("停止监控")
        self.stop_monitoring_btn.clicked.connect(self.stop_performance_monitoring)

        self.optimize_btn = QPushButton("性能优化")
        self.optimize_btn.clicked.connect(self.optimize_performance)

        perf_layout.addWidget(self.start_monitoring_btn)
        perf_layout.addWidget(self.stop_monitoring_btn)
        perf_layout.addWidget(self.optimize_btn)

        layout.addLayout(perf_layout)

        # 性能信息显示
        self.performance_info = QTextEdit()
        self.performance_info.setReadOnly(True)
        layout.addWidget(QLabel("性能信息:"))
        layout.addWidget(self.performance_info)

        return widget

    def create_template_export_tab(self) -> QWidget:
        """创建模板导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 说明
        info_label = QLabel("模板导出演示：使用预定义模板快速导出多种格式")
        info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info_label)

        # 模板选择
        template_layout = QHBoxLayout()

        self.youtube_template_btn = QPushButton("YouTube多格式")
        self.youtube_template_btn.clicked.connect(lambda: self.demo_template_export("youtube_multi_format"))

        self.social_template_btn = QPushButton("社交媒体套件")
        self.social_template_btn.clicked.connect(lambda: self.demo_template_export("social_media_package"))

        self.backup_template_btn = QPushButton("备份存档")
        self.backup_template_btn.clicked.connect(lambda: self.demo_template_export("backup_archive"))

        template_layout.addWidget(self.youtube_template_btn)
        template_layout.addWidget(self.social_template_btn)
        template_layout.addWidget(self.backup_template_btn)

        layout.addLayout(template_layout)

        # 模板导出结果
        self.template_results = QTextEdit()
        self.template_results.setReadOnly(True)
        self.template_results.setMaximumHeight(200)
        layout.addWidget(QLabel("模板导出结果:"))
        layout.addWidget(self.template_results)

        return widget

    def setup_signals(self):
        """设置信号连接"""
        # 导出系统信号
        self.export_system.export_started.connect(self.on_export_started)
        self.export_system.export_progress.connect(self.on_export_progress)
        self.export_system.export_completed.connect(self.on_export_completed)
        self.export_system.export_failed.connect(self.on_export_failed)

        # 事件系统信号
        self.event_system.subscribe("export_started", self.on_event_export_started)
        self.event_system.subscribe("export_completed", self.on_event_export_completed)

    def setup_demo_data(self):
        """设置演示数据"""
        # 创建演示项目数据
        self.demo_projects = [
            {"id": "demo_1", "name": "产品介绍视频", "duration": "00:02:30", "resolution": "1920x1080"},
            {"id": "demo_2", "name": "教学视频", "duration": "00:05:15", "resolution": "1920x1080"},
            {"id": "demo_3", "name": "广告片", "duration": "00:00:30", "resolution": "1920x1080"}
        ]

        # 创建演示素材数据
        self.demo_materials = [
            {"id": "video_1", "path": "/demo/video1.mp4", "type": "video", "duration": 120},
            {"id": "audio_1", "path": "/demo/audio1.mp3", "type": "audio", "duration": 180},
            {"id": "image_1", "path": "/demo/image1.png", "type": "image", "duration": 5}
        ]

    def demo_basic_export(self, format_type: str):
        """演示基础导出"""
        try:
            project = self.demo_projects[0]
            output_path = f"/tmp/{project['name']}_{format_type}.mp4"

            task_id = self.export_system.export_project(
                project_id=project["id"],
                output_path=output_path,
                preset_id=f"{format_type}_preset",
                metadata={
                    "project_name": project["name"],
                    "format": format_type,
                    "demo_mode": True
                }
            )

            self.basic_log.append(f"✅ 基础导出任务已创建: {task_id}")
            self.basic_log.append(f"   项目: {project['name']}")
            self.basic_log.append(f"   格式: {format_type}")
            self.basic_log.append(f"   输出路径: {output_path}")
            self.basic_log.append("")

        except Exception as e:
            self.basic_log.append(f"❌ 基础导出失败: {str(e)}")

    def demo_jianying_export(self):
        """演示剪映Draft导出"""
        try:
            generator = JianyingDraftGenerator()

            # 添加素材
            video_id = generator.add_video_material("/demo/video1.mp4", "主视频")
            audio_id = generator.add_audio_material("/demo/audio1.mp3", "背景音乐")

            # 创建轨道
            video_track_id = generator.create_track("video")
            audio_track_id = generator.create_track("audio")

            # 添加素材到轨道
            generator.add_material_to_track(video_track_id, video_id, 0.0)
            generator.add_material_to_track(audio_track_id, audio_id, 0.0)

            # 添加文字叠加
            generator.add_text_overlay("CineAIStudio演示", 0.0, 5.0)

            # 生成Draft文件
            output_path = "/tmp/jianying_draft.json"
            success = generator.generate_draft(
                project_name="演示项目",
                output_path=output_path
            )

            if success:
                self.draft_preview.setText(f"✅ Draft文件已生成: {output_path}")
                self.preview_jianying_draft()
            else:
                self.draft_preview.setText("❌ Draft文件生成失败")

        except Exception as e:
            self.draft_preview.setText(f"❌ Draft导出失败: {str(e)}")

    def preview_jianying_draft(self):
        """预览剪映Draft内容"""
        try:
            draft_path = "/tmp/jianying_draft.json"
            if os.path.exists(draft_path):
                with open(draft_path, 'r', encoding='utf-8') as f:
                    draft_data = json.load(f, indent=2)
                    self.draft_preview.setText(json.dumps(draft_data, indent=2, ensure_ascii=False))
            else:
                self.draft_preview.setText("❌ Draft文件不存在")
        except Exception as e:
            self.draft_preview.setText(f"❌ 预览失败: {str(e)}")

    def demo_batch_export(self, batch_type: str):
        """演示批量导出"""
        try:
            batch_configs = []

            if batch_type == "mp4":
                # 批量导出MP4
                for project in self.demo_projects:
                    output_path = f"/tmp/{project['name']}_batch.mp4"
                    batch_configs.append({
                        "project_id": project["id"],
                        "output_path": output_path,
                        "preset_id": "mp4_h264_preset",
                        "metadata": project
                    })

            elif batch_type == "multi":
                # 批量多格式导出
                project = self.demo_projects[0]
                formats = ["mp4_h264", "mp4_h265", "mov_prores"]
                for fmt in formats:
                    output_path = f"/tmp/{project['name']}_{fmt}.mp4"
                    batch_configs.append({
                        "project_id": project["id"],
                        "output_path": output_path,
                        "preset_id": f"{fmt}_preset",
                        "metadata": {**project, "format": fmt}
                    })

            elif batch_type == "template":
                # 批量模板导出
                job_ids = self.export_service.export_with_template(
                    project_id=self.demo_projects[0]["id"],
                    template_id="social_media_package",
                    output_dir="/tmp/",
                    project_name=self.demo_projects[0]["name"]
                )
                self.batch_status.append(f"✅ 模板批量导出已创建: {len(job_ids)} 个作业")
                return

            task_ids = self.export_system.export_batch(batch_configs)
            self.batch_status.append(f"✅ 批量导出已创建: {len(task_ids)} 个任务")
            self.batch_status.append(f"   类型: {batch_type}")
            self.batch_status.append("")

        except Exception as e:
            self.batch_status.append(f"❌ 批量导出失败: {str(e)}")

    def start_performance_monitoring(self):
        """开始性能监控"""
        try:
            self.performance_optimizer.monitor.start_monitoring()
            self.performance_info.append("✅ 性能监控已启动")
        except Exception as e:
            self.performance_info.append(f"❌ 启动监控失败: {str(e)}")

    def stop_performance_monitoring(self):
        """停止性能监控"""
        try:
            self.performance_optimizer.monitor.stop_monitoring()
            self.performance_info.append("✅ 性能监控已停止")
        except Exception as e:
            self.performance_info.append(f"❌ 停止监控失败: {str(e)}")

    def optimize_performance(self):
        """优化性能"""
        try:
            # 获取性能建议
            recommendations = self.performance_optimizer.get_resource_recommendations()

            self.performance_info.append("📊 性能优化建议:")
            for rec in recommendations.get("recommendations", []):
                self.performance_info.append(f"   • {rec['message']}")

            # 应用优化
            config = ExportOptimizationConfig(OptimizationLevel.AUTO)
            self.performance_optimizer.update_config(config)

            self.performance_info.append("✅ 性能优化已应用")
            self.performance_info.append("")

        except Exception as e:
            self.performance_info.append(f"❌ 性能优化失败: {str(e)}")

    def demo_template_export(self, template_id: str):
        """演示模板导出"""
        try:
            project = self.demo_projects[0]
            job_ids = self.export_service.export_with_template(
                project_id=project["id"],
                template_id=template_id,
                output_dir="/tmp/",
                project_name=project["name"]
            )

            self.template_results.append(f"✅ 模板导出已创建: {template_id}")
            self.template_results.append(f"   作业数量: {len(job_ids)}")
            self.template_results.append(f"   项目: {project['name']}")
            self.template_results.append("")

        except Exception as e:
            self.template_results.append(f"❌ 模板导出失败: {str(e)}")

    def update_status(self):
        """更新状态"""
        try:
            # 获取队列状态
            queue_status = self.export_system.get_queue_status()
            status_text = f"队列: {queue_status['queue_size']} 待处理, {queue_status['active_tasks']} 处理中"

            # 获取性能信息
            if hasattr(self.performance_optimizer, 'monitor'):
                resources = self.performance_optimizer.monitor.get_system_resources()
                status_text += f" | CPU: {resources.cpu_usage:.1f}% | 内存: {resources.memory_usage:.1f}%"

            self.status_label.setText(status_text)

        except Exception as e:
            self.logger.error(f"Status update failed: {e}")

    # 信号处理方法

    def on_export_started(self, task_id: str):
        """导出开始信号"""
        self.logger.info(f"Export started: {task_id}")

    def on_export_progress(self, task_id: str, progress: float):
        """导出进度信号"""
        self.logger.info(f"Export progress: {task_id} - {progress:.1f}%")

    def on_export_completed(self, task_id: str, output_path: str):
        """导出完成信号"""
        self.logger.info(f"Export completed: {task_id} -> {output_path}")
        QMessageBox.information(self, "导出完成", f"导出任务已完成: {output_path}")

    def on_export_failed(self, task_id: str, error_message: str):
        """导出失败信号"""
        self.logger.error(f"Export failed: {task_id} - {error_message}")
        QMessageBox.warning(self, "导出失败", f"导出任务失败: {error_message}")

    def on_event_export_started(self, data: Dict[str, Any]):
        """事件导出开始"""
        self.logger.info(f"Event export started: {data}")

    def on_event_export_completed(self, data: Dict[str, Any]):
        """事件导出完成"""
        self.logger.info(f"Event export completed: {data}")

    def closeEvent(self, event):
        """关闭事件"""
        try:
            self.export_service.stop()
            self.performance_optimizer.shutdown()
            self.export_system.shutdown()
        except:
            pass
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序信息
    app.setApplicationName("CineAIStudio Export Integration Demo")
    app.setApplicationVersion("1.0.0")

    # 创建主窗口
    window = ExportIntegrationDemo()
    window.show()

    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()