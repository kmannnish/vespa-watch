import json

from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def js_config_object():
    conf = {
        'apis': {
            'observationsUrl': reverse('vespawatch:api_observations'),
            'actionOutcomesUrl': reverse('vespawatch:api_action_outcomes'),
            'actionSaveUrl': reverse('vespawatch:api_action_save'),
            'actionLoadUrl': reverse('vespawatch:api_action_get'),
            'actionDeleteUrl': reverse('vespawatch:api_action_delete')
        },
        'map': {
            'circle': {
                'fill_opacity': settings.MAP_CIRCLE_FILL_OPACITY,
                'stroke_opacity': settings.MAP_CIRCLE_STROKE_OPACITY,
                'stroke_width': settings.MAP_CIRCLE_STROKE_WIDTH
            }
        }
    }
    return mark_safe(json.dumps(conf))