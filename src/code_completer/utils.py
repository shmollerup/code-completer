#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-


class TokenMapper():

    def __init__(self, keywords):
        self.token2ID = {k: i for i, k in enumerate(keywords)}
        self.ID2token = {i: k for i, k in enumerate(keywords)}

    def tokens2IDs(self, tokens):
        """
        Converts list of tokens to ids.
        if token is not in already registered tokens it is saved for
        future reference.

        :param tokens:
            list of tokens
        :returns:
            list of ids
        """
        def get_token(token):
            if token not in self.token2ID:
                self.ID2token[len(self.token2ID)] = token
                self.token2ID[token] = len(self.token2ID)
            return self.token2ID[token]

        return [get_token(t) for t in tokens]

    def __call__(self, tokens):
        return self.tokens2IDs(tokens)
