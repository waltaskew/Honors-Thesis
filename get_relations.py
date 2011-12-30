from bsddb import db
import math
from normalize import normalize

class RelationFinder:
    """Holds data structures needed for computing relations
    between diseases.
    """
    def __init__(self, out_file, min_threshold = 0):
        self.out_file = out_file
        self.min_threshold = min_threshold

        self.shared_cooccurrences = {}
        self.relation_metrics = {}

    def add_cooccurrence(self, target, word, pmi):
        """Find cooccurrences which are shared by multiple target words.
        """
        try:
             # a collision means that two targets cooccurr with the same word
            self.shared_cooccurrences[word].append((target, pmi))
        except KeyError:
            self.shared_cooccurrences[word] = [(target, pmi)]

    def compute_relations(self):
        """Compute relation metrics using cooccurrence words shared by
        multiple targets.
        """
        for word, cooccurrences in self.shared_cooccurrences.iteritems():
            length = len(cooccurrences)
            for i in range(length - 1):
                target_1, pmi_1 = cooccurrences[i]
                for j in range(i + 1, length):
                    target_2, pmi_2 = cooccurrences[j]
                    context_sim = (min(pmi_1, pmi_2)) / (max(pmi_1, pmi_2))
                    norm = abs(pmi_1 - pmi_2)
                    weight = max(pmi_1, pmi_2)
                    self.add_relation_metrics(target_1, target_2, context_sim,
                            norm, weight)

    def add_relation_metrics(self, target_1, target_2, context_sim, norm, weight):
        """Hold the weighted average of relation metrics between two targets.
        """
        def calculate_vals(contex_sim, norm, weight, total_context_sim,
                total_norm, total_weight, count):
            return (total_context_sim + (context_sim * weight), 
                    total_norm + (norm * weight),
                    total_weight + weight,
                    count + 1)

        try:
            key_1 = "%s,%s" % (target_1, target_2)
            total_context_sim, total_norm, total_weight, count =\
                    self.relation_metrics[key_1]
            self.relation_metrics[key_1] = calculate_vals(context_sim, norm, weight,
                    total_context_sim, total_norm, total_weight, count)
        except KeyError:
            try:
                key_2 = "%s,%s" % (target_2, target_1)
                total_context_sim, total_norm, total_weight, count =\
                        self.relation_metrics[key_2]
                self.relation_metrics[key_2] = calculate_vals(context_sim, norm, weight,
                    total_context_sim, total_norm, total_weight, count)
            except KeyError:
                self.relation_metrics[key_1] = (context_sim, norm, weight, 1)

    def write_output(self):
        """Write a Berkely DB which contains calculated relation metrics.
        """
        outDB = db.DB()
        outDB.open(self.out_file, None, db.DB_HASH, 
                db.DB_CREATE | db.DB_TRUNCATE)
        for key, (context_sim, norm, weight, count) in self.relation_metrics.iteritems():
            if count > self.min_threshold:
                context_sim /= weight
                norm /= weight
                outDB.put(key, "%s,%s" % (context_sim, norm))
        outDB.close()

def get_relations(pmi_file, min_threshold, out_file):
    """Use calculated PMI's to compute relationship metrics
    between a list of targets.
    """
    pmi_DB = db.DB()
    pmi_DB.open(pmi_file, None, db.DB_HASH, db.DB_RDONLY)
    cursor = pmi_DB.cursor()
    record = cursor.first()

    relationFinder = RelationFinder(out_file, min_threshold)

    while record:
        key, pmi = record
        pmi = float(pmi)
        target, word = key.split(',')
        relationFinder.add_cooccurrence(target, word, pmi)
        record = cursor.next()
    pmi_DB.close()

    relationFinder.compute_relations()
    relationFinder.write_output()
