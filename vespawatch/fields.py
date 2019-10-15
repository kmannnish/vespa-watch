from django import forms
from django.utils.dateparse import parse_datetime
from django.utils.encoding import force_str
from django.forms.widgets import DateTimeInput
from django.utils.translation import gettext_lazy as _


class ISODateTimeField(forms.Field):
    """DateTimeField that uses django.utils.dateparse.parse_datetime.
    More precisely, this DateTimeField accepts ISO 8601 datetime strings
    that specify timezone with +00:00 syntax.
    https://en.wikipedia.org/wiki/ISO_8601
    https://code.djangoproject.com/ticket/11385
    https://bugs.python.org/issue15873
    https://bugs.python.org/msg169952
    """
    widget = DateTimeInput
    default_error_messages = {
        'invalid': _('Enter a valid date/time.'),
    }
    def to_python(self, value):
        value = value.strip()
        try:
            return self.strptime(value, format)
        except (ValueError, TypeError):
            raise forms.ValidationError(self.error_messages['invalid'], code='invalid')

    def strptime(self, value, format):
        return parse_datetime(force_str(value))