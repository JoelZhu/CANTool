rm -rf dist
pyinstaller --add-data "ui/material_style.qss:ui" \
            --add-data "app_icon.ico:." \
            Main.py --windowed