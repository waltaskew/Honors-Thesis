class TagList:
    """tag_file is a file containing the XML tags that
    hold the text to be indexed.  The file may also
    specify a delimiator (separates one file into 
    multiple documents) and/or a title flag
    """
    def __init__(self, tag_file):
        self.tags = {}
        self.title = None
        self.heading = None
        self.delimiator = None

        with open(tag_file, 'r') as file:
            for line in file:
                line = line.strip() #remove leading & trailing whitespace and \n
                if 'DelimiatorTag:' in line:
                    line = line.split()
                    self.delimiator = " ".join(line[1:])
                elif 'TitleTag:' in line:
                    line = line.split()
                    self.title = " ".join(line[1:])
                    self.tags[self.title] = None
                elif 'HeadingTag:' in line:
                    line = line.split()
                    self.heading = " ".join(line[1:])
                    self.tags[self.heading] = None
                else:
                    self.tags[line] = None
