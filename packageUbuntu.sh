rm -rf dist
pyinstaller --add-data "resources/styles/material_base.qss:resources/styles" \
            --add-data "resources/styles/material_dark_style.qss:resources/styles" \
            --add-data "resources/styles/material_light_style.qss:resources/styles" \
            --add-data "resources/languages/en_US.qm:resources/languages" \
            --add-data "resources/languages/zh_CN.qm:resources/languages" \
            --add-data "resources/fonts/selawk.ttf:resources/fonts" \
            --add-data "app_icon.ico:." \
            Main.py --windowed