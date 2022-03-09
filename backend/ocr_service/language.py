import string
from backend.ocr_service.config import OCR_MAX_TEXT_LENGTH
from backend.ocr_service.tokenization import Tokenizer

#LATIN_ALPHABET = {"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l",
#                  "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "x", "y", "z",
#                  "A", "B", "C", "D", "E", "F", "H", "I", "J", "K", "L", "M",
#                  "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
#                  ".", ",", " "}
#ITALIAN_ALPHABET = set(string.printable[:95])

LATIN_ALPHABET = "abcdefghijklmnopqrstuvxyzABCDEFHIJKLMNOPQRSTUVWXYZ.,' "

ITALIAN_ALPHABET = string.printable[:95]

class Language:

    def __init__(self, name, code, alphabet, description):
        self.name = name
        self.code = code
        self.alphabet = alphabet
        self.description = description
        self.tokenizer = Tokenizer(self.alphabet, OCR_MAX_TEXT_LENGTH)

    @staticmethod
    def from_name(name):
        return NAME_2_LANGUAGE[name.lower()] if name.lower() in NAME_2_LANGUAGE else ITALIAN


LATIN = Language(name="Latin",
                 code="LAT",
                 alphabet=LATIN_ALPHABET,
                 description="Medieval Latin used in Honorii III and Innocent III documents.")

ITALIAN = Language(name="Italian",
                   code="ITA",
                   alphabet=ITALIAN_ALPHABET,
                   description="Italian Language.")

NAME_2_LANGUAGE = {"italian": ITALIAN,
                   "latin": LATIN}
