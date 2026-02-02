import pytest
from date_textparser import parse_time_range_full

def test_now_iso_determinism():
    """
    Test dat 'now_iso' de referentietijd bevriest voor deterministische output.
    Dit is cruciaal voor Text-to-SQL en regressietests.
    """
    # Scenario: Het is 1 januari 2026
    fixed_now = "2026-01-01T12:00:00"
    
    # 1. "Vorig kwartaal" moet Q4 2025 zijn
    # (Dit verifieert ook de fix voor 'vorig kwartaal')
    result = parse_time_range_full("vorig kwartaal", now_iso=fixed_now)
    assert result.start.to_date_string() == "2025-10-01"
    assert result.end.to_date_string() == "2025-12-31"
    
    # 2. "Morgen" moet 2 januari 2026 zijn
    result = parse_time_range_full("morgen", now_iso=fixed_now)
    assert result.start.to_date_string() == "2026-01-02"
    
    # 3. "Over 3 dagen"
    result = parse_time_range_full("over 3 dagen", now_iso=fixed_now)
    # 1 jan + 3 dagen = 4 jan
    assert result.start.to_date_string() == "2026-01-04"

def test_now_iso_timezone_handling():
    """
    Test dat now_iso correct naar de target tijdzone wordt omgezet.
    """
    # Input is UTC (Z) -> 10:00 UTC
    utc_now = "2026-01-01T10:00:00Z" 
    
    # Target is Amsterdam (UTC+1 in winter) -> 11:00 lokaal
    # Als we vragen om "12:00", en het is nu 11:00 lokaal, dan is dat VANDAAG nog.
    
    result = parse_time_range_full("12:00", tz="Europe/Amsterdam", now_iso=utc_now)
    
    assert result.start.year == 2026
    assert result.start.month == 1
    assert result.start.day == 1
    assert result.start.hour == 12