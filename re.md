# MCP Client Test Report

Date: 2026-02-02 23:43:20

✅ Connected to `http://localhost:9000`

## 1. Initialization

- **Server Name**: `time-range-parser`

- **Server Version**: `1.26.0`

## 2. Available Tools

- **resolve_time_range**: 
Parse natural language date/time text into a start/end ISO-8601 range.
Returns the parsed range and the 'kind' of expression (e.g. 'time', 'date', 'period').

Output is SECOND resolution only (no microseconds).

Args:
    text: Natural language input (NL/EN).
    timezone: IANA timezone (default: Europe/Amsterdam)
    now_iso: Optional ISO timestamp as reference for relative expressions
    fiscal_start_month: Start month of the fiscal year (1-12). Default: 1 (January).

Returns:
    Dictionary with input, timezone, start, end (ISO-8601), and kind


- **resolve_time_range_simple**: 
Parse and return only start/end/timezone (minimal output).
Output is SECOND resolution only (no microseconds).


- **resolve_time_range_debug**: 
Parse and return extended debug output including all internal assumptions/metadata.
Logs full stack traces on error.
Output is SECOND resolution only (no microseconds).


- **convert_timezone**: 
Convert a date/time expression from one timezone to another.
Example: text="15:00", source="Amsterdam", target="New York"


- **expand_recurrence**: 
Generate a list of dates based on a recurrence rule.
Example: text="elke vrijdag", count=5 -> returns next 5 Fridays.


- **calculate_duration**: 
Calculate the duration between two dates/times.
Example: start="now", end="christmas" -> returns days/hours until christmas.


- **get_world_time**: 
Get the current time for a specific city or timezone via WorldTimeAPI.
Example: city="New York" -> returns current time in America/New_York.


- **server_info**: Basic server info for clients.

## 3. Tool: `resolve_time_range`

### From `test_time_range_parser.py`

**Input**: `morgen`
- **Arguments**: `text=morgen`
- **Result**:
```json
{
  "input": "morgen",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-03T00:00:00+01:00",
  "end": "2026-02-03T23:59:59+01:00",
  "kind": "date_whole_day"
}
```

---

**Input**: `morgen 15:00`
- **Arguments**: `text=morgen 15:00`
- **Result**:
```json
{
  "input": "morgen 15:00",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-03T15:00:00+01:00",
  "end": "2026-02-03T16:00:00+01:00",
  "kind": "time_with_default_duration"
}
```

---

**Input**: `van 10:00 tot 12:30`
- **Arguments**: `text=van 10:00 tot 12:30`
- **Result**:
```json
{
  "input": "van 10:00 tot 12:30",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-02T10:00:00+01:00",
  "end": "2026-02-02T12:30:00+01:00",
  "kind": "explicit_range"
}
```

---

**Input**: `tussen maandag en woensdag`
- **Arguments**: `text=tussen maandag en woensdag`
- **Result**:
```json
{
  "input": "tussen maandag en woensdag",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-02T00:00:00+01:00",
  "end": "2026-02-04T23:59:59+01:00",
  "kind": "explicit_range"
}
```

---

**Input**: `volgende week`
- **Arguments**: `text=volgende week`
- **Result**:
```json
{
  "input": "volgende week",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-09T00:00:00+01:00",
  "end": "2026-02-15T23:59:59+01:00",
  "kind": "future_period"
}
```

---

**Input**: `2025-11-01`
- **Arguments**: `text=2025-11-01`
- **Result**:
```json
{
  "input": "2025-11-01",
  "timezone": "Europe/Amsterdam",
  "start": "2025-11-01T00:00:00+01:00",
  "end": "2025-11-01T23:59:59+01:00",
  "kind": "date_whole_day"
}
```

---

**Input**: `5 januari 2026`
- **Arguments**: `text=5 januari 2026`
- **Result**:
```json
{
  "input": "5 januari 2026",
  "timezone": "Europe/Amsterdam",
  "start": "2026-01-05T00:00:00+01:00",
  "end": "2026-01-05T23:59:59+01:00",
  "kind": "dutch_day_month"
}
```

