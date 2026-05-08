from tree_sitter_languages import get_parser

from backend.app.core.logger import get_logger

logger = get_logger()

class ParserManager:
    """
        Class to add global parsers registry for all languages
    """

    def __init__(self):
        self.parsers = {}

    def get_language_parser(self, language: str):
        """
            Returns a parser of given language stored in global registry
            Input: language (str)
            Output: Parser of given language
        """
        
        logger.debug(f"Fetching {language}'s parser")

        if language not in self.parsers:
            self.parsers[language] = get_parser(language)
        
        return self.parsers[language]