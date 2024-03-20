import glob
import logging

logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s %(message)s', level=logging.ERROR)


class Classifier:
    """
    Interface class
    """
    _name = None

    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(logging.INFO)
        self.log.info('Apply model %s' % self.get_name())
        self.results = []

    def train(self, folder_name):
        raise NotImplementedError

    def predict(self, file_name_in):
        raise NotImplementedError

    def save_model(self):
        raise NotImplementedError

    def load_model(self):
        raise NotImplementedError

    def folder_to_file(self, folder_name, file_name):
        self.log.info('Move data from folder %s to file %s' % (folder_name, file_name))
        with open(file_name, mode='w', encoding='utf-8') as f:
            for line in self.iterate_lines(folder_name):
                f.write(line + '\n')

    def iterate_lines(self, folder_name):
        files = glob.glob(folder_name + '/**/*.tsv', recursive=True)
        for file_name_in in files:
            self.log.info('Read file %s' % file_name_in)
            with open(file_name_in, mode='r', encoding='utf-8') as f:
                for line in f.readlines():
                    yield line.strip()

    def evaluate(self, result_file, ref_file, explain=True):
        """
        Build confusion matrix, calculate precision and recall
        https://en.wikipedia.org/wiki/Confusion_matrix
        """
        self.log.info('Evaluate result in : %s, reference: %s' % (result_file, ref_file))

        # read reference data
        ref_data = {}
        with open(ref_file, mode='r', encoding='utf-8') as f_ref:
            for line in f_ref.readlines():
                try:
                    parts = line.strip().split('\t')
                    name = parts[0]
                    value = int(parts[1])
                    ref_data[name] = value
                except IndexError:
                    self.log.exception('Error at %s' % line)

        true_positive = []
        false_positive = []
        false_negative = []
        true_negative = []
        # read results and compare
        res_data = {}
        with open(result_file, mode='r', encoding='utf-8') as f_res:
            for line in f_res.readlines():
                parts = line.strip().split('\t')
                name = parts[0]
                if name not in ref_data:
                    self.log.warning('Cannot find %s in reference data!' % name)
                else:
                    value = int(parts[1])
                    score = parts[2]
                    explain = parts[3]
                    res_data[name] = (value, score, explain)

                    if ref_data[name] == 1:
                        if value == 1:
                            # correct with value 1
                            true_positive.append(name)
                        else:
                            # wrong with value 0
                            false_negative.append(name)
                    else:
                        if value == 0:
                            # correct with value 0
                            true_negative.append(name)
                        else:
                            # wrong with value 1
                            false_positive.append(name)
        total_positive = len(true_positive) + len(false_positive)
        total_ref_positive = len(true_positive) + len(false_negative)
        precision = len(true_positive) / total_positive
        recall = len(true_positive) / total_ref_positive
        total = len(true_positive) + len(true_negative) + len(false_positive) + len(false_negative)
        accuracy = (len(true_positive) + len(true_negative)) / total
        fscore = 2 * (precision * recall) / (precision + recall)
        self.log.info('Precision: %s' % precision)
        self.log.info('Recall: %s' % recall)
        self.log.info('F-Score: %s' % fscore)
        self.log.info('Accuracy: %s' % accuracy)

        if explain:
            detail = ''
            for name in false_positive:
                detail += '%s\t%s\t%s\t%s\n' % (name, res_data[name][0], res_data[name][1], res_data[name][2])
            self.log.info('False Positive:\n%s' % len(false_positive))
            with open(result_file + '.false_positive', mode='w', encoding='utf-8') as f:
                f.write(detail)

            detail = ''
            for name in false_negative:
                detail += '%s\t%s\t%s\t%s\n' % (name, res_data[name][0], res_data[name][1], res_data[name][2])
            self.log.info('False Negative:\n%s' % len(false_negative))
            with open(result_file + '.false_negative', mode='w', encoding='utf-8') as f:
                f.write(detail)

    def get_name(self):
        return self._name

    def write_results(self, file_name_out):
        self.results = sorted(self.results, key=lambda tup: (tup[1], tup[0]) , reverse=True)
        with open(file_name_out, mode='w', encoding='utf-8') as fout:
            for r in self.results:
                fout.write('%s\t%s\t%s\t%s\n' % (r[0], r[1], r[2], r[3]))

        self.log.info('Prediction output: %s' % file_name_out)