---

**Input**: `morgen 2 uur`
- **Arguments**: `text=morgen 2 uur`
- **Result**:
```json
{
  "input": "morgen 2 uur",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-03T02:00:00+01:00",
  "end": "2026-02-03T03:00:00+01:00",
  "kind": "time_with_default_duration"
}
```

---

**Input**: `van 22:00 tot 02:00`
- **Arguments**: `text=van 22:00 tot 02:00`
- **Result**:
```json
{
  "input": "van 22:00 tot 02:00",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-02T22:00:00+01:00",
  "end": "2026-02-03T02:00:00+01:00",
  "kind": "explicit_range"
}
```

---

**Input**: `half 10`
- **Arguments**: `text=half 10`
- **Result**:
```json
{
  "input": "half 10",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-03T09:30:00+01:00",
  "end": "2026-02-03T10:30:00+01:00",
  "kind": "time_with_default_duration"
}
```

---

**Input**: `vorig jaar`
- **Arguments**: `text=vorig jaar`
- **Result**:
```json
{
  "input": "vorig jaar",
  "timezone": "Europe/Amsterdam",
  "start": "2025-01-01T00:00:00+01:00",
  "end": "2025-12-31T23:59:59+01:00",
  "kind": "past_period"
}
```

---

**Input**: `tomorrow`
- **Arguments**: `text=tomorrow`
- **Result**:
```json
{
  "input": "tomorrow",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-03T00:00:00+01:00",
  "end": "2026-02-03T23:59:59+01:00",
  "kind": "date_whole_day"
}
```

---

**Input**: `1st of march`
- **Arguments**: `text=1st of march`
- **Result**:
```json
{
  "input": "1st of march",
  "timezone": "Europe/Amsterdam",
  "start": "2026-03-01T00:00:00+01:00",
  "end": "2026-03-01T23:59:59+01:00",
  "kind": "dutch_day_month"
}
```

---

**Input**: `29 februari`
- **Arguments**: `text=29 februari`
- **Result**:
```json
{
  "input": "29 februari",
  "timezone": "Europe/Amsterdam",
  "start": "2028-02-29T00:00:00+01:00",
  "end": "2028-02-29T23:59:59+01:00",
  "kind": "dutch_day_month"
}
```

---

### From `test_quarters_and_past_periods.py`

**Input**: `Q1`
- **Arguments**: `text=Q1`
- **Result**:
```json
{
  "input": "Q1",
  "timezone": "Europe/Amsterdam",
  "start": "2026-01-01T00:00:00+01:00",
  "end": "2026-03-31T23:59:59+02:00",
  "kind": "quarter"
}
```

---

**Input**: `Q4 2025`
- **Arguments**: `text=Q4 2025`
- **Result**:
```json
{
  "input": "Q4 2025",
  "timezone": "Europe/Amsterdam",
  "start": "2025-10-01T00:00:00+02:00",
  "end": "2025-12-31T23:59:59+01:00",
  "kind": "quarter"
}
```

---

**Input**: `eerste kwartaal`
- **Arguments**: `text=eerste kwartaal`
- **Result**:
```json
{
  "input": "eerste kwartaal",
  "timezone": "Europe/Amsterdam",
  "start": "2026-01-01T00:00:00+01:00",
  "end": "2026-03-31T23:59:59+02:00",
  "kind": "quarter"
}
```

---

**Input**: `afgelopen jaar`
- **Arguments**: `text=afgelopen jaar`
- **Result**:
```json
{
  "input": "afgelopen jaar",
  "timezone": "Europe/Amsterdam",
  "start": "2025-01-01T00:00:00+01:00",
  "end": "2025-12-31T23:59:59+01:00",
  "kind": "past_period"
}
```

---

**Input**: `vorige maand`
- **Arguments**: `text=vorige maand`
- **Result**:
```json
{
  "input": "vorige maand",
  "timezone": "Europe/Amsterdam",
  "start": "2026-01-01T00:00:00+01:00",
  "end": "2026-01-31T23:59:59+01:00",
  "kind": "past_period"
}
```

