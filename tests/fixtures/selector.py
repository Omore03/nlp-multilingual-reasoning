"""Predetermined fixture infrastructure; no random or similarity algorithm."""
__version__ = 'fixture-table-v1'


def select_examples(query, pool, k, strategy, seed):
    assert set(query) == {'id', 'question_ur'}, 'Never pass dev gold to selectors'
    assert k == 2
    if strategy == 'random':
        return ['synthetic-demo-02', 'synthetic-demo-01']
    if strategy == 'similarity':
        return ['synthetic-demo-04', 'synthetic-demo-03']
    raise ValueError('Unsupported fixture strategy')
