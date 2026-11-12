"""Controlled bilingual two-shot prompts. No evaluation or answer parsing."""
TEMPLATE_VERSION = 'bilingual-math-2shot-v1'
FINAL_MARKER = 'FINAL_ANSWER:'
CONDITIONS = {'U-U-U': ('ur', 'ur', 'ur'), 'U-U-E': ('ur', 'ur', 'en'),
              'U-E-E': ('ur', 'en', 'en'), 'E-E-E': ('en', 'en', 'en')}
INSTRUCTIONS = {
    'en': ('Solve the target question with a complete worked solution in the target question language. '
           'Follow the solved demonstrations. End with a single final numerical answer on the last line '
           'using the literal marker FINAL_ANSWER: followed by the number.'),
    'ur': ('ہدف سوال کی زبان میں مکمل مرحلہ وار حل لکھیں۔ حل شدہ مثالوں کی پیروی کریں۔ '
           'آخری سطر میں صرف حتمی عددی جواب لکھیں۔ اس سطر کے شروع میں یہی نشان '
           'FINAL_ANSWER: لکھیں اور اس کے بعد جواب کا عدد لکھیں۔')}
LABELS = {'en': ('Demonstration', 'Question', 'Worked solution', 'Target question'),
          'ur': ('مثال', 'سوال', 'مکمل حل', 'ہدف سوال')}


def build_prompt(query, demos, condition):
    if condition not in CONDITIONS:
        raise ValueError('Unsupported language condition')
    if len(demos) != 2 or len({d['id'] for d in demos}) != 2:
        raise ValueError('Exactly two distinct solved demonstrations are required')
    qlang, dlang, ilang = CONDITIONS[condition]
    example, question, solution, target = LABELS[ilang]
    parts = [INSTRUCTIONS[ilang]]
    for n, demo in enumerate(demos, 1):
        parts.append(f"{example} {n}\n{question}: {demo['question_' + dlang]}\n"
                     f"{solution}: {demo['reasoning_' + dlang]}\n{FINAL_MARKER} {demo['answer']}")
    # Explicit field access keeps target gold and any extra fields out of prompts.
    parts.append(f"{target}\n{question}: {query['question_' + qlang]}")
    return '\n\n'.join(parts)
