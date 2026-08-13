import pytest
import os
import tempfile
from db import init_db, get_nearby_facilities, save_call_analytics, get_call_analytics

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    init_db(db_path=db_path)
    os.environ["HEALTHSATHI_DB_PATH"] = db_path
    yield db_path

    if "HEALTHSATHI_DB_PATH" in os.environ:
        del os.environ["HEALTHSATHI_DB_PATH"]

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except PermissionError:
        pass


def test_pune_hospitals_lookup(temp_db):
    """Test retrieving hospitals in Pune from database memory."""
    facilities = get_nearby_facilities("Pune", db_path=temp_db)
    assert len(facilities) >= 4
    names = [f["facility_name"] for f in facilities]
    assert any("Sassoon General Hospital" in n for n in names)
    assert any("PMC Urban Primary Health Centre" in n for n in names)


def test_nagpur_hospitals_lookup(temp_db):
    """Test retrieving hospitals in Nagpur from database memory."""
    facilities = get_nearby_facilities("Nagpur", db_path=temp_db)
    assert len(facilities) >= 4
    names = [f["facility_name"] for f in facilities]
    assert any("Government Medical College" in n for n in names)
    assert any("Mayo Hospital" in n for n in names)


def test_mumbai_hospitals_lookup(temp_db):
    """Test retrieving hospitals in Mumbai from database memory."""
    facilities = get_nearby_facilities("Mumbai", db_path=temp_db)
    assert len(facilities) >= 4
    names = [f["facility_name"] for f in facilities]
    assert any("King Edward Memorial" in n or "KEM" in n for n in names)
    assert any("Sion Hospital" in n for n in names)


def test_delhi_hospitals_lookup(temp_db):
    """Test retrieving hospitals in Delhi from database memory."""
    facilities = get_nearby_facilities("Delhi", db_path=temp_db)
    assert len(facilities) >= 4
    names = [f["facility_name"] for f in facilities]
    assert any("AIIMS Delhi" in n for n in names)
    assert any("Safdarjung Hospital" in n for n in names)
