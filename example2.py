from cooccurrence_similarity import experimenter

## If you have already created an index and run experiments, they will still be
## around after the program which created them exits.  Experimenter objects 
## retain consistency across multiple runs

truth='/aut/proj/ir/wsaskew/Data/thesis/truthDSM.db'
targets='/aut/proj/ir/wsaskew/Data/thesis/targetListDSM.txt'
stop_words='/aut/proj/ir/wsaskew/Data/thesis/stopWords2.txt'
corpus_dir = '/aut/proj/ir/wsaskew/Data/webcrawls/psych_forums/www.psychforums.com/'

e = experimenter.Experimenter('test_experiment')
e.perform_experiment(targets, synonym_file=None, 
                       window=50, pmi_threshold=0, 
                       relation_threshold=500, truth_DB=truth, 
                       truth_function='2_way_strong')
