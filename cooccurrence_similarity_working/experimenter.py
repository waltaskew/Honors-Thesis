import os
import cPickle

import index
import get_cooccurrences
import get_PMIs
import get_relations
import get_features

INSTANCE_FILE = 'saved_experimenter_instance'

INDEX_TASK = 1
COOCCURRENCE_TASK = 2
PMI_TASK = 3
RELATION_TASK = 4
FEATURE_TASK = 5

INDEX_FILE_PATH = 1
TOTAL_WORDS_PATH = 2
TARGET_FILE_PATH = 3
SYNONYM_FILE_PATH = 4
WORD_COUNT_FILE_PATH = 5
COOCCURRENCE_FILE_PATH = 6
PMI_FILE_PATH = 7
RELATION_FILE_PATH = 8
FEATURE_FILE_PATH = 9

INDEX_FILE = 'index.txt'
TOTAL_WORD_COUNT_FILE = 'total_word_count.txt'
COOCCURRENCE_DIR_PREFIX = 'cooccurrence_window_'
WORD_COUNT_FILE = 'word_counts.db'
COOCCURRENCE_FILE = 'cooccurences.db'
PMI_DIR_PREFIX = 'pmi_threshold_'
PMI_FILE = 'pmis.db'
RELATION_DIR_PREFIX = 'relation_threshold_'
RELATION_FILE = 'relations.db'
FEATURE_DIR = 'features'
FEATURE_FILE_SUFFIX = '_feature.arff'

def _get_files(dir, experiments):
    global INDEX_TASK, COOCCURRENCE_TASK, PMI_TASK, RELATION_TASK, FEATURE_TASK
    global INDEX_FILE, COOCCURRENCE_DIR_PREFIX, WORD_COUNT_FILE, COOCCURRENCE_FILE,\
            PMI_DIR_PREFIX, PMI_FILE, RELATION_DIR_PREFIX,\
            RELATION_FILE, FEATURE_DIR, FEATURE_FILE_SUFFIX
    global INDEX_FILE_PATH, TOTAL_WORDS_PATH, TARGET_FILE_PATH,\
            SYONYM_FILE_PATH, WORD_COUNT_FILE_PATH, COOCCURRENCE_FILE_PATH,\
            PMI_FILE_PATH, RELATION_FILE_PATH, FEATURE_FILE_PATH
            
    files = {}
    index_file = os.path.join(dir, INDEX_FILE)
    files[INDEX_FILE_PATH] = index_file
    total_words_file = os.path.join(dir, TOTAL_WORD_COUNT_FILE)
    files[TOTAL_WORDS_PATH] = total_words_file
    for experiment in experiments:
        if experiment.task == COOCCURRENCE_TASK:
            target_file, synonym_file, window = experiment.args
            files[TARGET_FILE_PATH] = target_file
            files[SYNONYM_FILE_PATH] = synonym_file
            cooccurrence_dir = os.path.join(dir, "%s%s_%s_%s" % 
                    (COOCCURRENCE_DIR_PREFIX, 
                    window, 
                    str(target_file).replace('/', '_'),
                    str(synonym_file).replace('/', '_')))
            if not os.path.exists(cooccurrence_dir):
                os.mkdir(cooccurrence_dir)
            word_count_file = os.path.join(cooccurrence_dir, 
                    WORD_COUNT_FILE)
            cooccurrence_file = os.path.join(cooccurrence_dir, 
                    COOCCURRENCE_FILE)
            files[WORD_COUNT_FILE_PATH] = word_count_file
            files[COOCCURRENCE_FILE_PATH] = cooccurrence_file
        elif experiment.task == PMI_TASK:
            pmi_threshold, = experiment.args
            pmi_dir = os.path.join(cooccurrence_dir, PMI_DIR_PREFIX
                    + str(pmi_threshold))
            if not os.path.exists(pmi_dir):
                os.mkdir(pmi_dir)
            files[PMI_FILE_PATH] = os.path.join(pmi_dir, PMI_FILE)
        elif experiment.task == RELATION_TASK:
            relation_threshold, = experiment.args
            relation_dir = os.path.join(pmi_dir, RELATION_DIR_PREFIX
                    + str(relation_threshold))
            if not os.path.exists(relation_dir):
                os.mkdir(relation_dir)
            relations_file = os.path.join(relation_dir, RELATION_FILE)
            files[RELATION_FILE_PATH] = relations_file
        elif experiment.task == FEATURE_TASK:
            truth_DB, truth_function = experiment.args[:2]
            feature_dir = os.path.join(dir, FEATURE_DIR)
            if not os.path.exists(feature_dir):
                os.mkdir(feature_dir)
            files[FEATURE_FILE_PATH] = os.path.join(feature_dir, "%s_%s_%s_%s%s" % 
                    (window, pmi_threshold, relation_threshold, truth_function, FEATURE_FILE_SUFFIX))
        else:
            raise AttributeError ("invalid task %s" % experiment.task)
    return files

def _count_cooccurrences(files, target_file, synonym_file, window):
    get_cooccurrences.get_cooccurrences(files[INDEX_FILE_PATH], target_file,
            synonym_file, window, files[WORD_COUNT_FILE_PATH],
            files[COOCCURRENCE_FILE_PATH])
    
