import uuid


def make_unique_filename(initial_filename):
    """Add a random part to a filename so it's unique. File extension is preserved."""
    before_ext, ext = initial_filename.split('.')
    random_part = uuid.uuid4()
    return f"{before_ext}-{random_part}.{ext}"