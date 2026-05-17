from app.services.pii_engine import validate_verhoeff, validate_gstin_checksum

aadhaar = "5421 8890 1234"
gstin = "27AAAAA0000A1Z5"
pan = "BKXPS1234Z"

print(f"Aadhaar '{aadhaar}' Verhoeff Valid: {validate_verhoeff(aadhaar)}")
print(f"GSTIN '{gstin}' Checksum Valid: {validate_gstin_checksum(gstin)}")

# PAN validation is mostly structural in our engine, but let's check status char
status_char = pan[3]
print(f"PAN '{pan}' Status Char '{status_char}' Valid: {status_char in 'PCHFABTLJG'}")
