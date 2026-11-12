"""Runner boundary checks, not Hussain's full linguistic/dataset validator."""
import importlib
import inspect
import json
import re
from pathlib import Path

NUMBER = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z')


def load_records(path, demonstration=False, synthetic=False):
    records = []
    try:
        lines = Path(path).read_text(encoding='utf-8').splitlines()
    except OSError:
        raise ValueError(f'Missing input {path}; integrate Hussain’s data or use configs/mock.yaml') from None
    for n, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except (ValueError, UnicodeError):
            raise ValueError(f'Invalid input JSON at line {n}') from None
        required = ['id', 'question_en', 'question_ur', 'answer']
        if demonstration:
            required += ['reasoning_en', 'reasoning_ur']
        if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k].strip() for k in required):
            raise ValueError(f'Missing/non-string required input field at line {n}')
        if not NUMBER.fullmatch(row['answer']):
            raise ValueError(f'Answer must be a plain numeric string at line {n}')
        if 'verified' in row and type(row['verified']) is not bool:
            raise ValueError('Optional verified field must be boolean')
        if demonstration and type(row.get('verified')) is not bool:
            raise ValueError('Demonstrations require boolean verified')
        if demonstration and not synthetic and row['verified'] is not True:
            raise ValueError('Real demonstrations must be human verified by Hussain')
        if synthetic and (row.get('synthetic') is not True or row.get('verified', False)):
            raise ValueError('Fixtures must declare synthetic=true and cannot claim human verification')
        records.append(row)
    if not records or len({r['id'] for r in records}) != len(records):
        raise ValueError('Input must be nonempty with unique IDs')
    return records


def selector_query(question):
    return {'id': question['id'], 'question_ur': question['question_ur']}


def resolve_ids(ids, pool, k):
    if not isinstance(ids, list) or len(ids) != k or any(not isinstance(i, str) for i in ids):
        raise ValueError('Selector must return a list of exactly two demo ID strings')
    if len(set(ids)) != k or any(i not in pool for i in ids):
        raise ValueError('Selector returned duplicate or unknown demo IDs')
    return [pool[i] for i in ids]


def import_selector(location):
    try:
        module, name = location.split(':')
        mod = importlib.import_module(module)
        fn = getattr(mod, name)
        if not callable(fn):
            raise TypeError
        return fn, Path(inspect.getfile(mod))
    except (ValueError, ImportError, AttributeError, TypeError):
        raise ValueError('Selector unavailable; integrate Rayyan’s module and set selector to module:select_examples. '
                         'For offline fixtures use configs/mock.yaml.') from None
