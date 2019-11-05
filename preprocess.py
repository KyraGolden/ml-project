from collections import namedtuple, defaultdict
import re
from typing import List, Iterator, TextIO


Token = namedtuple('Token', (
    'doc_id',
    'sent_id',
    'tok_id',
    'form',
    'lemma',
    'pos',
    'posx',
    'morph',
    'parse',
    'head_id',
    'dep',
    'ne',
    'coref',
    'more'
))
Mention = namedtuple('Mention', (
    'coref_id',
    'doc_id',
    'sent_id',
    'phrase_start',
    'phrase_end'
))


def read_sentences(coref_file: TextIO, sync_file: TextIO) -> Iterator[List[Token]]:
    tokens = []
    for coref_line, sync_line in zip(coref_file, sync_file):
        if coref_line.startswith('#'):
            # ignore comment
            continue

        if not coref_line.strip():
            # sentence is over
            yield tokens
            tokens = []
            continue

        doc_id, sent_id, tok_id, form, posx, parse, lemma, _, _, _, ne, _, coref = coref_line.strip().split('\t')
        _, _, _, _, _, pos, _, morph, head_id, dep, _, more = sync_line.strip().split('\t')
        tokens.append(Token(doc_id, sent_id, tok_id, form, lemma, pos, posx, morph, parse, head_id, dep, ne, coref, more))


def extract_mentions(coref_filename: str, sync_filename: str) -> List[Mention]:
    mentions = []
    with open(coref_filename) as coref_file, open(sync_filename) as sync_file:
        for sentence in read_sentences(coref_file, sync_file):
            phrase_stacks = defaultdict(list)
            for token in sentence:
                if token.coref == '-':
                    continue
                corefs = token.coref.split('|')
                for coref in corefs:
                    paren_left, coref_id, paren_right = re.match(r'(\(?)(\d+)(\)?)', coref).groups()
                    if paren_left:
                        # coreference phrase starts: add start id to stack
                        phrase_stacks[coref_id].append(token.tok_id)
                    if paren_right:
                        # coreference phrase ends: remove start id from stack, store mention
                        phrase_start = phrase_stacks[coref_id].pop()
                        phrase_end = token.tok_id
                        mentions.append(Mention(coref_id, token.doc_id, token.sent_id, phrase_start, phrase_end))
            if any(len(stack) > 0 for stack in phrase_stacks.values()):
                raise RuntimeError('something\'s wrong with sentence {} in document {}'.format(sentence[0].sent_id, sentence[0].doc_id))
    return mentions


def create_coref_chains(mentions):
    # TODO
    pass


if __name__ == '__main__':
    mentions = extract_mentions('data/train.tueba.coref.txt', 'data/train.tueba.sync.txt')
    print(mentions[:10])
    coref_chains = create_coref_chains(mentions)
