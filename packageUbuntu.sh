rm -rf dist
pyinstaller --add-data "ui/material_dark_style.qss:ui" \
            --add-data "ui/material_light_style.qss:ui" \
            --add-data "app_icon.ico:." \
            Main.py --windowed