def _calculate_PMIs(files, pmi_threshold):
    get_PMIs.get_PMIs(files[WORD_COUNT_FILE_PATH], 
            files[COOCCURRENCE_FILE_PATH], pmi_threshold, 
            files[TOTAL_WORDS_PATH], files[PMI_FILE_PATH])

def _calculate_relations(files, relation_threshold):
    get_relations.get_relations(files[PMI_FILE_PATH], relation_threshold, 
        files[RELATION_FILE_PATH])

def _write_feature_files(files, truth_DB, truth_function):
    get_features.get_features(files[RELATION_FILE_PATH], 
        files[PMI_FILE_PATH], files[COOCCURRENCE_FILE_PATH],
        files[FEATURE_FILE_PATH], truth_DB, truth_function)

TASK_FUNCTIONS = {
        COOCCURRENCE_TASK: _count_cooccurrences,
        PMI_TASK: _calculate_PMIs,
        RELATION_TASK: _calculate_relations,
        FEATURE_TASK:_write_feature_files,
        }

class Experimenter(object):
    """Class which saves results of experiments and determines how
    much work needs to be done to perform a new experiment.
    """
    def __new__(cls, dir):
        ## __init__ doesn't give us enough control, so we are defining
        ## all of the class creation stuff in __new__
        global INSTANCE_FILE

        if os.path.exists(dir):
            if not os.path.isdir(dir):
                raise ValueError ("%s is not a directory" % dir)
            ## if we have been given a non-empty directory, try to 
            ## return the object pickled into that directory instead
            ## of a new instance
            elif os.listdir(dir):
                try:
                    with open(os.path.join(dir, INSTANCE_FILE), 'r') as instance_file:
                        return cPickle.load(instance_file)
                except (cPickle.UnpicklingError, IOError):
                    raise ValueError ("%s is not a directory created by an Experimenter instance" % dir)
        else:
            os.makedirs(dir)
        ## if we were given an empty directory or a non-existant path
        ## (for which we created a directory), create and return the
        ## object as normal
        obj = super(Experimenter, cls).__new__(cls)
        obj.dir = dir
        obj.instance_file = os.path.join(dir, INSTANCE_FILE)
        obj.completed_tasks = {}
        obj.index_contents = {}
        obj.save_instance()
        return obj

    def save_instance(self):
        """Pickles the instance for concurrency between experiments
        """
        with open(self.instance_file, 'w') as instance_file:
            cPickle.dump(self, instance_file)

    def add_to_index(self, corpus_dir, corpus_type,
                     stop_file=None, tag_file=None, synch_freq=10000):
        """Appends entries from @corpus_dir into the index
        """
        global INDEX_FILE, TOTAL_WORD_COUNT_FILE
        if corpus_dir not in self.index_contents:
            index_file = os.path.join(self.dir, INDEX_FILE)
            word_count_file = os.path.join(self.dir, TOTAL_WORD_COUNT_FILE)
            index.build_index(corpus_dir, corpus_type, stop_file,
                    index_file, tag_file, word_count_file, synch_freq)
            self.index_contents[corpus_dir] = (corpus_type, stop_file, tag_file)
        self.save_instance()

    def perform_experiment(self, target_file, synonym_file=None, 
                           window=float('inf'), pmi_threshold=0, 
                           relation_threshold=0, truth_DB=None, 
                           truth_function=None):
        """Performs an experiment with the requested parameters.  The
        function will reuse past experimental results if possible.
        """
        experiments = [ 
                Experiment(COOCCURRENCE_TASK, 
                    (target_file, synonym_file, window),
                    ()),
                Experiment(PMI_TASK, 
                    (pmi_threshold,), 
                    (target_file, synonym_file, window)),
                Experiment(RELATION_TASK, 
                    (relation_threshold,),
                    (target_file, synonym_file, window, pmi_threshold)),
                Experiment(FEATURE_TASK, 
                    (truth_DB, truth_function),
                    (target_file, synonym_file, window, pmi_threshold, relation_threshold)),
                ]
        files = _get_files(self.dir, experiments)
        for experiment in experiments:
            if experiment not in self.completed_tasks:
                experiment(files)
                self.completed_tasks[experiment] = True
                self.save_instance()

    def show_performed_experiments(self):
        """Print performed experiments onto STDOUT
        """
        for experiment in self.completed_tasks:
            print(experiment)

    def show_index(self):
        """Print directories added to the index onto STDOUT
        """
        for dir, options in self.index_contents.iteritems():
            print("indexed %s with options %s" % (dir, options))

class Experiment:
    """Representation of an experiment to be performed.
    """
    def __init__(self, task, args, context=()):
        global TASK_FUNCTIONS
        self.task = task
        self.args = args
        self.context = context

    def __repr__(self):
        return "task %s with arguments %s" % (self.task, self.args)

    def __call__(self, files):
        function = TASK_FUNCTIONS[self.task]
        ## the feature task needs information to distinguish itself
        ## from other feature tasks, but they are not actually used
        ## as arguments for the task
        function(files, *self.args)

    def __eq__(self, other):
        if self.task == other.task and self.args == other.args\
                and self.context == other.context:
            return True
        else:
            return False

    def __hash__(self):
        return hash(self.args + self.context + (self.task,))
