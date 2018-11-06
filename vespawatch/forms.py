from django.forms import inlineformset_factory, ModelForm
from .models import ManagementAction, Nest, Individual, NestPicture, IndividualPicture


class IndividualForm(ModelForm):
    class Meta:
        model = Individual
        fields = ['species', 'individual_count', 'behaviour', 'location', 'latitude', 'longitude',
                  'inaturalist_id', 'observation_time', 'comments',
                  'observer_title', 'observer_last_name', 'observer_first_name', 'observer_email', 'observer_phone',
                  'observer_is_beekeeper', 'observer_approve_data_process', 'observer_approve_display',
                  'observer_approve_data_distribution'
        ]

    def save(self, *args, **kwargs):
        observation = super().save(*args, **kwargs)
        if hasattr(self.files, 'getlist'):
            for image in self.files.getlist('images'):
                IndividualPicture.objects.create(observation=observation, image=image)

class NestForm(ModelForm):
    class Meta:
        model = Nest
        fields = ['species', 'location', 'latitude', 'longitude',
                  'inaturalist_id', 'observation_time', 'comments',
                  'observer_title', 'observer_last_name', 'observer_first_name', 'observer_email', 'observer_phone',
                  'observer_is_beekeeper', 'observer_approve_data_process', 'observer_approve_display',
                  'observer_approve_data_distribution'
        ]

    def save(self, *args, **kwargs):
        observation = super().save(*args, **kwargs)
        if hasattr(self.files, 'getlist'):
            for image in self.files.getlist('images'):
                NestPicture.objects.create(observation=observation, image=image)

class IndividualPictureForm(ModelForm):
    class Meta:
        model = IndividualPicture
        fields = ['observation', 'image']


class NestPictureForm(ModelForm):
    class Meta:
        model = NestPicture
        fields = ['observation', 'image']


ImageFormset = inlineformset_factory(Individual, IndividualPicture, fields=('image',), extra=2)


class ManagementActionForm(ModelForm):
    class Meta:
        model = ManagementAction
        fields = ['nest', 'outcome', 'action_time', 'person_name']