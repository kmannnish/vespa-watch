from django.forms import inlineformset_factory, ModelForm, BooleanField, ChoiceField, IntegerField, forms
from vespawatch.fields import ISODateTimeField
from .models import ManagementAction, Nest, Individual, NestPicture, IndividualPicture


class IndividualForm(ModelForm):
    redirect_to = ChoiceField(choices=(('index', 'index'), ('management', 'management')), initial='index')
    card_id = IntegerField()
    terms_of_service = BooleanField(label='Accept the terms of service', required=False)   # TODO how to translate that label?

    class Meta:
        model = Individual
        fields = ['taxon', 'individual_count', 'behaviour', 'address', 'latitude', 'longitude',
                  'observation_time', 'comments',
                  'observer_last_name', 'observer_first_name', 'observer_email', 'observer_phone',
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
    def __init__(self, *args, **kwargs):
        self.new_nest_from_anonymous = kwargs.pop('new_nest_from_anonymous', False)
        super().__init__(*args, **kwargs)

    redirect_to = ChoiceField(choices=(('index', 'index'), ('management', 'management')), initial='index')
    card_id = IntegerField()
    terms_of_service = BooleanField(label='Accept the terms of service', required=False)   # TODO how to translate that label?

    class Meta:
        model = Nest
        fields = ['taxon', 'address', 'latitude', 'longitude',
                  'observation_time', 'size', 'height', 'comments',
                  'observer_last_name', 'observer_first_name', 'observer_email', 'observer_phone',
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

        # If it's for announcing a new nest from an anonymous user, we'll need some contact info
        observer_email = cleaned_data.get('observer_email')
        if self.new_nest_from_anonymous and not observer_email:
            self.add_error('observer_email', 'Observer email is mandatory')

        observer_phone = cleaned_data.get('observer_phone')
        if self.new_nest_from_anonymous and not observer_phone:
            self.add_error('observer_phone', 'Observer phone is mandatory')

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

class ManagementActionForm(ModelForm):
    class Meta:
        model = ManagementAction
        fields = ['nest', 'outcome', 'action_time', 'duration', 'person_name']

        field_classes = {
            'action_time': ISODateTimeField,
        }