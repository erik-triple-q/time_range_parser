"""
Compiled regex patterns for date/time parsing.

All patterns are precompiled for performance and organized by category.
"""

from __future__ import annotations

import re

from .vocabulary import (
    ALL_WEEKDAYS,
    DUTCH_NUMBER_WORDS,
    ENGLISH_NUMBER_WORDS,
    MONTH_NAMES,
    MOVING_HOLIDAY_NAMES,
    PERIOD_UNITS,
    SEASONS,
    FIXED_HOLIDAYS,
    VAGUE_TIME_EXPRESSIONS,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def build_word_pattern(words: set[str] | dict) -> re.Pattern:
    """Build a regex pattern that matches any of the words with word boundaries."""
    if isinstance(words, dict):
        word_set = set(words.keys())
    else:
        word_set = words
    # Sort by length descending to match longer words first
    escaped = [re.escape(w) for w in sorted(word_set, key=len, reverse=True)]
    return re.compile(rf"\b({'|'.join(escaped)})\b", re.IGNORECASE)


# =============================================================================
# VOCABULARY PATTERNS
# =============================================================================

WEEKDAY_PATTERN = build_word_pattern(ALL_WEEKDAYS)
PERIOD_UNIT_PATTERN = build_word_pattern(PERIOD_UNITS)
SEASON_PATTERN = build_word_pattern(SEASONS)
HOLIDAY_PATTERN = build_word_pattern(FIXED_HOLIDAYS)
MONTH_PATTERN = build_word_pattern(MONTH_NAMES)


# =============================================================================
# WEEKDAY PATTERNS
# =============================================================================

NEXT_WEEKDAY_PATTERN = re.compile(
    r"\b(volgende|komende|aanstaande|next)\s+"
    r"(maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    re.IGNORECASE,
)

PREV_WEEKDAY_PATTERN = re.compile(
    r"\b(vorige|afgelopen|laatste|last|previous)\s+"
    r"(maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    re.IGNORECASE,
)

ORDINAL_WEEKDAY_PATTERN = re.compile(
    r"\b(?P<ordinal>eerste|tweede|derde|vierde|vijfde|laatste|"
    r"1e|2e|3e|4e|5e|1ste|2de|3de|4de|5de|"
    r"first|second|third|fourth|fifth|last|1st|2nd|3rd|4th|5th)\s+"
    r"(?P<weekday>maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    r"(?:\s+(?:van|of|in)(?:\s+(?:de|the))?\s+"
    r"(?P<month>januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december|"
    r"january|february|march|april|may|june|july|august|september|october|november|december|"
    r"maand|month)"
    r"(?:\s+(?P<year>\d{4}))?)?\b",
    re.IGNORECASE,
)

COMPOUND_DAY_PATTERN = re.compile(
    r"\b(?P<day>vandaag|morgen|overmorgen|gisteren|eergisteren|"
    r"maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)"
    r"(?P<part>ochtend|middag|avond|nacht)\b",
    re.IGNORECASE,
)


# =============================================================================
# PERIOD PATTERNS
# =============================================================================

QUARTER_PATTERN = re.compile(
    r"\b(?:"
    r"(?P<ordinal>1e|2e|3e|4e|eerste|tweede|derde|vierde|1ste|2de|3de|4de|"
    r"1st|2nd|3rd|4th|first|second|third|fourth)\s*(?:kwartaal|quarter)|"
    r"(?P<q_notation>q[1-4])|"
    r"(?:kwartaal|quarter)\s*(?P<quarter_num>[1-4])"
    r")"
    r"(?:\s+(?P<year>\d{4}))?\b",
    re.IGNORECASE,
)

WEEK_NUMBER_PATTERN = re.compile(
    r"\b(?:week|wk)\.?\s*(?P<week>\d{1,2})(?:\s+(?P<year>\d{4}))?\b",
    re.IGNORECASE,
)

HALF_YEAR_PATTERN = re.compile(
    r"\b(?:"
    r"(?P<h_notation>h[12])|"
    r"(?P<text>eerste\s+(?:helft|semester)|tweede\s+(?:helft|semester)|"
    r"1e\s+(?:helft|semester)|2e\s+(?:helft|semester)|"
    r"first\s+(?:half|semester)|second\s+(?:half|semester)|"
    r"1st\s+half|2nd\s+half)"
    r")"
    r"(?:\s+(?P<year>\d{4}))?\b",
    re.IGNORECASE,
)

# Dynamically build regex for all period units (singular/plural) from vocabulary
_PERIOD_UNITS_REGEX = "|".join(
    re.escape(u) for u in sorted(PERIOD_UNITS.keys(), key=len, reverse=True)
)

PAST_PERIOD_PATTERN = re.compile(
    r"\b(afgelopen|vorig|vorige|laatste|last|previous)\s+(?P<unit>"
    + _PERIOD_UNITS_REGEX
    + r")\b",
    re.IGNORECASE,
)

FUTURE_PERIOD_PATTERN = re.compile(
    r"\b(volgende|volgend|komende|komend|aanstaande|next)\s+(?P<unit>"
    + _PERIOD_UNITS_REGEX
    + r")\b",
    re.IGNORECASE,
)

WEEKEND_PATTERN = re.compile(
    r"\b(?:(?P<modifier>dit|deze|this|volgend|volgende|next|vorig|vorige|last|afgelopen)\s+)?weekend\b",
    re.IGNORECASE,
)

YEAR_BOUNDARY_PATTERN = re.compile(
    r"\b(?P<type>begin|start|eind|end)(?:\s+(?:van|of))?(?:\s+(?:het|the))?(?:\s+(?:jaar|year))?\s+(?P<year>\d{4})\b",
    re.IGNORECASE,
)


# =============================================================================
# SEASON PATTERN
# =============================================================================

SEASON_EXPR_PATTERN = re.compile(
    r"\b(?:(?P<modifier>deze|dit|this|volgende|volgend|next|vorige|vorig|last|previous|afgelopen)\s+)?"
    r"(?P<season>lente|voorjaar|zomer|herfst|najaar|winter|spring|summer|autumn|fall)"
    r"(?:\s+(?P<year>\d{4}))?\b",
    re.IGNORECASE,
)


# =============================================================================
# MONTH PATTERN
# =============================================================================

MONTH_EXPR_PATTERN = re.compile(
    r"\b(?:(?P<position>begin|eind|end|medio|half|midden|mid)\s+)?"
    r"(?P<month>januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december|"
    r"jan|feb|mrt|apr|jun|jul|aug|sep|sept|okt|oct|nov|dec|"
    r"january|february|march|may|june|july|august|october)"
    r"(?:\s+(?P<year>\d{4}))?\b",
    re.IGNORECASE,
)


# =============================================================================
# DATE PATTERNS
# =============================================================================

_MONTH_NAMES_REGEX = "|".join(
    re.escape(m) for m in sorted(MONTH_NAMES.keys(), key=len, reverse=True)
)

_ALL_NUMBER_WORDS = {**DUTCH_NUMBER_WORDS, **ENGLISH_NUMBER_WORDS}

DUTCH_DAY_MONTH_PATTERN = re.compile(
    r"\b(?:op\s+|the\s+|on\s+)??"
    r"(?P<day>\d{1,2}(?:st|nd|rd|th|e|ste|de)?|"
    + "|".join(
        re.escape(w) for w in sorted(_ALL_NUMBER_WORDS.keys(), key=len, reverse=True)
    )
    + r")\s+"
    r"(?:(?:van|of)\s+)?"
    r"(?P<month>" + _MONTH_NAMES_REGEX + r")"
    r"(?:\s+(?P<year>\d{4}))?\b",
    re.IGNORECASE,
)


# =============================================================================
# DURATION PATTERNS
# =============================================================================

IN_DURATION_PATTERN = re.compile(
    r"\b(?:over|in)\s+(?P<n>\d+|een|één|a|an)\s+(?P<unit>dagen?|weken?|maanden?|jaren?|days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)

AGO_PATTERN = re.compile(
    r"\b(?P<n>\d+|een|één|a|an)\s+(?P<unit>dagen?|weken?|maanden?|jaren?|days?|weeks?|months?|years?)\s+(?:geleden|ago)\b",
    re.IGNORECASE,
)

DURATION_PATTERN = re.compile(
    r"\b(?P<n>\d+)\s*(?P<u>"
    r"min(uten?)?|mins?|"
    r"uur|uren|hours?|h|"
    r"dag(en)?|days?|d|"
    r"week|weken|weeks?|w|"
    r"maand(en)?|months?|"
    r"jaar|jaren|years?"
    r")\b",
    re.IGNORECASE,
)


# =============================================================================
# HOLIDAY PATTERNS
# =============================================================================

MOVING_HOLIDAY_PATTERN = re.compile(
    r"\b(?P<holiday>" + "|".join(re.escape(h) for h in MOVING_HOLIDAY_NAMES) + r")"
    r"(?:\s+(?P<year>\d{4}))?\b",
    re.IGNORECASE,
)


# =============================================================================
# VAGUE TIME PATTERNS
# =============================================================================

_VAGUE_EXPRESSIONS_SORTED = sorted(VAGUE_TIME_EXPRESSIONS.keys(), key=len, reverse=True)
VAGUE_TIME_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(expr) for expr in _VAGUE_EXPRESSIONS_SORTED) + r")\b",
    re.IGNORECASE,
)


# =============================================================================
# RANGE AND TIME PATTERNS
# =============================================================================

RANGE_PATTERNS = [
    re.compile(r"\b(tussen)\b\s+(?P<a>.+?)\s+\b(en)\b\s+(?P<b>.+)$", re.IGNORECASE),
    re.compile(
        r"\b(van|from)\b\s+(?P<a>.+?)\s+\b(tot|t/m|tm|to|until)\b\s+(?P<b>.+)$",
        re.IGNORECASE,
    ),
]

DASH_RANGE_PATTERN = re.compile(r"(?P<a>.+?)\s+-\s+(?P<b>.+)$")

TIME_HINT_PATTERN = re.compile(
    r"("
    r"\b\d{1,2}:\d{2}\b|"
    r"\b\d{1,2}\.\d{2}\b|"
    r"\b\d{1,2}\s*(am|pm)\b|"
    r"\b\d{1,2}\s*u\b|"
    r"\b\d{1,2}\s*uur\b|"
    r"\b(ochtend|middag|avond|nacht)\b|"
    r"\b(kwart\s+(voor|over)|half)\b"
    r")",
    re.IGNORECASE,
)

DATE_HINT_PATTERN = re.compile(
    r"("
    r"\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b|"
    r"\b\d{4}-\d{2}-\d{2}\b|"
    r"\b(jan(uari)?|feb(ruari)?|mrt|maart|apr(il)?|mei|jun(i)?|jul(i)?|aug(ustus)?|"
    r"sep(tember)?|okt(ober)?|nov(ember)?|dec(ember)?|"
    r"january|february|march|april|may|june|july|august|september|october|november|december)\b|"
    r"\b(maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b|"
    r"\b(vandaag|morgen|overmorgen|gisteren|eergisteren|today|tomorrow|yesterday)\b|"
    r"\b(volgende|komende|aanstaande|deze|vorige|afgelopen|next|this|last|previous)\b"
    r")",
    re.IGNORECASE,
)

DATE_EXTRACT_PATTERN = re.compile(
    r"(?:"
    r"\b\d{4}-\d{2}-\d{2}\b|"
    r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b|"
    r"\b(?:begin|start|eind|end)(?:\s+(?:van|of))?(?:\s+(?:het|the))?(?:\s+(?:jaar|year))?\s+\d{4}\b|"
    r"\b\d{1,2}(?:st|nd|rd|th|e|ste|de)?\s+(?:(?:van|of)\s+)?"
    r"(?:" + _MONTH_NAMES_REGEX + r")"
    r"(?:\s+\d{4})?\b|"
    r"\b(?:"
    + "|".join(
        re.escape(w) for w in sorted(DUTCH_NUMBER_WORDS.keys(), key=len, reverse=True)
    )
    + r")\s+"
    r"(?:(?:van|of)\s+)?"
    r"(?:" + _MONTH_NAMES_REGEX + r")"
    r"(?:\s+\d{4})?\b|"
    r"\b(?:volgende|komende|aanstaande|vorige|afgelopen|next|last|previous)\s+"
    r"(?:maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|week)\b|"
    r"\b(?:maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b|"
    r"\b(?:vandaag|morgen|overmorgen|gisteren|today|tomorrow|yesterday)\b"
    r")",
    re.IGNORECASE,
)

TIME_RANGE_PATTERN = re.compile(
    r"\b(van|from)\s+(\d{1,2}(?::\d{2})?)\s*(uur\s*)?(tot|to|until|-)\s*(\d{1,2}(?::\d{2})?)\s*(uur)?\b",
    re.IGNORECASE,
)


# =============================================================================
# DUTCH TIME PATTERNS
# =============================================================================

DUTCH_HOUR_PATTERN = re.compile(r"\b(\d{1,2})\s*uur\b", re.IGNORECASE)
DUTCH_HALF_PATTERN = re.compile(r"\bhalf\s+(\d{1,2})\b", re.IGNORECASE)
DUTCH_KWART_OVER_PATTERN = re.compile(r"\bkwart\s+over\s+(\d{1,2})\b", re.IGNORECASE)
DUTCH_KWART_VOOR_PATTERN = re.compile(r"\bkwart\s+voor\s+(\d{1,2})\b", re.IGNORECASE)
