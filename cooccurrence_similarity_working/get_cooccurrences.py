from bsddb import db
import jar
import locale
from normalize import normalize

DEF_LOCALE = locale.getdefaultlocale()[1]
SYNCH_FREQ = 10000

def get_targets_from_file(target_file):
    """Return a dictionary of targets from a given file.
    """
    targets = {}
    with open(target_file, 'r') as file:
        for line in file:
            line = normalize(line.strip())
            #use a value-less hash table for constant time lookups
            targets[line] = None 
    return targets

def get_synonyms_from_file(synonym_file):
    """Return a dictionary of synonyms from a given file.
    """
    synonyms = {}
    if synonym_file:
        with open(synonym_file, 'r') as file:
            for line_num, line in enumurate(file):
                line = line.strip()
                try:
                    synonym, target = line.split(':')
                ## a value error means there was no ':' 
                ## or there nothing on the other side of the ':'
                except ValueError: 
                    raise AttributeError ("Formatting Error on line %d\n\
                            Lines Should be in the format 'synonym:target'"
                            % line_num + 1)
                synonyms[normalize(synonym)] = normalize(target)

    return synonyms

def set_window(window):
    """Sets the window for LimitQueue and CooccurrenceLimiter classes.
    """
    LimitQueue.set_window(window)
    CooccurrenceLimiter.set_window(window)

class LimitQueue:
    """A FIFO that holds words which are no more than @windows words apart.
    """
    @classmethod
    def set_window(cls, window):
        cls.window = window

    def __init__(self):
        ## self.window needs to be set before hand to an appropriate value 
        ## with a LimitQueue.set_window(n) call
        self.queue = []
    
    def push(self, indexed_word):
        """Push the new word onto the queue and delete any words nescessary
        to stay within the limit queue's window."""
        word, word_pos = indexed_word
        self.queue.append(indexed_word)

        head_word, head_word_pos = self.queue[0]
        room_left = self.window - (word_pos - head_word_pos)
        while room_left <= 0:
            old_head_word, old_head_num = self.queue.pop(0)
            head_word, head_word_pos = self.queue[0]
            room_left += (head_word_pos - old_head_num)

class CooccurrenceLimiter:
    """Ensures that only words within @windows are counted as cooccurrences
    with a target word.
    """
    @classmethod
    def set_window(cls, window):
        cls.window = window

    def __init__(self):
        self.targets = {}

    def place_target_in_window(self, indexed_target):
        """Ensures that the next words within @window
        will be counted as cooccurrences with the given targe.
        """
        ## This will be called each time a target is found in the
        ## text, so a dictionary is useful to easily keep many
        ## of the same targets from showing up in our list of
        ## targets in the window.
        target_word, target_pos = indexed_target
        self.targets[target_word] = target_pos

    def get_targets_in_window(self, indexed_word):
        """Returns a list of words that are within @window words
        of the given word.
        """
        word, word_pos = indexed_word
        targets_in_window = []
        for target_word, target_pos in self.targets.items():
            if self.window - (word_pos - target_pos) <= 0:
                # target is no longer within the current window
                del self.targets[target_word]
            else:
                targets_in_window.append(target_word)
        return targets_in_window

def iter_unseparated_words(text):
    """Yields lists of words which are not separated by a stop word.
    """
    current_phrase = [text[0]]
    prievious_word_pos = text[0][1]

    for indexed_word in text[1:]:
        word, word_pos = indexed_word
        ## if the difference between the word_pos is greater
        ## than 1, that means there was a stop word between 
        ## them which was removed in the index building stage
        if word_pos - prievious_word_pos == 1:
            current_phrase.append(indexed_word)
        else:
            yield current_phrase
            current_phrase = [indexed_word]
        prievious_word_pos = word_pos
    yield current_phrase

def replace_synonyms(phrase, synonyms, targets):
    """Takes a phrase and performs a greedy search for increasingly shorter
    sub-phrases of it in the synonym and target hash tables.
    """
    phrase_length = len(phrase)
    def search_phrase(left_bound):
        for right_bound in range(phrase_length, left_bound, -1):
            phrase_seg = ' '.join(word for word, word_pos in phrase[left_bound: right_bound])
            if phrase_seg in synonyms:
                phrase_seg = synonyms[phrase_seg]
            elif phrase_seg in targets:
                break
        return (phrase_seg, left_bound), right_bound

    replaced_phrase = []
    left_bound = 0
    while left_bound < len(phrase):
        phrase_seg, left_bound = search_phrase(left_bound)
        replaced_phrase.append(phrase_seg)

    return replaced_phrase

