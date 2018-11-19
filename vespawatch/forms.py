from django.forms import inlineformset_factory, ModelForm, BooleanField

from vespawatch.fields import ISODateTimeField
from .models import ManagementAction, Nest, Individual, NestPicture, IndividualPicture


class IndividualForm(ModelForm):
    terms_of_service = BooleanField(label='Accept the terms of service', required=False)   # TODO how to translate that label?

    class Meta:
        model = Individual
        fields = ['species', 'individual_count', 'behaviour', 'location', 'latitude', 'longitude',
                  'inaturalist_id', 'observation_time', 'comments',
                  'observer_title', 'observer_last_name', 'observer_first_name', 'observer_email', 'observer_phone',
                  'observer_is_beekeeper'
        ]
        field_classes = {
            'observation_time': ISODateTimeField,
        }

    def clean(self):
        cleaned_data = self.cleaned_data
        toc = cleaned_data.get('terms_of_service')
        print('Toc: {}'.format(toc))
        if not toc:
            msg = "You must accept the terms of service."
            self.add_error('terms_of_service', msg)
        return cleaned_data

    def save(self, *args, **kwargs):
        observation = super().save(*args, **kwargs)
        if hasattr(self.files, 'getlist'):
            for image in self.files.getlist('images'):
                IndividualPicture.objects.create(observation=observation, image=image)

class NestForm(ModelForm):
    terms_of_service = BooleanField(label='Accept the terms of service', required=False)   # TODO how to translate that label?

    class Meta:
        model = Nest
        fields = ['species', 'location', 'latitude', 'longitude',
                  'inaturalist_id', 'observation_time', 'comments',
                  'observer_title', 'observer_last_name', 'observer_first_name', 'observer_email', 'observer_phone',
                  'observer_is_beekeeper'
        ]
        field_classes = {
            'observation_time': ISODateTimeField,
        }

    def clean(self):
        cleaned_data = self.cleaned_data
        toc = cleaned_data.get('terms_of_service')
        print('Toc: {}'.format(toc))
        if not toc:
            msg = "You must accept the terms of service."
            self.add_error('terms_of_service', msg)
        return cleaned_data

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


IndividualImageFormset = inlineformset_factory(Individual, IndividualPicture, fields=('image',), extra=2)
NestImageFormset = inlineformset_factory(Nest, NestPicture, fields=('image',), extra=2)
ManagementFormset = inlineformset_factory(Nest, ManagementAction, fields=('outcome', 'action_time', 'person_name'), extra=1, max_num=1)

class ManagementActionForm(ModelForm):
    class Meta:
        model = ManagementAction
        fields = ['nest', 'outcome', 'action_time', 'person_name']