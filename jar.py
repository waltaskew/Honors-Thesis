import cPickle
import os
from normalize import normalize

def iter_docs(index_file):
    """Reads through documents which have been synchronized
    """
    with open(index_file, 'rb') as index_file:
        while True:
            try:
                yield cPickle.load(index_file)
            except EOFError:
                return

class Jar:
    """Holds statistics which can be synchronized and dumped into a
    file.  Also allows old statistic runs to be restarted.
    """
    def __init__(self, index_file, word_count_file,
                 synch_freq, stop_file):

        self.synch_freq = synch_freq
        self.docs_added = 0

        self.stop_words = {}
        if stop_file:
            with open(stop_file, 'r') as file:
                for line in file:
                    line = normalize(line.strip())
                    self.stop_words[line] = None
        
        self.index_file = index_file
        self.total_words_file = word_count_file
        self.doc_map = []

        # if we are restarting an old run, start the
        # total word count at the right number
        if os.path.isfile(self.total_words_file):
            with open(self.total_words_file, 'r') as total_words_file:
                self.total_word_count = int(total_words_file.readline()[:-1])
        else:
            self.total_word_count = 0

    def index_and_count_text(self, text):
        """Increments word count by the number of words in text and returns
        a word index of the text, in (word, word_position) pairs with
        stop words removed.
        """
        text = normalize(text).split()
        self.total_word_count += len(text)
        return [(word, word_pos) for word_pos, word in enumerate(text)
            if word not in self.stop_words]
        
    def add_doc(self, source=None, title=None, 
            meta_info=None, text=None):
        """Add a document into the jar, synching to disk if nescessary.
        """
        doc = (source, title, meta_info, text)
        self.doc_map.append(doc)
        self.docs_added += 1
        
        if self.docs_added % self.synch_freq == 0:
            self.synchronize()
            
    def synchronize(self):
        """Synchs the data structures onto disk and wipes them from memory.
        """
        with open(self.total_words_file, 'w') as total_words_file:
            total_words_file.write('%s\n' % self.total_word_count)

        with open(self.index_file, 'ab') as index_file:
            for doc in self.doc_map:
                cPickle.dump(doc, index_file)
        self.doc_map = []

    def iter_synched_docs(self):
        """Reads through documents which have been synchronized
        """
        iter_docs(self.index_file)
