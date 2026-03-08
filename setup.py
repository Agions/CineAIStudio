#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ClipFlowCut 安装配置
"""

from setuptools import setup, find_packages
from pathlib import Path


# 读取 README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""


# 读取依赖
def get_requirements():
    req_file = Path(__file__).parent / "requirements.txt"
    if req_file.exists():
        return [
            line.strip()
            for line in req_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
    return []


setup(
    name="clipflowcut",
    version="3.0.0",
    description="AI 驱动的专业视频创作桌面应用",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ClipFlowCut Team",
    author_email="team@clipflowcut.com",
    url="https://github.com/Agions/ClipFlowCut",
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    install_requires=get_requirements(),
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "clipflowcut=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Video :: Conversion",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="video ai editing editing pyqt6",
    include_package_data=True,
    zip_safe=False,
)