def add_word_count(word, word_counts):
    """Keeps track of how many times a word has occurred.
    """
    try:
        word_counts[word] += 1
    except KeyError:
        word_counts[word] = 1

def add_cooccurrence_count(target, word, cooccurrence_counts):
    """Keeps track of how many times a word has cooccurred with a target.
    """
    # don't count a word as cooccurring with itself
    if target != word:
        try:
            cooccurrence_counts[(target, word)] += 1
        except KeyError:
            try:
                cooccurrence_counts[(word, target)] += 1
            except KeyError:
                cooccurrence_counts[(target, word)] = 1

def get_counts(text, synonyms, targets, word_counts, cooccurrence_counts):
    """Get word counts and cooccurrences counts in a piece of text.
    """
    limit_queue = LimitQueue()
    cooccurrence_limiter = CooccurrenceLimiter()

    for unseparated_words in iter_unseparated_words(text):
        unseparated_words = replace_synonyms(unseparated_words, synonyms, targets)
        for indexed_word in unseparated_words:
            word, word_pos = indexed_word
            add_word_count(word, word_counts)
            for target in cooccurrence_limiter.get_targets_in_window(indexed_word):
                add_cooccurrence_count(target, word, cooccurrence_counts)
            if word in targets:
                for cooccurrence_word, cooccurrence_word_pos in limit_queue.queue:
                    add_cooccurrence_count(word, cooccurrence_word, 
                            cooccurrence_counts)
                cooccurrence_limiter.place_target_in_window(indexed_word)
            limit_queue.push(indexed_word)

def synchronize(word_counts, cooccurrence_counts,
        word_counts_db_file, cooccurrence_counts_db_file):
    """Write structures to disk before clearing their contents from memory.
    """
    global DEF_LOCALE
    word_counts_db = db.DB()
    word_counts_db.open(word_counts_db_file, None, 
                db.DB_HASH, db.DB_CREATE)
    for word, count in word_counts.iteritems():
        word = word.encode(DEF_LOCALE)
        old_val = word_counts_db.get(word)
        try:
            new_val = int(old_val) + count
            word_counts_db.put(word, str(new_val))
        ## if the key was not found in the database, db.get(word)
        ## will return None, which will raise a TypeError when we
        ## try to add an int to None
        except TypeError:
            word_counts_db.put(word, str(count))
    word_counts_db.close()
    word_counts.clear()

    cooccurrence_counts_db = db.DB()
    cooccurrence_counts_db.open(cooccurrence_counts_db_file, None, 
                db.DB_HASH, db.DB_CREATE)
    for (target, word), count in cooccurrence_counts.iteritems():
        ## Try to find both (target, word) and (word, target) in the
        ## db. This is important if word is itself a target, that is,
        ## two targets cooccurr with each other, because an earlier
        ## pass could have placed the cooccurrence pair a different
        ## order than we have now
        target, word = target.encode(DEF_LOCALE), word.encode(DEF_LOCALE)
        key_1 = "%s,%s" % (target, word)
        old_val_1 = cooccurrence_counts_db.get(key_1)
        try:
            new_val_1 = int(old_val_1) + count
            cooccurrence_counts_db.put(key_1, str(new_val_1))
        except TypeError:
            key_2 = "%s,%s" % (word, target)
            old_val_2 = cooccurrence_counts_db.get(key_2)
            try:
                new_val_2 = int(old_val_2) + count
                cooccurrence_counts_db.put(key_2, str(new_val_2))
            except TypeError:
                cooccurrence_counts_db.put(key_1, str(count))
    cooccurrence_counts_db.close()
    cooccurrence_counts.clear()

def get_cooccurrences(index_file, target_file, synonym_file, 
        window, word_counts_db, cooccurrence_counts_db):
    """Place cooccurrence counts into a berkely db for a given
    index, given a list of targets to count cooccurrences for
    """
    global SYNCH_FREQ
    targets = get_targets_from_file(target_file)
    synonyms = get_synonyms_from_file(synonym_file)
    set_window(window)

    word_counts = {}
    cooccurrence_counts = {}

    for index, (source, title, meta_info, text) in enumerate(jar.iter_docs(index_file)):
        if title:
            get_counts(title, synonyms, targets, word_counts, cooccurrence_counts)
        if meta_info:
            get_counts(meta_info, synonyms, targets, word_counts, cooccurrence_counts)
        if text:
            get_counts(text, synonyms, targets, word_counts, cooccurrence_counts)
        if index % SYNCH_FREQ == 0:
            synchronize(word_counts, cooccurrence_counts, word_counts_db,
                    cooccurrence_counts_db)

    synchronize(word_counts, cooccurrence_counts, word_counts_db,
            cooccurrence_counts_db)
