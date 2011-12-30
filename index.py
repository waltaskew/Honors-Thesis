from bsddb import db
import read_corpora
import jar
import locale
import os

DEF_LOCALE = locale.getdefaultlocale()[1]

def iter_indexed_posts(post_db_file, post_delimiter, jar):
    global DEF_LOCALE
    post_db = db.DB()
    post_db.open(post_db_file, None, db.DB_HASH, db.DB_RDONLY)
    cursor = post_db.cursor()
    record = cursor.first()
    while record:
        title, posts = record
        title, posts = title.decode(DEF_LOCALE), posts.decode(DEF_LOCALE)
        title = jar.index_and_count_text(title)
        for post in posts.split(post_delimiter):
            yield title, jar.index_and_count_text(post)
            record = cursor.next()
    post_db.close()
    os.remove(post_db_file)

def build_index(corpus_dir, corpus_type, stop_file, index_file, 
                tag_file, word_count_file, synch_freq):
    index_jar = jar.Jar(index_file, word_count_file, synch_freq, stop_file)

    if corpus_type == "phpBB":
        post_db = corpus_dir + ".db"
        read_corpora.get_phpBB_posts(corpus_dir, post_db)
        for title, post in iter_indexed_posts(post_db, 
                read_corpora.POST_DELIMITER, index_jar):
            index_jar.add_doc(source=corpus_dir, title=title, text=post)
    elif corpus_type == "xml":
        if not tag_file:
            raise AttributeError (
                    "a tag file must be supplied when parsing an xml corpus")

        for file_name, title, heading, text in read_corpora.iter_xml(corpus_dir, tag_file):
            title = index_jar.index_and_count_text(title)
            heading = index_jar.index_and_count_text(heading)
            text = index_jar.index_and_count_text(text)
            index_jar.add_doc(file_name, title, heading, text)
    else:
        raise AttributeError ("invalid corpus type %s\n\
                must be one of phpBB or xml" % corpus_type)
    
    #one final synch and then we are done
    index_jar.synchronize()
