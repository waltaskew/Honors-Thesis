import locale
import os
import re
from bsddb import db
from lxml import etree

# locale for unicode encoding
DEF_LOCALE = locale.getdefaultlocale()[1]
# random string to delimit posts in the DB
POST_DELIMITER = '^$~'

def strip_delimiter(text):
    """ make sure that the delimiter isn't in the post
    """
    global POST_DELIMITER
    return re.sub(POST_DELIMITER, ' ', text)

def write_posts(title, posts, out_DB):
    """write the posts into a given DB, using the title as the key in the DB
    """
    global DEF_LOCALE, POST_DELIMITER
    ## make sure we parsed a page with posts (could have been some other 
    ## forum page)
    if title and posts:
        # make sure the delimter doesn't occur in the post
        posts = [strip_delimiter(post) for post in posts]
        # turn the list of posts into a delimiated string of posts
        posts = reduce(lambda post1, post2: post1 + POST_DELIMITER + post2, posts)
        # watch out for unicode
        title, posts = title.encode(DEF_LOCALE), posts.encode(DEF_LOCALE)
        ## Either append the posts to those already gathered under the tile
        ## or create a new entry.  If two threads have the same title, they
        ## will be collapsed into one thread
        old_posts = out_DB.get(title)
        if old_posts == None:
            out_DB.put(title, posts)
        else:
            out_DB.put(title, old_posts + POST_DELIMITER + posts)

def iter_dir(dir):
    """recursively iterate through a directory, 
    yielding file names
    """
    ## maintian a stack of directories we need to visit
    dir_stack = [dir]
    while dir_stack:
        dir_name = dir_stack.pop()
        for file in os.listdir(dir_name):
            file = os.path.join(dir_name, file)
            if os.path.isfile(file):
                yield file
            elif os.path.isdir(file):
                dir_stack.append(file)

def get_phpBB_posts(corpus_dir, post_DB):
    """write posts from a corpus of phpBB html files into a berkely DB,
    indexed by post title.
    """
    from indexers import phpBB_parser
    
    out_DB = db.DB()
    out_DB.open(post_DB, None, db.DB_HASH, db.DB_CREATE | db.DB_TRUNCATE)
            
    parser = etree.HTMLParser(target = phpBB_parser.PostGetter())
    for file in iter_dir(corpus_dir):
        if ".html" in file or ".php" in file or ".htm" in file:
            with open(file, 'r') as file:
                title, posts = etree.HTML(file.read(), parser)
            write_posts(title, posts, out_DB)
    out_DB.close()

def iter_xml(corpus_dir, tag_file):
    """iterate through a corpus of XML files, yielding information
    specified by the supllied tag list.
    """
    from indexers import XML_parser
    from tag_list import TagList

    tag_list = TagList(tag_file)
    parser = etree.XMLParser(target = XML_parser.TextGetter(tag_list))
    for file_name in iter_dir(corpus_dir):
        if '.xml' in file_name:
            with open(file_name, 'r') as file:
                text_list = etree.XML(file.read(), parser)
            for title, heading, text in text_list:
                yield file_name, title, heading, text
