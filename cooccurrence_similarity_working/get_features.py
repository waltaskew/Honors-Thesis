import arff
from bsddb import db

def five_way(pearson):
    if pearson > .3: # high correlation
        return "STRONG_POS"
    elif pearson > .1 and pearson < .3: # mild correlation
        return "MILD_POS"
    elif pearson < -.3: # high negative correlation
        return "STRONG_NEG"
    elif pearson < -.1 and pearson > -.3: # mild negative correlation
        return "MILD_NEG"
    else: # no correlation
        return "NONE"

def three_way_strong(pearson):
    if pearson > .3: # high correlation
        return "STRONG_POS"
    elif pearson < -.3: # high negative correlation
        return "STRONG_NEG"
    else: # no correlation
        return "NONE"

def three_way_mild(pearson):
    if pearson > .1: # mild correlation
        return "MILD_POS"
    elif pearson < -.1: # mild negative correlation
        return "MILD_NEG"
    else: # no correlation
        return "NONE"

def two_way_strong(pearson):
    if pearson > .3: # high correlation
        return "STRONG_POS"
    else: # no correlation
        return "NONE"

def two_way_mild(pearson):
    if pearson > .1: # mild correlation
        return "MILD_POS"
    else: # no correlation
        return "NONE"

def get_truth_function(function_name):
    """Pick out an appropriate function to compute truth values.
    """
    truth_functions = {}
    truth_functions['2_way_mild'] = two_way_mild
    truth_functions['2_way_strong'] = two_way_strong
    truth_functions['3_way_mild'] = three_way_mild
    truth_functions['3_way_strong'] = three_way_strong
    truth_functions['5_way'] = five_way

    try:
        return truth_functions[function_name]
    except KeyError:
        raise AttributeError ("invalid function name %s" % function_name)

def get_truth_nominals(function_name):
    """Pick out appropriate nominal values for the truth class
    given a truth function.
    """
    truth_nominals = {}
    truth_nominals['2_way_mild'] = ['MILD_POS', 'NONE']
    truth_nominals['2_way_strong'] = ['STRONG_POS', 'NONE']
    truth_nominals['3_way_mild'] = ['MILD_POS', 'MILD_NEG', 'NONE']
    truth_nominals['3_way_strong'] = ['STRONG_POS', 'STRONG_NEG', 'NONE']
    truth_nominals['5_way'] = ['STRONG_POS', 'MILD_POS', 'MILD_NEG', 'STRONG_NEG', 'NONE']

    try:
        return truth_nominals[function_name]
    except KeyError:
        raise AttributeError ("invalid function name %s" % function_name)

def get_features(relations_file, pmi_file, cooccurrence_counts_file, feature_file,
        truth_file=None, truth_function=None):
    """Write an arff file with the correct features from past experiments.
    """

    relations_DB = db.DB()
    relations_DB.open(relations_file, None, db.DB_HASH, 
            db.DB_RDONLY)
    pmi_DB = db.DB()
    pmi_DB.open(pmi_file, None, db.DB_HASH, db.DB_RDONLY)
    cooccurrence_counts_DB = db.DB()
    cooccurrence_counts_DB.open(cooccurrence_counts_file, None, db.DB_HASH, 
            db.DB_RDONLY)

    attribute_list = [("context similarity", 1, []),
            ("normal similarity", 1, []),
            ("pmi between diseases", 1, []),
            ("times diseases cooccurred", 1, []),
            ("disease names", 0, []),
            ]
    if truth_file and truth_function:
        truth_DB = db.DB()
        truth_DB.open(truth_file, None, db.DB_HASH, db.DB_RDONLY)
        attribute_list.append(("truth value", 0, get_truth_nominals(truth_function)))
        truth_function = get_truth_function(truth_function)

    instances = []
    cursor = relations_DB.cursor()
    record = cursor.first()
    while record:
        instance = []
        key, value = record
        target_1, target_2 = key.split(',')
        context_sim, norm = value.split(',')

        instance.append(context_sim)
        instance.append(norm)

        key_1 = "%s,%s" % (target_1, target_2)
        key_2 = "%s,%s" % (target_2, target_1)
        ## it's possible the two diseases never cooccurr with each
        ## other, so the cooccurrence count is 0 and the PMI is
        ## uncalculatable (can't divide by infinity) so we'll
        ## mark it as a missing feature (a '?')
        instance.append(pmi_DB.get(key_1) or pmi_DB.get(key_2) or '?')
        instance.append(cooccurrence_counts_DB.get(key_1) or 
                cooccurrence_counts_DB.get(key_2) or 0)
        instance.append("%s-%s" % (target_1, target_2))

        if truth_file and truth_function:
            pearson = truth_DB.get(key_1) or truth_DB.get(key_2)
            if pearson:
                instance.append(truth_function(float(pearson)))
            else:
                instance.append('?')

        instances.append(instance)
        record = cursor.next()

    with open(feature_file, 'w') as arff_file:
        arff.arffwrite(arff_file, attribute_list, instances, name='comorbidity')
