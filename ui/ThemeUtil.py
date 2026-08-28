from typing import Callable

from core.Util import settings

THEME_KEY = "Theme"
DARK_THEME = "material_dark_style"
LIGHT_THEME = "material_light_style"


class ThemeUtil:
    on_theme_changed: Callable[[str], None] = None

    @classmethod
    def register_theme_changed(cls, on_theme_changed: Callable[[str], None]):
        if on_theme_changed:
            cls.on_theme_changed = on_theme_changed

    @classmethod
    def is_dark_theme(cls) -> bool:
        return cls.query_theme() == DARK_THEME

    @classmethod
    def set_dark_theme(cls, is_dark: bool):
        if is_dark == cls.is_dark_theme():
            # 主题未变化，不做任何处理
            return
        new_theme_qss_name = DARK_THEME if is_dark else LIGHT_THEME
        cls.__store_theme__(new_theme_qss_name)
        if cls.on_theme_changed:
            cls.on_theme_changed(new_theme_qss_name)

    @classmethod
    def query_theme(cls) -> str:
        return settings.value(THEME_KEY, DARK_THEME)

    @classmethod
    def __store_theme__(cls, qss_name: str):
        settings.setValue(THEME_KEY, qss_name)
