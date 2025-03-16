from typing import Generic, TypeVar

from litestar.controller import Controller

from app.config import BaseConfig, Language
from app.db.enums import EnumLanguages

ConfigType = TypeVar('ConfigType', bound=BaseConfig)


class BaseController(Controller, Generic[ConfigType]):
    config: ConfigType
    path: str

    def lang_to_enumlang(self, lang: Language) -> EnumLanguages:
        try:
            return EnumLanguages(lang.value)
        except ValueError:
            return EnumLanguages.en
