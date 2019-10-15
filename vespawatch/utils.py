import functools
import os
import uuid
import secrets
import string

from django.http import JsonResponse


def make_unique_filename(initial_filename):
    """Add a random part to a filename so it's unique. File extension is preserved."""
    before_ext, ext = os.path.splitext(initial_filename)
    ext = ext.replace('.', '')  # Remove the dot, if already there.
    random_part = uuid.uuid4()
    return f"{before_ext}-{random_part}.{ext}"


def make_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))


def ajax_login_required(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        return JsonResponse('Unauthorized', status=401, safe=False)

    return wrapper