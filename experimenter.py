"""The experimenter class allows a user to generate ARFF files while varying a
number of parameters. The Experimenter class maintains consistency between uses,
and uses results from previous experiments when possible to avoid
redundant calculation.
"""

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

def _count_cooccurrences(files, target_file, synonym_file, window):
    """Function used for the cooccurrence counting task.
    """
    get_cooccurrences.get_cooccurrences(files[INDEX_FILE_PATH], target_file,
            synonym_file, window, files[WORD_COUNT_FILE_PATH],
            files[COOCCURRENCE_FILE_PATH])
    
def _calculate_PMIs(files, pmi_threshold):
    """Function used for the PMI calculation task.
    """
    get_PMIs.get_PMIs(files[WORD_COUNT_FILE_PATH], 
            files[COOCCURRENCE_FILE_PATH], pmi_threshold, 
            files[TOTAL_WORDS_PATH], files[PMI_FILE_PATH])

def _calculate_relations(files, relation_threshold):
    """Function used for the relation calculation task.
    """
    get_relations.get_relations(files[PMI_FILE_PATH], relation_threshold, 
        files[RELATION_FILE_PATH])

def _write_feature_files(files, truth_db, truth_function):
    """Function used to output a feature file for use in WEKA.
    """
    get_features.get_features(files[RELATION_FILE_PATH], 
        files[PMI_FILE_PATH], files[COOCCURRENCE_FILE_PATH],
        files[FEATURE_FILE_PATH], truth_db, truth_function)

TASK_FUNCTIONS = {
        COOCCURRENCE_TASK: _count_cooccurrences,
        PMI_TASK: _calculate_PMIs,
        RELATION_TASK: _calculate_relations,
        FEATURE_TASK: _write_feature_files,
        }

class Experimenter(object):
    """Class which saves results of experiments and determines how
    much work needs to be done to perform a new experiment.
    """
    def __new__(cls, directory):
        ## __init__ doesn't give us enough control, so we are defining
        ## all of the class creation stuff in __new__
        if os.path.exists(directory):
            if not os.path.isdir(directory):
                raise ValueError ("%s is not a directory" % directory)
            ## if we have been given a non-empty directory, try to 
            ## return the object pickled into that directory instead
            ## of a new instance
            elif os.listdir(directory):
                try:
                    with open(os.path.join(
                        directory, INSTANCE_FILE), 'r') as instance_file:
                        return cPickle.load(instance_file)
                except (cPickle.UnpicklingError, IOError):
                    raise ValueError("%s is not a directory created by an "
                                     "Experimenter instance" % directory)
        else:
            os.makedirs(directory)
        ## if we were given an empty directory or a non-existant path
        ## (for which we created a directory), create and return the
        ## object as normal
        obj = super(Experimenter, cls).__new__(cls)
        obj.directory = directory
        obj.instance_file = os.path.join(directory, INSTANCE_FILE)
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
        corpus_name = os.path.basename(os.path.normpath(corpus_dir))
        if corpus_name not in self.index_contents:
            index_file = os.path.join(self.directory, 'index.txt')
            word_count_file = os.path.join(
                self.directory, 'total_word_count.txt')
            index.build_index(corpus_dir, corpus_type, stop_file,
                    index_file, tag_file, word_count_file, synch_freq)
            value = (corpus_type, stop_file, tag_file)
            self.index_contents[corpus_name] = value
        self.save_instance()

    def get_files(self, target_file, synonym_file, window, pmi_threshold,
            relation_threshold, truth_db, truth_function):
        """Calculate the name of various intermediate files based on the
        arguments passed to perform_experiment.
        """
        files = {}
        experiment_dir = os.path.join(self.directory, 'experiment_results')
        feature_dir = os.path.join(self.directory, 'features')

        index_file = os.path.join(self.directory, 'index.txt')
        files[INDEX_FILE_PATH] = index_file
        total_words_file = os.path.join(self.directory, 'total_word_count.txt')

        files[TOTAL_WORDS_PATH] = total_words_file
        files[TARGET_FILE_PATH] = target_file
        files[SYNONYM_FILE_PATH] = synonym_file

        target_file = os.path.basename(os.path.normpath(str(target_file)))
        synonym_file = os.path.basename(os.path.normpath(str(synonym_file)))

        cooccurrence_dir = os.path.join(experiment_dir, 
                "%s_%s" % (target_file, synonym_file),
                "%s_cooccurrence_window" % window)
        files[WORD_COUNT_FILE_PATH] = os.path.join(cooccurrence_dir,
                "word_count.db")
        files[COOCCURRENCE_FILE_PATH] = os.path.join(cooccurrence_dir,
                "cooccurrences.db")

        pmi_dir = os.path.join(cooccurrence_dir, 
                "%s_pmi_threshold" % pmi_threshold)
        files[PMI_FILE_PATH] = os.path.join(pmi_dir, "pmis.db")

        relation_dir = os.path.join(pmi_dir, "%s_relation_threshold")
        files[RELATION_FILE_PATH] = os.path.join(relation_dir, "relations.db")

        feature_file_dir = os.path.join(feature_dir, 
                                        "%s_%s" % (target_file, synonym_file),
                                        str(truth_function))
        files[FEATURE_FILE_PATH] = os.path.join(feature_file_dir,
                "%s_%s_%s_features.arff" %
                (window, pmi_threshold, relation_threshold))

        # create directories for the files we want to create
        for _, file_name in files.iteritems():
            if file_name:
                directory = os.path.dirname(file_name)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)

        return files

    def perform_experiment(self, target_file, synonym_file=None, 
                           window=float('inf'), pmi_threshold=0, 
                           relation_threshold=0, truth_db=None, 
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
                    (truth_db, truth_function),
                    (target_file, synonym_file, window, pmi_threshold,
                     relation_threshold)),
                ]
        files = self.get_files(target_file, synonym_file, window, pmi_threshold,
                relation_threshold, truth_db, truth_function)
        for experiment in experiments:
            if experiment not in self.completed_tasks:
                experiment(files)
                self.completed_tasks[experiment] = None
                self.save_instance()

    def show_performed_experiments(self):
        """Print performed experiments onto STDOUT
        """
        for experiment in self.completed_tasks:
            print(experiment)

    def show_index(self):
        """Print directories added to the index onto STDOUT
        """
        for directory, options in self.index_contents.iteritems():
            print("indexed %s with options %s" % (directory, options))

class Experiment:
    """Representation of an experiment to be performed.
    """
    def __init__(self, task, args, context=()):
        self.task = task
        self.args = args
        self.context = context

    def __repr__(self):
        return("task %s\nwith arguments %s\nin context %s"
                % (self.task, self.args, self.context))

    def __call__(self, files):
        function = TASK_FUNCTIONS[self.task]
        function(files, *self.args)

    def __eq__(self, other):
        if self.task == other.task and self.args == other.args\
                and self.context == other.context:
            return True
        else:
            return False

    def __hash__(self):
        return hash(self.args + self.context + (self.task,))
