from django.forms import inlineformset_factory, ModelForm
from .models import ManagementAction, Observation, ObservationPicture


class ObservationForm(ModelForm):
    class Meta:
        model = Observation
        fields = ['species', 'individual_count', 'behaviour', 'subject', 'location', 'latitude', 'longitude',
                  'inaturalist_id', 'observation_time', 'comments',
                  'observer_title', 'observer_last_name', 'observer_first_name', 'observer_email', 'observer_phone',
                  'observer_is_beekeeper', 'observer_approve_data_process', 'observer_approve_display',
                  'observer_approve_data_distribution'
        ]

    def save(self, *args, **kwargs):
        observation = super().save(*args, **kwargs)
        if hasattr(self.files, 'getlist'):
            for image in self.files.getlist('images'):
                ObservationPicture.objects.create(observation=observation, image=image)

class ObservationPictureForm(ModelForm):
    class Meta:
        model = ObservationPicture
        fields = ['observation', 'image']


ImageFormset = inlineformset_factory(Observation, ObservationPicture, fields=('image',), extra=2)


class ManagementActionForm(ModelForm):
    class Meta:
        model = ManagementAction
        fields = ['observation', 'outcome', 'action_time', 'person_name']