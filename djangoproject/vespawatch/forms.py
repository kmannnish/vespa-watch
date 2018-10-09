from django.forms import ModelForm
from .models import Observation

class PublicObservationForm(ModelForm):
    class Meta:
        model = Observation
        fields = ['species', 'individual_count', 'behaviour', 'subject', 'nest_location', 'latitude', 'longitude',
                  'inaturalist_id', 'observation_time', 'comments',
                  'observer_title', 'observer_last_name', 'observer_first_name', 'observer_email', 'observer_phone',
                  'observer_is_beekeeper', 'observer_approve_data_process', 'observer_approve_display',
                  'observer_approve_data_distribution'
        ]


class ObservationForm(ModelForm):
    class Meta:
        model = Observation
        fields = ['species', 'individual_count', 'behaviour', 'subject', 'nest_location', 'latitude', 'longitude',
                  'inaturalist_id', 'observation_time', 'comments'
        ]
