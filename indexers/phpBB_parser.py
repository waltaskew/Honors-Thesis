### example title:
#start a {'href': 'viewtopic40e7.html?t=6410&start=0&postdays=0&postorder=asc&highlight=', 'class': 'maintitle'}
#data u"munchausen's vs factitious disorder?"
#end a

###example post:
#start span {'class': 'postbody'}
#data u'Thanks, Ddee - I am still a bit confused but what else is new???\r\n'
#start br {}
#end br
#data u'\n\r\n'
#start br {}
#end br
#data u'\nIs Munchausen\'s really as rare as I\'ve read? Is it more rare than Munchausen\'s by Proxy? Or is it that people are so ashamed of the dx? Judging by the amount of posts on this board, it doesn\'t seem that many people have it or are willing to admit it. I can admit it here - but anonymously, not in my "real" life.'
#end span

class PostGetter:
    """get the title of a page and the posts on it
    """
    def __init__(self):
        self.clear_fields()

    def clear_fields(self):
        """clean up the class instance for repeated use by the parser
        """
        self.title = ''
        self.in_title = False

        self.span_count = 0 # for keeping track of nested div tags in the post
        self.post = '' # the post we are in right now
        self.all_posts = [] # all of the posts on the page
        self.in_post = False

    def start(self, tag, attrib):
        """decide if the parser is inside a post, a title, or nothing at all
        """
        if tag == 'span':
            ## keep track of nested div tags inside of a post, so we don't
            ## leave on the wrong </div>
            if self.in_post:
                self.span_count += 1
            elif attrib.get('class') == 'postbody':
                self.in_post = True
                self.span_count = 1
        elif tag == 'a' and attrib.get('class') == 'maintitle':
            self.in_title = True

    def end(self, tag):
        """decide if the parser has reached the end of a post or title
        """
        if self.in_post and tag == 'span':
            self.span_count -= 1
            if self.span_count <= 0:
                ## append the post we just found into a list and get
                ## ready for the next post on the page
                self.all_posts.append(self.post.strip())
                self.post = ''
                self.in_post = False
        elif self.in_title and tag == 'a':
            self.title = self.title.strip()
            self.in_title = False

    def data(self, data):
        """accumulate the post and title text
        """
        if self.in_post:
            self.post += data
        elif self.in_title:
            self.title += data

    def comment(self, text):
        """do nothing on comments
        """
        return

    def close(self):
        """Get the class instance ready for the next file to parse.
        Return the tile and the posts from the file we just finished parsing.
        """
        all_posts = self.all_posts
        title = self.title
        self.clear_fields()
        return title, all_posts
