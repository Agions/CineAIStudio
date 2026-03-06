#!/bin/bash
# ClipFlowCut DMG 打包脚本
# 使用方法: ./build_dmg.sh

set -e

# 配置
APP_NAME="ClipFlowCut"
APP_BUNDLE="${APP_NAME}.app"
VERSION="3.0.0"
DMG_NAME="${APP_NAME}-${VERSION}-macOS.dmg"
TEMP_DIR="/tmp/${APP_NAME}_build"
 RESOURCES_DIR="resources/icons"

echo "========================================"
echo "  ClipFlowCut DMG 打包工具"
echo "========================================"
echo ""

# 清理
echo "[1/6] 清理旧构建..."
rm -rf build dist *.app *.dmg
mkdir -p "${TEMP_DIR}"

# 检查依赖
echo "[2/6] 检查依赖..."
if ! command -v pyinstaller &> /dev/null; then
    echo "错误: PyInstaller 未安装"
    echo "请运行: pip install pyinstaller"
    exit 1
fi

if [ ! -f "${RESOURCES_DIR}/app_icon_512.png" ]; then
    echo "错误: 应用图标未找到"
    exit 1
fi

# 构建应用
echo "[3/6] 构建应用..."
pyinstaller \
    --name="${APP_NAME}" \
    --windowed \
    --onedir \
    --add-data="resources:resources" \
    --hidden-import="PyQt6.sip" \
    --hidden-import="PyQt6.QtCore" \
    --hidden-import="PyQt6.QtGui" \
    --hidden-import="PyQt6.QtWidgets" \
    --hidden-import="cryptography" \
    --hidden-import="cryptography.fernet" \
    --hidden-import="cryptography.hazmat" \
    --hidden-import="keyring" \
    --hidden-import="keyring.backends" \
    --collect-all="PyQt6" \
    --collect-all="keyring" \
    --noconfirm \
    main.py

# 创建 .app 捆绑包
echo "[4/6] 创建应用捆绑包..."
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
mkdir -p "${APP_BUNDLE}/Contents/Resources"

# 复制可执行文件
cp -r "dist/${APP_NAME}/"* "${APP_BUNDLE}/Contents/MacOS/"

# 复制资源
cp -r resources "${APP_BUNDLE}/Contents/"

# 复制图标
if [ -f "${RESOURCES_DIR}/ClipFlowCut.icns" ]; then
    cp "${RESOURCES_DIR}/ClipFlowCut.icns" "${APP_BUNDLE}/Contents/Resources/"
fi

# 创建 Info.plist
cat > "${APP_BUNDLE}/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>zh_CN</string>
    <key>CFBundleExecutable</key>
    <string>ClipFlowCut</string>
    <key>CFBundleIconFile</key>
    <string>ClipFlowCut</string>
    <key>CFBundleIdentifier</key>
    <string>com.clipflow.ClipFlowCut</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>ClipFlowCut</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>3.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2024 Agions. All rights reserved.</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# 使用 Notes 图标作为临时替代
if [ ! -f "${RESOURCES_DIR}/ClipFlowCut.icns" ]; then
    echo "警告: 未找到 ICNS 文件，将使用默认图标"
fi

# 设置权限
chmod -R a+rX "${APP_BUNDLE}"
chmod +x "${APP_BUNDLE}/Contents/MacOS/"*

# 创建 DMG
echo "[5/6] 创建 DMG..."
if command -v create-dmg &> /dev/null; then
    create-dmg \
        --volname "${APP_NAME}" \
        --volicon "${RESOURCES_DIR}/ClipFlowCut.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "${APP_BUNDLE}" 150 185 \
        --app-drop-link 450 185 \
        "${DMG_NAME}" \
        "${APP_BUNDLE}"
else
    # 使用 hdiutil 作为备选
    hdiutil create -volname "${APP_NAME}" -srcfolder "${APP_BUNDLE}" -ov -format UDZO "${DMG_NAME}"
fi

# 完成
echo "[6/6] 完成!"
echo ""
echo "========================================"
echo "  构建成功!"
echo "========================================"
echo ""
echo "输出文件:"
echo "  - ${APP_BUNDLE}"
echo "  - ${DMG_NAME}"
echo ""
echo "下一步:"
echo "  1. 检查 .app 文件是否可以正常运行"
echo "  2. 分发 .dmg 文件给用户"
echo ""
