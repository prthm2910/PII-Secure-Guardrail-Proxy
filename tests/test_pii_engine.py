import pytest
from app.services.pii_engine import pii_engine

def test_aadhaar_valid_detection():
    # Valid Aadhaar with Verhoeff: 366215485509
    text = "My Aadhaar is 366215485509"
    results = pii_engine.analyze(text)
    entities = [res.entity_type for res in results]
    assert "IN_AADHAAR" in entities

def test_aadhaar_invalid_detection():
    # Invalid Aadhaar (e.g., 123412341234)
    text = "My fake Aadhaar is 123412341234"
    results = pii_engine.analyze(text)
    entities = [res.entity_type for res in results]
    assert "IN_AADHAAR" not in entities

def test_upi_detection():
    text = "Pay me at prathamesh@ybl"
    results = pii_engine.analyze(text)
    entities = [res.entity_type for res in results]
    assert "IN_UPI" in entities

def test_pan_detection():
    # Valid PAN with Individual status 'P' at index 3: ABCPE1234F
    text = "My PAN is ABCPE1234F"
    results = pii_engine.analyze(text)
    entities = [res.entity_type for res in results]
    assert "IN_PAN" in entities

def test_mixed_pii():
    # Valid PAN with Individual status 'P' at index 3: ABCPE1234F
    text = "Name: John Doe, PAN: ABCPE1234F, Email: john@doe.com"
    results = pii_engine.analyze(text)
    entities = [res.entity_type for res in results]
    assert "PERSON" in entities
    assert "IN_PAN" in entities
    assert "EMAIL_ADDRESS" in entities
