@echo off
chcp 65001 >nul

echo 正在拉取最新代码...
git checkout .
git pull

echo.
echo 正在准备打包环境...
set "folder_to_delete=dist"
if exist "%folder_to_delete%" (
    echo 正在清理打包环境...
    rd /s /q "%folder_to_delete%"
    echo 打包环境清理完成
)

echo.
echo 正在打包...
".venv\Scripts\pyinstaller.exe" --add-data "ui/material_dark_style.qss;ui" ^
                                --add-data "ui/material_light_style.qss;ui" ^
                                --add-data "app_icon.ico;." ^
                                Main.py --windowed

echo.
echo 打包完成

@pause