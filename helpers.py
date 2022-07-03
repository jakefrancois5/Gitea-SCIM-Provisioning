import string
import secrets

LEGAL_ORG_CHARS = string.ascii_letters + string.digits + "-_."

def generate_password():
    return secrets.token_urlsafe(32)
