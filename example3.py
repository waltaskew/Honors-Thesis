from cooccurrence_similarity_working import experimenter

truth='/aut/proj/ir/wsaskew/Data/thesis/truthDSM.db'
targets='/aut/proj/ir/wsaskew/Data/thesis/targetListDSM.txt'
stop_words='/aut/proj/ir/wsaskew/Data/thesis/stopWords2.txt'
corpus_dir = '/aut/proj/ir/wsaskew/System/pythonpath/cooccurrence_similarity_working/test_xml_corpus'
tag_file='/aut/proj/ir/wsaskew/Data/thesis/medline_tag_list.txt'

e = experimenter.Experimenter('test_experiment_2')
e.add_to_index(corpus_dir, 'xml', stop_file=stop_words, 
        tag_file=tag_file, synch_freq=10000)
               

e.perform_experiment(targets, synonym_file=None, 
                       window=50, pmi_threshold=0, 
                       relation_threshold=0, truth_DB=truth, 
                       truth_function='2_way_mild')
e.perform_experiment(targets, synonym_file=None, 
                       window=50, pmi_threshold=50, 
                       relation_threshold=0, truth_DB=truth, 
                       truth_function='2_way_mild')