---

**Input**: `afgelopen week`
- **Arguments**: `text=afgelopen week`
- **Result**:
```json
{
  "input": "afgelopen week",
  "timezone": "Europe/Amsterdam",
  "start": "2026-01-26T00:00:00+01:00",
  "end": "2026-02-01T23:59:59+01:00",
  "kind": "past_period"
}
```

---

### From `test_vague_and_periods.py`

**Input**: `straks`
- **Arguments**: `text=straks`
- **Result**:
```json
{
  "input": "straks",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-03T01:43:22+01:00",
  "end": "2026-02-03T02:43:22+01:00",
  "kind": "vague_time"
}
```

---

**Input**: `vanavond`
- **Arguments**: `text=vanavond`
- **Result**:
```json
{
  "input": "vanavond",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-02T20:00:00+01:00",
  "end": "2026-02-02T22:00:00+01:00",
  "kind": "vague_time"
}
```

---

**Input**: `zomer 2026`
- **Arguments**: `text=zomer 2026`
- **Result**:
```json
{
  "input": "zomer 2026",
  "timezone": "Europe/Amsterdam",
  "start": "2026-06-01T00:00:00+02:00",
  "end": "2026-08-31T23:59:59+02:00",
  "kind": "season"
}
```

---

**Input**: `week 42`
- **Arguments**: `text=week 42`
- **Result**:
```json
{
  "input": "week 42",
  "timezone": "Europe/Amsterdam",
  "start": "2026-10-12T00:00:00+02:00",
  "end": "2026-10-18T23:59:59+02:00",
  "kind": "week_number"
}
```

---

**Input**: `H1`
- **Arguments**: `text=H1`
- **Result**:
```json
{
  "input": "H1",
  "timezone": "Europe/Amsterdam",
  "start": "2026-01-01T00:00:00+01:00",
  "end": "2026-06-30T23:59:59+02:00",
  "kind": "half_year"
}
```

---

**Input**: `dit weekend`
- **Arguments**: `text=dit weekend`
- **Result**:
```json
{
  "input": "dit weekend",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-07T00:00:00+01:00",
  "end": "2026-02-08T23:59:59+01:00",
  "kind": "weekend"
}
```

---

### From `test_holidays.py`

**Input**: `pasen 2026`
- **Arguments**: `text=pasen 2026`
- **Result**:
```json
{
  "input": "pasen 2026",
  "timezone": "Europe/Amsterdam",
  "start": "2026-04-05T00:00:00+02:00",
  "end": "2026-04-05T23:59:59+02:00",
  "kind": "moving_holiday"
}
```

---

**Input**: `goede vrijdag`
- **Arguments**: `text=goede vrijdag`
- **Result**:
```json
{
  "input": "goede vrijdag",
  "timezone": "Europe/Amsterdam",
  "start": "2026-04-03T00:00:00+02:00",
  "end": "2026-04-03T23:59:59+02:00",
  "kind": "moving_holiday"
}
```

---

**Input**: `hemelvaartsdag`
- **Arguments**: `text=hemelvaartsdag`
- **Result**:
```json
{
  "input": "hemelvaartsdag",
  "timezone": "Europe/Amsterdam",
  "start": "2026-05-14T00:00:00+02:00",
  "end": "2026-05-14T23:59:59+02:00",
  "kind": "moving_holiday"
}
```

---

**Input**: `eerste maandag van maart`
- **Arguments**: `text=eerste maandag van maart`
- **Result**:
```json
{
  "input": "eerste maandag van maart",
  "timezone": "Europe/Amsterdam",
  "start": "2026-03-02T00:00:00+01:00",
  "end": "2026-03-02T23:59:59+01:00",
  "kind": "ordinal_weekday"
}
```

---

**Input**: `laatste vrijdag van de maand`
- **Arguments**: `text=laatste vrijdag van de maand`
- **Result**:
```json
{
  "input": "laatste vrijdag van de maand",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-27T00:00:00+01:00",
  "end": "2026-02-27T23:59:59+01:00",
  "kind": "ordinal_weekday"
}
```

