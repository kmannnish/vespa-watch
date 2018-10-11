from django.forms import ModelForm, ImageField, ClearableFileInput
from .models import ManagementAction, Observation, ObservationPicture

class PublicObservationForm(ModelForm):
    images = ImageField(required=False, widget=ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = Observation
        fields = ['species', 'individual_count', 'behaviour', 'subject', 'location', 'latitude', 'longitude',
                  'inaturalist_id', 'observation_time', 'comments',
                  'observer_title', 'observer_last_name', 'observer_first_name', 'observer_email', 'observer_phone',
                  'observer_is_beekeeper', 'observer_approve_data_process', 'observer_approve_display',
                  'observer_approve_data_distribution'
        ]

    def save(self, *args, **kwargs):
        public_observation = super(PublicObservationForm, self).save(*args, **kwargs)
        if hasattr(self.files, 'getlist'):
            for image in self.files.getlist('images'):
                ObservationPicture.objects.create(observation=public_observation, image=image)


class ObservationForm(ModelForm):
    images = ImageField(required=False, widget=ClearableFileInput(attrs={'multiple': True}))

    class Meta:
        model = Observation
        fields = ['species', 'individual_count', 'behaviour', 'subject', 'location', 'latitude', 'longitude',
                  'inaturalist_id', 'observation_time', 'comments'
        ]

    def save(self, *args, **kwargs):
        public_observation = super(ObservationForm, self).save(*args, **kwargs)
        if hasattr(self.files, 'getlist'):
            for image in self.files.getlist('images'):
                ObservationPicture.objects.create(observation=public_observation, image=image)



class ManagementActionForm(ModelForm):
    class Meta:
        model = ManagementAction
        fields = ['observation', 'outcome', 'action_time', 'person_name']