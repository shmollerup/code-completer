#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`code_completer.data_generator` -- generates training data

==============
Data Generator
==============


"""
from code_completer.utils import TokenMapper
from datetime import datetime
import json
import logging
import numpy as np
import joblib
logger = logging.getLogger(__name__)


class DataGenerator():

    def __init__(self, keyword_file, token_lists_file, window_size=100, move_non_keywords=True, iso_position=True):
        """
        Initializes Datagenerator.


        if the move_non_keywords is True, their index is moved as follows:
        * Token ids in range [0, K-1 are left unchanged],
          where K is the number of keywords
        * Token ids >= K are converted to a contiguous range with lower
          ids than what they originally had.
          if iso_position is false, the numbering of non-keyword tokens
          start at K. Otherwise, a non-keyword token first occuring at
          position w in the list is assigned id K+w

        Example:
          K=3
          * [0,2,1,5,7,10,2] => [0,2,1,3,4,5,2] if iso_position=False
          * [0,2,1,5,7,10,2] => [0,2,1,6,7,8,2] if iso_position=True

        :param keyword_file:
            File containing list of keywords
        :param token_lists_file:
            File containing token lists for training
        :param window_size:
            Size of training window. Default 100
        :param move_non_keywords:
            if True non-keywords in the token sequences are moved. The
            move is dependent on the setting of the iso_position
            parameter.
        :iso_position:
            True if iso position should be used for non-keywords
        """
        self.window_size = window_size
        self.move_non_keywords = move_non_keywords
        self.iso_position = iso_position

        self.keywords, self.token_lists = self.__load_data(keyword_file, token_lists_file)
        self.token_map = TokenMapper(self.keywords)

    def generate(self):
        """
        Generate test examples.
        That is a list of token ids with length window_size and the
        following id as target value.
        """
        logger.info("Generating Data (move-non-keywords=%s, iso-position=%s)", self.move_non_keywords, self.iso_position)
        id_lists = [self.token_map(tl) for tl in self.token_lists if len(tl) > self.window_size]
        weights = np.array([len(tl) - self.window_size for tl in id_lists])
        n_windows = sum(weights)
        weights = weights / n_windows

        for j, i in enumerate(np.random.choice(range(len(id_lists)), size=n_windows, p=weights)):
            window_ix = np.random.randint(len(id_lists[i]) - self.window_size)
            X = id_lists[i][window_ix:window_ix + self.window_size]
            y = id_lists[i][window_ix + self.window_size]
            if self.move_non_keywords:
                X, y = self.__move_non_keywords(X, y)
            yield np.array(X), y

            if j != 0 and j % 10000:
                logger.debug("Generated %d examples", j)

    def __move_non_keywords(self, token_ids, target):
        """ Moves non-keyword id range """
        non_keywords = {}
        converted_tokens = list(token_ids)
        for i, token in enumerate(converted_tokens):
            if token >= len(self.keywords):
                if token not in non_keywords:
                    window_token_id = len(self.keywords) + i
                    if not self.iso_position:
                        window_token_id = len(self.keywords) + len(non_keywords)
                    non_keywords[token] = window_token_id
                converted_tokens[i] = non_keywords[token]

        converted_target = target
        if target >= len(self.keywords):
            if target not in non_keywords:
                converted_target = len(self.keywords) + self.window_size
            else:
                converted_target = non_keywords[target]

        return converted_tokens, converted_target

    def __load_data(self, keyword_file, token_lists_file):
        """ loads training data """
        keywords = token_lists = None
        with open(keyword_file) as fh:
            keywords = json.load(fh)
            logger.debug("Read %d keywords from %s", len(keywords), keyword_file)
        with open(token_lists_file) as fh:
            token_lists = json.load(fh)
            logger.debug("Loaded %d token lists (avg tokens=%d) from %s",
                         len(token_lists),
                         int(sum([len(l) for l in token_lists]) / len(token_lists)),
                         token_lists_file)
        return keywords, token_lists

    def __iter__(self):
        for X, y in self.generate():
            yield X, y


def create_test_data(keyword_file, token_lists_file, outfile_prefix, window_size=100, move_non_keywords=True, iso_position=True):
    """
    Creates Test data and writes it to file.
    """
    start = datetime.now()
    dg = DataGenerator(keyword_file, token_lists_file, window_size, move_non_keywords, iso_position)
    Xs = []
    ys = []
    for X, y in dg:
        Xs.append(X)
        ys.append(y)

    mnk = 'm0'
    if move_non_keywords:
        mnk = 'm1'
    ip = 'i0'
    if iso_position:
        ip = 'i1'

    outfile = '%s-%d-%d-%s-%s.pkl' % (outfile_prefix, len(dg.keywords), len(Xs), mnk, ip)
    token_map_path = '%s-%s-tokens.pkl' % (outfile_prefix, len(dg.keywords))
    joblib.dump({'Xs': np.array(Xs), 'ys': np.array(ys)}, outfile)
    joblib.dump(dg.token_map, token_map_path)
    logger.info("Generated %d test entries in [%s]", len(Xs), datetime.now() - start)


def cli():
    import argparse
    outfile = "training-data"
    parser = argparse.ArgumentParser(description='Analyze and tokenize sourcecode files')
    parser.add_argument('keyword_file', metavar='KEYWORD_FILE',
                        help='path to keyword file')
    parser.add_argument('token_lists_file', metavar='TOKEN_LISTS_FILE',
                        help='path to token-lists-file')
    parser.add_argument('-w', '--window-size', type=int, default=100,
                        help='window-size of generated training examples. Default is 100')
    parser.add_argument('-m', '--move-non-keywords', dest='move_non_keywords', action='store_false',
                        help='move the non keywords to a continuous range above kewords in each sample')
    parser.add_argument('-i', '--iso-position', dest='iso_position', action='store_false',
                        help='iso-positioning of non-keywords. Only used if --move-non-keywords are set')
    parser.add_argument('-o', '--outfile-prefix', default=outfile, dest='outfile_prefix',
                        help='file prefix to write keyword data to. Default is \'%s\'' % outfile)
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='verbose output')

    args = parser.parse_args()

    level = logging.INFO
    if args.verbose:
        level = logging.DEBUG

    logging.basicConfig(format='%(message)s', level=level)

    create_test_data(args.keyword_file,
                     args.token_lists_file,
                     args.outfile_prefix,
                     args.window_size,
                     args.move_non_keywords,
                     args.iso_position)
