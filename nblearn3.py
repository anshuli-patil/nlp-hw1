import json
import math
import sys
from collections import defaultdict

from nlp.hw1 import data_tokenizer

model_filename = 'nbmodel.txt'


def get_genuine(labels_dict, data_id):
    return labels_dict[data_id][0]


def get_sentiment(labels_dict, data_id):
    return labels_dict[data_id][1]


def read_sample_data(textfile_path, labelfile_path):
    absolute_path = labelfile_path
    label_tokenizer = data_tokenizer.DataTokenizer(absolute_path)
    labels_dict = label_tokenizer.read_labels()

    absolute_path = textfile_path
    tokenizer = data_tokenizer.DataTokenizer(absolute_path)

    occurrences_positive = defaultdict(int)
    occurrences_negative = defaultdict(int)

    occurrences_truthful = defaultdict(int)
    occurrences_deceptive = defaultdict(int)

    # training_lines = get_training_dev_split(path)[0]
    # training_lines_count = 0

    positive_data_count = 0
    negative_data_count = 0
    deceptive_data_count = 0
    truthful_data_count = 0

    while tokenizer.has_line(): # and training_lines_count < training_lines:
        # training_lines_count += 1
        line = tokenizer.next_line()
        data_id = tokenizer.next_id()

        genuine = get_genuine(labels_dict, data_id)
        sentiment = get_sentiment(labels_dict, data_id)

        truth, deceptive, pos, neg = count_feature_occurrences(line, genuine, sentiment, occurrences_positive,
                                                               occurrences_negative, occurrences_truthful,
                                                               occurrences_deceptive)
        positive_data_count += pos
        negative_data_count += neg
        deceptive_data_count += deceptive
        truthful_data_count += truth

    tokenizer.close()
    prior_prob_genuine = (truthful_data_count / (truthful_data_count + deceptive_data_count))
    prior_prob_sentiment = (positive_data_count / (positive_data_count + negative_data_count))

    return (occurrences_positive, occurrences_negative, prior_prob_genuine), \
           (occurrences_truthful, occurrences_deceptive, prior_prob_sentiment)


def count_feature_occurrences(line, genuine, sentiment, occurrences_positive, occurrences_negative,
                              occurrences_truthful, occurrences_deceptive):
    positive_data_count = 0
    negative_data_count = 0
    deceptive_data_count = 0
    truthful_data_count = 0

    if genuine == 'truthful':
        truthful_data_count = 1
        increase_count(occurrences_truthful, line)
    elif genuine == 'deceptive':
        deceptive_data_count = 1
        increase_count(occurrences_deceptive, line)
    if sentiment == 'positive':
        positive_data_count = 1
        increase_count(occurrences_positive, line)
    elif sentiment == 'negative':
        negative_data_count = 1
        increase_count(occurrences_negative, line)
    return truthful_data_count, deceptive_data_count, positive_data_count, negative_data_count


def estimate_probability(textfile_path, labelfile_path):
    data_results = read_sample_data(textfile_path, labelfile_path)

    positive, negative, prior_probability_pos = data_results[0]
    prior_probability_neg = 1 - prior_probability_pos

    truthful, deceptive, prior_probability_truth = data_results[1]
    prior_probability_deceptive = 1 - prior_probability_truth

    fill_missing(positive, negative)
    fill_missing(negative, positive)
    fill_missing(truthful, deceptive)
    fill_missing(deceptive, truthful)
    smooth_normalize(negative)
    smooth_normalize(positive)
    smooth_normalize(deceptive)
    smooth_normalize(truthful)

    return {'+': (positive, math.log(prior_probability_pos)), '-': (negative, math.log(prior_probability_neg)),
            't': (truthful, math.log(prior_probability_truth)), 'd': (deceptive, math.log(prior_probability_deceptive))}


def fill_missing(occurrences_dict, occurrences_dict_complement):
    for word in occurrences_dict:
        if word not in occurrences_dict_complement:
            occurrences_dict_complement[word] = 0


def smooth_normalize(occurrences_dict):
    if '' in occurrences_dict:
        del occurrences_dict['']
    total_count = 0

    for key in occurrences_dict:
        occurrences_dict[key] += 1
        total_count += occurrences_dict[key]

    # taking log to prevent underflow
    for key in occurrences_dict:
        occurrences_dict[key] = math.log(occurrences_dict[key]/total_count)
    return


def increase_count(dict_feature, line):
    """
    :type dict_feature: dict
    """
    for word in line:
        if check_number(word):
            continue
        dict_feature[word] += 1
    return


def check_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def print_dict(dictionary):
    for key in dictionary:
        print(key, dictionary[key])


def create_model(textfile_path, labelfile_path):
    model = estimate_probability(textfile_path, labelfile_path)
    absolute_path_model = model_filename
    with open(absolute_path_model, 'w') as f:
        json.dump(model, f)
    f.close()

'''
python nblearn.py /path/to/text/file /path/to/label/file
'''
create_model(str(sys.argv[1]), str(sys.argv[2]))
