from bsddb import db
import math

def get_PMIs(word_counts_db_file, cooccurrence_counts_db_file,
        cooccurrence_threshold, total_words_file, pmi_db_file):
    with open(total_words_file, 'r') as total_words_file:
        total_word_count = float(total_words_file.readline()[:-1]) # to force precise division

    word_counts_db = db.DB()
    word_counts_db.open(word_counts_db_file, None, db.DB_HASH, db.DB_RDONLY)

    cooccurrence_counts_db = db.DB()
    cooccurrence_counts_db.open(cooccurrence_counts_db_file, None, db.DB_HASH, db.DB_RDONLY)
    cursor = cooccurrence_counts_db.cursor()
    record = cursor.first()

    pmi_db = db.DB()
    pmi_db.open(pmi_db_file, None, db.DB_HASH, db.DB_CREATE | db.DB_TRUNCATE)

    while record:
        key, cooccurrence_count = record
        target, word = key.split(',')
        cooccurrence_count = float(cooccurrence_count) # to force precise division

        if cooccurrence_count > cooccurrence_threshold:
            prob_word = float(word_counts_db.get(word)) / total_word_count
            prob_target = float(word_counts_db.get(target)) / total_word_count
            prob_cooccurrence = cooccurrence_count / total_word_count

            pmi = math.log(prob_cooccurrence, 2) - math.log(prob_target, 2) - math.log(prob_word, 2)
            pmi_db.put(key, str(pmi))

        record = cursor.next()

    word_counts_db.close()
    cooccurrence_counts_db.close()
    pmi_db.close()
