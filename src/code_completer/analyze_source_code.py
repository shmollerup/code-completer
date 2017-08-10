#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`code_completer.analyze_source_code` -- source code analyzer

===================
Analyze Source Code
===================

Analyzes source code and creates json file with common keywords, and
their count.
"""
from collections import Counter
import fnmatch
import json
import logging
import os
import re

logger = logging.getLogger(__name__)


def remove_comments(filename, content):
    if filename.endswith('.c'):
        return __c_uncomment(content)
    elif sum([filename.endswith(e) for e in ['.cpp', '.cc', 'cxx', '.h', '.hh', '.hxx', '.hpp']]) > 0:
        return __cpp_uncomment(content)
    elif filename.endswith('.py'):
        return __py_uncomment(content)


def __c_uncomment(content):
    return re.sub(r'/\*.*?\*/', '', content, flags=re.MULTILINE | re.DOTALL)


def __cpp_uncomment(content):
    pass1 = __c_uncomment(content)
    pass2 = re.sub(r'//.*', '', pass1)
    return pass2


def __py_uncomment(content):
    pass1 = re.sub(r'#.*', '', content)
    pass2 = re.sub(r'""".*?"""', '', pass1, flags=re.MULTILINE | re.DOTALL)
    return pass2


def matching_files(paths, suffixes):
    patterns = ['*' + x for x in suffixes]
    matches = []
    for path in paths:
        for r, d, f in os.walk(path, topdown=True):
            d = [dr for dr in d if '__' not in dr]
            for p in patterns:
                for fname in fnmatch.filter(f, p):
                    matches.append(os.path.join(r, fname))
    return matches


def tokenize(filename, content):
    tokens = []
    content = remove_comments(filename, content)
    for line in content.split('\n'):
        tokens += [t.strip() for t in re.split(r'(\W+)', line) if len(t.strip()) > 0]
    return tokens


def find_frequent_tokens(paths, suffixes, max_tokens, min_count=None, training_data=True):
    token_counter = Counter()
    training_lists = []
    i = 0
    for i, filename in enumerate(matching_files(paths, suffixes)):
        with open(filename) as fh:
            tokens = tokenize(filename, fh.read())
            if training_data:
                training_lists.append(tokens)
            for t in tokens:
                token_counter[t] += 1
        if i and i % 100 == 0:
            logger.debug('analyzed %d files' % i)
    logger.info('analyzed %d files' % i)
    tokens = token_counter.most_common(max_tokens)

    if min_count:
        for k in list(token_counter):
            if token_counter[k] < 15:
                del token_counter[k]
        tokens = token_counter.items()

    return training_lists, tokens


def main(paths, suffixes, max_tokens, min_count, outfile_prefix, training_data=True):
    training_data, tokens = find_frequent_tokens(paths, suffixes, max_tokens, min_count, training_data=training_data)

    outfile = outfile_prefix + '-%d.json' % len(tokens)
    with open(outfile, 'w') as fh:
        fh.write(json.dumps([t for t, _ in tokens]))
    logger.info("result written to file %s", outfile)
    if training_data:
        outfile = outfile_prefix + '-token-lists-%d-%d.json' % (len(training_data), len(tokens))
        with open(outfile, 'w') as fh:
            fh.write(json.dumps(training_data))
        logger.info("training data written to file %s", outfile)


def __lsplit(arg):
    return arg.split(',')


def cli():
    import argparse

    langs = {'c': ['c', '.cpp', '.cc', 'cxx', '.h', '.hh', '.hxx', '.hpp'],
             'py': ['py']}
    default_lang = ['.py']
    num_tokens = 1000
    outfile = 'keywords'

    parser = argparse.ArgumentParser(description='Analyze and tokenize sourcecode files')
    parser.add_argument('paths', metavar='PATH', nargs='+',
                        help='paths to find source code in')
    parser.add_argument('-l', '--langs', type=__lsplit, default=default_lang,
                        help='languages to use as a comma spearated list. supported languages are %s. default is %s' %
                        (langs.keys(), default_lang))
    parser.add_argument('-n', '--num', type=int, default=num_tokens,
                        help='number of unique keywords to extract counts for. Default is %d' % num_tokens)
    parser.add_argument('-m', '--min-count', type=int,
                        help='minimum number occurences of keywords. If set num is ignored')
    parser.add_argument('-o', '--outfile-prefix', default=outfile, dest='outfile',
                        help='file prefix to write keyword data to. Default is \'%s\'' % outfile)
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help='verbose output')

    args = parser.parse_args()

    level = logging.INFO
    if args.verbose:
        level = logging.DEBUG

    logging.basicConfig(format='%(message)s', level=level)
    main(args.paths, args.langs, args.num, args.min_count, args.outfile)


if __name__ == '__main__':
    cli()
