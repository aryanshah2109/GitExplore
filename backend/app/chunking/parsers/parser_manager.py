"""Cache Tree-sitter parsers so repeated parsing stays cheap."""

from tree_sitter_languages import get_parser

from backend.app.core.logger import get_logger


logger = get_logger()


class ParserManager:
    """Keep one Tree-sitter parser per language in memory."""

    _parsers = {}

    @classmethod
    def get_parser(
        cls,
        language: str
    ):
        """Return a cached parser for the requested language."""

        logger.debug(
            f"Fetching parser for: {language}"
        )

        if language not in cls._parsers:

            logger.debug(
                f"Creating new parser for: {language}"
            )

            cls._parsers[language] = (
                get_parser(language)
            )

        return cls._parsers[language]
