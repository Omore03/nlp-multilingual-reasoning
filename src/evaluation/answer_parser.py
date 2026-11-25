import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

OK = "ok"
MISSING = "missing"
AMBIGUOUS = "ambiguous"
PARSE_STATUSES = (OK, MISSING, AMBIGUOUS)

DEFAULT_MARKERS = (
    r"FINAL_ANSWER\s*:",
    r"#{4}",
    r"final\s+answer\s*(?:is\b\s*[:：]?|[:：])",
    r"حتمی\s+جواب\s*[:：]",
    r"آخری\s+جواب\s*[:：]",
)

# Parser change proposed 25 Nov 2026 (pending Saad's approval; see docs/parser_change_2026-11-25.md).
# The runner's own terminal marker takes priority: when a response contains a literal FINAL_ANSWER
# (colon optional) followed by a number, the LAST such marker decides the answer. Only responses with
# no usable FINAL_ANSWER fall back to the earlier rule over all DEFAULT_MARKERS, unchanged.
# This stops two formatting failures: "FINAL_ANSWER 70" (no colon) and a generic "final answer:"
# followed by a restated question being read as a second, disagreeing answer.
PARSER_VERSION = "2-last-final-answer-first"
PRIMARY_MARKER = r"FINAL_ANSWER\s*[:：]?"
_AUTO = object()

_DIGIT_MAP = {}
for _offset in range(10):
    _DIGIT_MAP[0x0660 + _offset] = str(_offset)
    _DIGIT_MAP[0x06F0 + _offset] = str(_offset)

_CHAR_MAP = dict(_DIGIT_MAP)
_CHAR_MAP.update({
    0x066B: ".",
    0x066C: ",",
    0x066A: "%",
    0x2212: "-",
    0xFE63: "-",
    0xFF0D: "-",
})
for _invisible in (0x200E, 0x200F, 0x061C, 0x200B, 0x200C, 0x200D, 0xFEFF):
    _CHAR_MAP[_invisible] = None
for _bidi in list(range(0x202A, 0x202F)) + list(range(0x2066, 0x206A)):
    _CHAR_MAP[_bidi] = None

_NUMBER = re.compile(
    r"(?<![\w.])(-?)(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?!\d)"
    r"|(?<![\w.])(-?)(\.\d+)(?!\d)"
)


@dataclass(frozen=True)
class ParseResult:
    value: Optional[Decimal]
    status: str
    detail: str

    @property
    def prediction(self) -> Optional[str]:
        if self.value is None:
            return None
        return format_decimal(self.value)


def normalize_text(text: str) -> str:
    folded = unicodedata.normalize("NFKC", text)
    return folded.translate(_CHAR_MAP)


def format_decimal(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(value.quantize(Decimal(1)))
    return format(value.normalize(), "f")


def to_decimal(raw) -> Decimal:
    if isinstance(raw, bool):
        raise ValueError("boolean is not a numeric answer")
    if isinstance(raw, Decimal):
        return raw
    if isinstance(raw, (int, float)):
        return Decimal(str(raw))
    if not isinstance(raw, str):
        raise ValueError(f"unsupported answer type: {type(raw).__name__}")
    found = find_numbers(raw)
    if len(found) != 1:
        raise ValueError(f"expected exactly one number in {raw!r}")
    return found[0]


def find_numbers(text: str) -> list:
    cleaned = normalize_text(text)
    values = []
    for match in _NUMBER.finditer(cleaned):
        values.append(_match_to_decimal(match))
    return values


def _match_to_decimal(match) -> Decimal:
    if match.group(2) is not None:
        sign, whole, fraction = match.group(1), match.group(2), match.group(3) or ""
        literal = sign + whole.replace(",", "") + fraction
    else:
        literal = match.group(4) + "0" + match.group(5)
    try:
        return Decimal(literal)
    except InvalidOperation as exc:
        raise ValueError(f"cannot read number {literal!r}") from exc


def _segment_after(text: str, start: int) -> str:
    rest = text[start:].lstrip()
    newline = rest.find("\n")
    if newline == -1:
        return rest
    return rest[:newline]


def _values_after_markers(text: str, markers) -> list:
    pattern = re.compile("|".join(f"(?:{m})" for m in markers), re.IGNORECASE)
    segments = []
    for hit in pattern.finditer(text):
        segments.append(_segment_after(text, hit.end()))
    return segments


def _distinct(values) -> list:
    unique = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def _last_primary(text: str, primary: str) -> Optional[ParseResult]:
    """Result from the last literal primary marker that is followed by a number, else None."""
    for hit in reversed(list(re.finditer(primary, text, re.IGNORECASE))):
        values = _distinct(find_numbers(_segment_after(text, hit.end())))
        if not values:
            continue  # e.g. an echoed instruction "... marker FINAL_ANSWER: followed by the number"
        if len(values) > 1:
            return ParseResult(None, AMBIGUOUS, "several numbers after the last FINAL_ANSWER marker")
        return ParseResult(values[0], OK, "last FINAL_ANSWER marker")
    return None


def parse_answer(response, markers=DEFAULT_MARKERS, primary=_AUTO) -> ParseResult:
    """Parse the final numerical answer.

    ``primary`` defaults to PRIMARY_MARKER with the default markers and to None (no priority rule)
    when custom markers are supplied, so custom markers still fully replace the defaults.
    """
    if not isinstance(response, str) or not response.strip():
        return ParseResult(None, MISSING, "empty response")

    text = normalize_text(response).replace("*", "")
    legacy = _parse_markers(text, markers)
    if primary is _AUTO:
        primary = PRIMARY_MARKER if tuple(markers) == DEFAULT_MARKERS else None
    if primary is None:
        return legacy
    last = _last_primary(text, primary)
    if last is None:
        return legacy
    if legacy.status == OK and legacy.value == last.value:
        return legacy  # same answer as before: keep the earlier detail text unchanged
    return last


def _parse_markers(text: str, markers) -> ParseResult:
    """The original rule: every marker's segment must agree on a single number."""
    segments = _values_after_markers(text, markers)
    if not segments:
        return ParseResult(None, MISSING, "no final-answer marker")

    per_segment = [_distinct(find_numbers(seg)) for seg in segments]
    with_numbers = [vals for vals in per_segment if vals]
    if not with_numbers:
        return ParseResult(None, MISSING, "marker without a number")

    if any(len(vals) > 1 for vals in with_numbers):
        return ParseResult(None, AMBIGUOUS, "several numbers after one marker")

    candidates = _distinct(vals[0] for vals in with_numbers)
    if len(candidates) > 1:
        shown = ", ".join(format_decimal(v) for v in candidates)
        return ParseResult(None, AMBIGUOUS, f"markers disagree: {shown}")

    return ParseResult(candidates[0], OK, f"{len(with_numbers)} marker(s) agree")
