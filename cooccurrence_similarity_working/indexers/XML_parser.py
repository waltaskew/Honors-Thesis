class TextGetter:
    """keeps a list of texts parsed out via XML tags
    """
    def __init__(self, tag_list):
        self.tag_list = tag_list
        self.clear_fields()

    def clear_fields(self):
        self.title = ''
        self.heading = ''
        self.text = ''

        self.text_list = []
        self.in_tag = None

    def start(self, tag, attrib):
        if tag in self.tag_list.tags:
            self.in_tag = tag

    def end(self, tag):
        if tag == self.tag_list.title:
            self.in_tag = None
            self.title += ' '
        if tag == self.tag_list.heading:
            self.in_tag = None
            self.heading += ' '
        elif tag == self.tag_list.delimiator:
            self.in_tag = None
            group = (self.title.strip(), self.heading.strip(), self.text.strip())
            self.text_list.append(group)
            self.text = ''
            self.title = ''
            self.heading = ''
        elif tag in self.tag_list.tags:
            self.in_tag = None
            self.text += ' '

    def data(self, text):
        if self.in_tag == self.tag_list.title:
            self.title += text
        elif self.in_tag == self.tag_list.heading:
            self.heading += text
        elif self.in_tag:
            self.text += text

    def comment(self, text):
        return

    def close(self):
        text_list = self.text_list
        self.clear_fields()
        return text_list
