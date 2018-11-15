import os
import uuid
import secrets
import string

def make_unique_filename(initial_filename):
    """Add a random part to a filename so it's unique. File extension is preserved."""
    before_ext, ext = os.path.splitext(initial_filename)
    random_part = uuid.uuid4()
    return f"{before_ext}-{random_part}.{ext}"

def make_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))