---

### From `test_coverage_gaps.py`

**Input**: `morgenochtend`
- **Arguments**: `text=morgenochtend`
- **Result**:
```json
{
  "input": "morgenochtend",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-03T06:00:00+01:00",
  "end": "2026-02-03T11:59:59+01:00",
  "kind": "compound_day"
}
```

---

**Input**: `binnenkort`
- **Arguments**: `text=binnenkort`
- **Result**:
```json
{
  "input": "binnenkort",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-02T00:00:00+01:00",
  "end": "2026-02-09T23:59:59+01:00",
  "kind": "vague_time"
}
```

---

**Input**: `begin januari 2026`
- **Arguments**: `text=begin januari 2026`
- **Result**:
```json
{
  "input": "begin januari 2026",
  "timezone": "Europe/Amsterdam",
  "start": "2026-01-01T00:00:00+01:00",
  "end": "2026-01-10T23:59:59+01:00",
  "kind": "month_expr"
}
```

---

## 4. Tool: `expand_recurrence`

### From `test_recurrence.py`

**Input**: `elke vrijdag`
- **Arguments**: `text=elke vrijdag`, `count=3`
- **Result**:
```json
{
  "input": "elke vrijdag",
  "timezone": "Europe/Amsterdam",
  "rule": {
    "interval": 1,
    "unit": "weeks",
    "weekday": 4
  },
  "dates": [
    "2026-02-06T00:00:00+01:00",
    "2026-02-13T00:00:00+01:00",
    "2026-02-20T00:00:00+01:00"
  ]
}
```

---

**Input**: `dagelijks`
- **Arguments**: `text=dagelijks`, `count=3`
- **Result**:
```json
{
  "input": "dagelijks",
  "timezone": "Europe/Amsterdam",
  "rule": {
    "interval": 1,
    "unit": "days",
    "weekday": null
  },
  "dates": [
    "2026-02-02T23:43:24.518615+01:00",
    "2026-02-03T23:43:24.518615+01:00",
    "2026-02-04T23:43:24.518615+01:00"
  ]
}
```

---

**Input**: `elke 2 weken`
- **Arguments**: `text=elke 2 weken`, `count=3`
- **Result**:
```json
{
  "input": "elke 2 weken",
  "timezone": "Europe/Amsterdam",
  "rule": {
    "interval": 2,
    "unit": "weeks",
    "weekday": null
  },
  "dates": [
    "2026-02-02T23:43:24.629334+01:00",
    "2026-02-16T23:43:24.629334+01:00",
    "2026-03-02T23:43:24.629334+01:00"
  ]
}
```

---

**Input**: `maandelijks`
- **Arguments**: `text=maandelijks`, `count=2`
- **Result**:
```json
{
  "input": "maandelijks",
  "timezone": "Europe/Amsterdam",
  "rule": {
    "interval": 1,
    "unit": "months",
    "weekday": null
  },
  "dates": [
    "2026-02-02T23:43:24.740175+01:00",
    "2026-03-02T23:43:24.740175+01:00"
  ]
}
```

---

## 5. Tool: `calculate_duration`

### From `test_duration.py`

**Input**: `vandaag`
- **Arguments**: `start=vandaag`, `end=volgende vrijdag`
- **Result**:
```json
{
  "input_start": "vandaag",
  "input_end": "volgende vrijdag",
  "timezone": "Europe/Amsterdam",
  "start_iso": "2026-02-02T00:00:00+01:00",
  "end_iso": "2026-02-13T00:00:00+01:00",
  "duration": {
    "total_days": 11.0,
    "total_seconds": 950400.0,
    "business_days": 9,
    "human_readable": "1 week 4 days"
  }
}
```

---

**Input**: `vandaag`
- **Arguments**: `start=vandaag`, `end=dinsdag`
- **Result**:
```json
{
  "input_start": "vandaag",
  "input_end": "dinsdag",
  "timezone": "Europe/Amsterdam",
  "start_iso": "2026-02-02T00:00:00+01:00",
  "end_iso": "2026-02-03T00:00:00+01:00",
  "duration": {
    "total_days": 1.0,
    "total_seconds": 86400.0,
    "business_days": 1,
    "human_readable": "1 day"
  }
}
```

