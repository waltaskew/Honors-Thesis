import locale
import re

TAG_RE = re.compile('<.*?>')
FORMATTING_CHARS_RE = re.compile('[\n\t\r]')
DEF_LOCALE = locale.getdefaultlocale()[1]
PUNCTUATION_RE= re.compile('[!"#$%&\'()*+,./:;<=>?@[\]^_`{|}~]')

def normalize(text):
    """Removes xml/html tags and punctuation.
    """
    global DEF_LOCALE, TAG_RE, FORMATTING_CHARS_RE, PUNCTUTATION_RE

    text = TAG_RE.sub('', text)
    text = FORMATTING_CHARS_RE.sub(' ', text)
    text = PUNCTUATION_RE.sub(' ', text)

    text = text.lower()

    return text
