from collections import namedtuple, defaultdict
import re
from typing import Dict, Iterator, List, TextIO, Tuple



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
    'phrase_end',
    'tokens'
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
        tokens.append(Token(doc_id, sent_id, tok_id, form, lemma, pos, posx,
                            morph, parse, head_id, dep, ne, coref, more))


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
                        phrase_tokens = sentence[int(phrase_start) - 1 : int(phrase_end)]
                        mentions.append(Mention(coref_id,
                                                token.doc_id,
                                                token.sent_id,
                                                phrase_start,
                                                phrase_end,
                                                phrase_tokens))

            if any(len(stack) > 0 for stack in phrase_stacks.values()):
                raise RuntimeError('something\'s wrong with sentence {} in document {}'.format(sentence[0].sent_id, sentence[0].doc_id))

    return mentions


def create_coref_chains(mentions: List[Mention]) -> Dict[str, List[List[Mention]]]:
    """For every document, extract a list of coref chains. A coref chain is a list of Mentions."""
    doc_id_hash = {}
    curr_id = {}
    curr_list = []

    # sort mentions into doc_id_hash by doc_id
    for mention in mentions:
        if mention.doc_id in doc_id_hash:
            curr_list.append(mention)
            doc_id_hash[mention.doc_id] += curr_list
            curr_list = []
        else:
            curr_list.append(mention)
            doc_id_hash[mention.doc_id] = curr_list
            curr_list = []

    # sort mentions in curr_id hash to sort for coref_id
    for doc_id in doc_id_hash: 
        for mention in doc_id_hash[doc_id]:
            if mention.coref_id in curr_id:
                curr_list.append(mention)
                curr_id[mention.coref_id] += curr_list
                curr_list = []
            else:
                curr_list.append(mention)
                curr_id[mention.coref_id] = curr_list
                curr_list = []

        # create a list of list of mentions and set them as value for doc_id in doc_îd_hash
        for coref_id in curr_id:
            mention = curr_id[coref_id]
            curr_list.append(mention)
        doc_id_hash[doc_id] = curr_list

        # go to next doc_id with empty curr list and hash
        curr_list = []
        curr_id = {}

    return doc_id_hash 


def extract_feature_vector(mention1: Mention, mention2: Mention) -> tuple:
    """Extract features for a single Mention pair."""
    #get information from token
    Pos1 = mention1[5][5]  
    gramFct1 = mention1[5][10] 
    Pos2 = mention2[5][5]
    gramFct2 = mention2[5][10]
    if mention1[5][2] == mention2[5][2]:
        samehead = 2
    else:
        samehead = 0
    samehead 
    if Pos1 == Pos2:
        samePos= 2
    else:
          samePos = 0
    if gramFct1 == gramFcr2:
        samegramFct = 2
    else: 
        samegramFct = 0
    feature_vector = (PoS1, gramFct1, Pos2, gramFct2, samehead, samePoS, samegramFct)
    return feature_vector


def extract_features_labels(mentions: List[Mention],
                            doc_coref_chains: Dict[str, List[List[Mention]]]
                            ) -> Tuple[List[tuple], List[int]]:
    """Create parallel lists of features and labels (X and y)."""
    features = []  # = X
    labels = []    # = y
        for doc in doc_coref_chains:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
        coref_chains = doc_coref_chains[doc]
        for coref_chain in coref_chains:
            for mention1, mention2 in zip(coref_chain, coref_chain[1:]):
                feature_vector = extract_feature_vector(mention1, mention2)
                features.append(feature_vector)
                labels.append(1)  # 1 = "coreference", 0 = "no coreference"
                # TODO: compare mention1 to all mentions between mention1 and mention2
                for mention3 in mentions:
                    if mention3.doc_id == mention2.doc_id == mention1.doc_id #doc id must be same
                    if mention1.phrase_start<mention3.phrase_start<mention2.phrase_start: #mention3 must be betw
                        if mention1.sent_id<=mention3.sent_id<=mention2.sent_id: #mention id can between sentences. 
                            features.append(extract_feature_vector(mention1,mention3)
                                            labels.append(0))
                       
                # → add features and label=0 (lines 8ff on slide 4)

    return features, labels


if __name__ == '__main__':
    mentions = extract_mentions('data/train.tueba.coref.txt', 'data/train.tueba.sync.txt')
    doc_coref_chains = create_coref_chains(mentions)
    features, labels = extract_features_labels(mentions, doc_coref_chains)
    # TODO output features and labels as CSV
    
