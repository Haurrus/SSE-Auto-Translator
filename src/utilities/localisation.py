"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import locale
import logging
from pathlib import Path

import jstyleson as json
import win32api


class LocalisationSection:
    """
    LocalisationSection class.
    """

    def __init__(self, logger: logging.Logger, name: str = None):
        self.log = logger
        self._name = name

    def __repr__(self) -> str:
        if self._name is not None:
            return self._name
        else:
            return "LocalisationSection"

    def __getattribute__(self, __name: str) -> str:
        try:
            return object.__getattribute__(self, __name)
        except AttributeError:
            self.log.warning(f"Missing localisation for {__name!r} in {self!r}!")
            return __name


class Localisator:
    """
    Localisation class.
    Manages localized strings.
    """

    # Localisation attributes
    language = "en-US"  # Default

    def __init__(self, lang: str, lang_path: Path) -> None:
        self.log = logging.getLogger(self.__repr__())

        self.language = lang
        self.lang_path = lang_path / lang

    def __repr__(self) -> str:
        return "Localisation"

    def load_lang(self) -> None:
        """
        Loads localisation for <language>.
        Falls back to "en-US" if <language> does not exist.
        """

        # Detect system language
        if self.language == "System":
            try:
                language_id = win32api.GetUserDefaultLangID()
                system_language = locale.windows_locale[language_id]
                self.log.debug(f"Detected system language: {system_language}")
                self.language = system_language
                self.lang_path = self.lang_path.parent / system_language
            except Exception as ex:
                self.log.error(f"Failed to get system language: {ex}")
                self.language = "en _US"
                self.lang_path = self.lang_path.parent / system_language

        # Fall back to english localisation
        if not self.lang_path.is_dir():
            self.log.warning(
                f"Failed to load language '{self.language}': Localisation does not exist!"
            )
            self.log.info("Falling back to 'en_US'...")
            self.language = "en_US"  # Fall back to default if lang does not exist
            self.lang_path = self.lang_path.parent / self.language

        for lang_file in self.lang_path.glob("*.json"):
            with open(lang_file, mode="r", encoding="utf8") as file:
                lang_data: dict[str, str] = json.load(file)

            # Create root attribute
            setattr(self, lang_file.stem, LocalisationSection(self.log, lang_file.name))
            root_attr = getattr(self, lang_file.stem)
            root_attr.__getattribute__ = self.__getattribute__

            for key, value in lang_data.items():
                setattr(root_attr, key, value)

    def get_available_langs(self):
        return [lang.name for lang in self.lang_path.parent.glob("??_??")]

    def __getattribute__(self, __name: str) -> LocalisationSection:
        try:
            return object.__getattribute__(self, __name)
        except AttributeError:
            self.log.warning(f"Missing localisation section for {__name!r}!")
            return LocalisationSection(self.log, __name)
