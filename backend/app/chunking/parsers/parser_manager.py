from tree_sitter_languages import get_parser

from backend.app.core.logger import get_logger


logger = get_logger()


class ParserManager:
    """
    Global Tree-sitter parser cache.
    """

    _parsers = {}

    @classmethod
    def get_parser(
        cls,
        language: str
    ):
        """
        Returns cached Tree-sitter parser.

        Input:
            language: str

        Output:
            Parser
        """

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