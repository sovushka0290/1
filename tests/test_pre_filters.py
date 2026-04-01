import math
import pytest
from core.ai_engine import verify_geo, verify_timestamp

def test_verify_geo():
    # AKT Hub: 50.28, 57.18
    # Within 1km
    assert verify_geo(50.28, 57.18, 50.2801, 57.1801, 1) == True
    # Too far (10km)
    assert verify_geo(50.28, 57.18, 50.38, 57.28, 1) == False

def test_verify_timestamp():
    # Format: ISO 8601
    from datetime import datetime, timedelta
    now_str = datetime.utcnow().isoformat()
    old_str = (datetime.utcnow() - timedelta(hours=50)).isoformat()
    
    assert verify_timestamp(now_str, max_hours=48) == True
    assert verify_timestamp(old_str, max_hours=48) == False