---

**Input**: `13:00`
- **Arguments**: `start=13:00`, `end=16:30`
- **Result**:
```json
{
  "input_start": "13:00",
  "input_end": "16:30",
  "timezone": "Europe/Amsterdam",
  "start_iso": "2026-02-03T13:00:00+01:00",
  "end_iso": "2026-02-03T16:30:00+01:00",
  "duration": {
    "total_days": 0.14583333333333334,
    "total_seconds": 12600.0,
    "business_days": 0,
    "human_readable": "3 hours 30 minutes"
  }
}
```

---

## 6. Tool: `convert_timezone`

### From `test_timezone_conversion.py`

**Input**: `15:00`
- **Arguments**: `text=15:00`, `source_timezone=Amsterdam`, `target_timezone=New York`
- **Result**:
```json
{
  "input": "15:00",
  "source_timezone": "Europe/Amsterdam",
  "target_timezone": "America/New_York",
  "source_start": "2026-02-03T15:00:00+01:00",
  "target_start": "2026-02-03T09:00:00-05:00",
  "source_end": "2026-02-03T16:00:00+01:00",
  "target_end": "2026-02-03T10:00:00-05:00",
  "utc_offset_diff_hours": -6.0
}
```

---

**Input**: `12:00`
- **Arguments**: `text=12:00`, `source_timezone=London`, `target_timezone=Tokyo`
- **Result**:
```json
{
  "input": "12:00",
  "source_timezone": "Europe/London",
  "target_timezone": "Asia/Tokyo",
  "source_start": "2026-02-03T12:00:00+00:00",
  "target_start": "2026-02-03T21:00:00+09:00",
  "source_end": "2026-02-03T13:00:00+00:00",
  "target_end": "2026-02-03T22:00:00+09:00",
  "utc_offset_diff_hours": 9.0
}
```

---

## 7. Tool: `server_info`

### Server Metadata

**Tool**: `server_info`
- **Arguments**: 
- **Result**:
```json
{
  "name": "time-range-parser",
  "default_timezone": "Europe/Amsterdam",
  "resolution": "seconds",
  "tools": [
    "resolve_time_range",
    "resolve_time_range_simple",
    "resolve_time_range_debug",
    "convert_timezone",
    "expand_recurrence",
    "calculate_duration",
    "get_world_time",
    "server_info"
  ]
}
```

---

## 8. Deterministic Tests (`now_iso`)

### Fixed Reference Time (2026-01-01)

**Input**: `morgen`
- **Arguments**: `text=morgen`, `now_iso=2026-01-01T12:00:00`
- **Result**:
```json
{
  "input": "morgen",
  "timezone": "Europe/Amsterdam",
  "start": "2026-01-02T00:00:00+01:00",
  "end": "2026-01-02T23:59:59+01:00",
  "kind": "date_whole_day"
}
```

---

**Input**: `vorig kwartaal`
- **Arguments**: `text=vorig kwartaal`, `now_iso=2026-01-01T12:00:00`
- **Result**:
```json
{
  "input": "vorig kwartaal",
  "timezone": "Europe/Amsterdam",
  "start": "2025-10-01T00:00:00+02:00",
  "end": "2025-12-31T23:59:59+01:00",
  "kind": "relative_quarter"
}
```

---

## 9. Tool: `resolve_time_range_debug`

### Debug Output (Assumptions)

**Input**: `morgen`
- **Arguments**: `text=morgen`
- **Result**:
```json
{
  "input": "morgen",
  "timezone": "Europe/Amsterdam",
  "start": "2026-02-03T00:00:00+01:00",
  "end": "2026-02-03T23:59:59+01:00",
  "assumptions": {
    "kind": "date_whole_day",
    "base_now": "2026-02-02T23:43:25.761061+01:00"
  }
}
```

---

