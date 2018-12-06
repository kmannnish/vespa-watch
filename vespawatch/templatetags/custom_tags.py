import json

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def js_config_object():
    conf = {
        'apis': {
            'actionOutcomesUrl': reverse('vespawatch:api_action_outcomes')
        }
    }
    return mark_safe(json.dumps(conf))