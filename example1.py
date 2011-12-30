from cooccurrence_similarity import experimenter

truth='/aut/proj/ir/wsaskew/Data/thesis/truthDSM.db'
targets='/aut/proj/ir/wsaskew/Data/thesis/targetListDSM.txt'
stop_words='/aut/proj/ir/wsaskew/Data/thesis/stopWords2.txt'
corpus_dir = '/aut/proj/ir/wsaskew/Data/webcrawls/psych_forums/www.psychforums.com/'

e = experimenter.Experimenter('test_experiment')
e.add_to_index(corpus_dir, 'phpBB',
               stop_file=stop_words, synch_freq=10000)

e.perform_experiment(targets, synonym_file=None, 
                       window=50, pmi_threshold=0, 
                       relation_threshold=0, truth_DB=truth, 
                       truth_function='2_way_mild')
e.perform_experiment(targets, synonym_file=None, 
                       window=50, pmi_threshold=0, 
                       relation_threshold=0, truth_DB=truth, 
                       truth_function='2_way_strong')
