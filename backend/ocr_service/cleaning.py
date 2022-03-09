"""
The cleaning module and its Cleaner objects, so far, are only used in dataset creation:
when we analyze a transcribed set of line images, before converting them into a ready-to-use HDF5 dataset,
we clean the transcriptions and check if they have become acceptable.

"Cleaning" a transcription usually boils down to:
    - translating characters that do not belong to the alphabet in acceptable forms:
        e.g., "à" can be translated to "a'"
    - removing characters that do not belong to the alphabet and that we do not want to keep:
        e.g., "§" will be just erased
"""

import html
import string
import re

# DeepSpell based text cleaning process (Tal Weiss. Deep Spelling.)
#   As seen in Medium: https://machinelearnings.co/deep-spelling-9ffef96a24f6#.2c9pu8nlm
#   and Github: https://github.com/MajorTal/DeepSpell
from backend.ocr_service.language import LATIN_ALPHABET, ITALIAN_ALPHABET

RE_DASH_FILTER = re.compile(r'[\-\˗\֊\‐\‑\‒\–\—\⁻\₋\−\﹣\－]', re.UNICODE)
RE_APOSTROPHE_FILTER = re.compile(r'&#39;|[ʼ՚＇‘’‛❛❜ߴߵ`‵´ˊˋ{}{}{}{}{}{}{}{}{}]'.format(
    chr(768), chr(769), chr(832), chr(833), chr(2387),
    chr(5151), chr(5152), chr(65344), chr(8242)), re.UNICODE)
RE_RESERVED_CHAR_FILTER = re.compile(r'[¶¤«»]', re.UNICODE)
RE_LEFT_PARENTH_FILTER = re.compile(r'[\(\[\{\⁽\₍\❨\❪\﹙\（]', re.UNICODE)
RE_RIGHT_PARENTH_FILTER = re.compile(r'[\)\]\}\⁾\₎\❩\❫\﹚\）]', re.UNICODE)
RE_BASIC_CLEANER = re.compile(r'[^\w\s{}]'.format(re.escape(string.punctuation)), re.UNICODE)

LEFT_PUNCTUATION_FILTER = """!%&),.:;<=>?@\\]^_`|}~"""
RIGHT_PUNCTUATION_FILTER = """"(/<=>@[\\^_`{|~"""
NORMALIZE_WHITESPACE_REGEX = re.compile(r'[^\S\n]+', re.UNICODE)


class Cleaner:
    def __init__(self, alphabet, tokenizer):
        self.alphabet = {c for c in alphabet}
        self.tokenizer = tokenizer

    def clean(self, transcription):
        pass

    def is_acceptable(self, text):
        """
        This method checks if the text is acceptable;
        if it does, it returns True, otherwise it returns False
        """

        # right now, this method only makes sure that the text has any characters other than punctuation marks
        original_text = text

        if text is None:
            return False

        text = html.unescape(text).replace("\\n", "").replace("\\t", "")

        text = RE_RESERVED_CHAR_FILTER.sub("", text)
        text = RE_DASH_FILTER.sub("-", text)
        text = RE_APOSTROPHE_FILTER.sub("'", text)
        text = RE_LEFT_PARENTH_FILTER.sub("(", text)
        text = RE_RIGHT_PARENTH_FILTER.sub(")", text)
        text = RE_BASIC_CLEANER.sub("", text)

        text = text.lstrip(LEFT_PUNCTUATION_FILTER)
        text = text.rstrip(RIGHT_PUNCTUATION_FILTER)
        text = text.translate(str.maketrans({c: f" {c} " for c in string.punctuation}))
        text = NORMALIZE_WHITESPACE_REGEX.sub(" ", text.strip())

        strip_punc = text.strip(string.punctuation).strip()
        no_punc = text.translate(str.maketrans("", "", string.punctuation)).strip()
        length_valid = (len(text) > 0) and (len(text) < self.tokenizer.maxlen)
        text_valid = (len(strip_punc) > 1) or (len(no_punc) > 1)

        return length_valid and text_valid and len(self.tokenizer.encode(original_text)) > 0

    @staticmethod
    def for_language(language):
        if language.name == "Latin":
            return LatinCleaner(language.tokenizer)
        else:
            return ItalianCleaner(language.tokenizer)


class LatinCleaner(Cleaner):

    def __init__(self, tokenizer):
        super().__init__(LATIN_ALPHABET, tokenizer)

    def clean(self, transcription):

        # remove all text between square brackets or curly brackets
        transcription = re.sub("\{.*?\}", "", transcription)
        transcription = re.sub("\[.*?\]", "", transcription)

        # filter away all characters not in the alphabet
        output = []
        for c in transcription:
            if c in self.alphabet:
                output.append(c)
        return "".join(output)

        # not needed since "'", "(", ")" and "-" are absent from the alphabet
        # transcription = transcription.replace("'", "").replace("-", "")
        # transcription = transcription.replace("(", "").replace(")", "")


class ItalianCleaner(Cleaner):

    def __init__(self, tokenizer):
        super().__init__(ITALIAN_ALPHABET, tokenizer)

        # in this map we store the characters that may be present in a transcription
        # but absent in the alphabet to use for that transcription.
        # we report for each of those characters the way to represent it.
        self.translation_matrix = {'°': "'",
                                   'à': "a'", 'á': "a'", 'â': "a'",
                                   'è': "e'", 'é': "e'", 'ê': "e'", 'ë': "e'",
                                   'ì': 'i', "i'": "i'", 'î': "i'", 'ï': "i'",
                                   'ò': "o'", 'ó': "o'", 'ô': "o'",
                                   'ù': "u'", 'ú': "u'", 'û': "u'",
                                   'À': "A'", 'Á': "A'", 'Â': "A'",
                                   'È': "E'", 'É': "E'", 'Ê': "E'", 'Ë': "E'",
                                   'Ì': "I'", 'Í': "I'", 'Î': "I'", 'Ï': "I'",
                                   'Ò': "O'", 'Ó': "O'", 'Ô': "O'",
                                   'Ù': "U'", 'Ú': "U'", 'Û': "U'",
                                   'ç': 'c', 'Ç': 'C',
                                   '£': 'L', '€': 'E', '¥': 'Y', '¢': 'c', '฿': 'B'}

    def clean(self, transcription: str):

        transcription = transcription.translate(self.translation_matrix)
        filter(self.alphabet.__contains__, transcription)

        return transcription
