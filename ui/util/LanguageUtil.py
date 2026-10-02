from enum import Enum
from typing import Callable

from core.Util import settings

LANGUAGE_KEY = "Language"


class Language(Enum):
    ENGLISH = "en_US"
    CHINESE = "zh_CN"


class LanguageUtil:
    on_language_changed: Callable[[str], None] = None

    @classmethod
    def register_language_changed(cls, on_language_changed: Callable[[str], None]):
        if on_language_changed:
            cls.on_language_changed = on_language_changed

    @classmethod
    def store_language(cls, language_type: Language):
        if cls.get_language() == language_type:
            # 语言未变化，不做任何处理
            return

        settings.setValue(LANGUAGE_KEY, language_type.value)
        if cls.on_language_changed:
            cls.on_language_changed(language_type.value)

    @classmethod
    def get_language(cls) -> Language:
        language_code = settings.value(LANGUAGE_KEY, Language.ENGLISH.value)
        try:
            return Language(language_code)
        except ValueError:
            # 默认使用 ENGLISH
            return Language.ENGLISH
