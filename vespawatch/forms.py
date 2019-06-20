from django.forms import inlineformset_factory, ModelForm, BooleanField, ChoiceField, IntegerField, EmailField, CharField
from django.utils.translation import ugettext_lazy as _
from vespawatch.fields import ISODateTimeField
from .models import ManagementAction, Nest, Individual, NestPicture, IndividualPicture


class IndividualForm(ModelForm):
    redirect_to = ChoiceField(choices=(('index', 'index'), ('management', 'management')), initial='index')
    card_id = IntegerField()
    terms_of_service = BooleanField(label=_('Accept the privacy policy'), required=False)
    image_ids = CharField(max_length=255)

    class Meta:
        model = Individual
        fields = ['taxon', 'individual_count', 'behaviour', 'address', 'latitude', 'longitude',
                  'observation_time', 'comments',
                  'observer_name', 'observer_email', 'observer_phone'
        ]
        field_classes = {
            'observation_time': ISODateTimeField,
        }

    def clean(self):
        cleaned_data = self.cleaned_data
        toc = cleaned_data.get('terms_of_service')
        print('Toc: {}'.format(toc))
        if not toc:
            msg = _("You must accept the privacy policy.")
            self.add_error('terms_of_service', msg)
        if not cleaned_data['image_ids']:
            msg = 'You must add at least one picture'
            self.add_error(None, msg)

        return cleaned_data

    def save(self, *args, **kwargs):
        observation = super().save(*args, **kwargs)
        image_ids = [x for x in self.cleaned_data['image_ids'].strip().split(',') if x]
        for image_id in image_ids:
            np = IndividualPicture.objects.get(pk=image_id)
            np.observation = observation
            np.save()


class IndividualFormUnauthenticated(IndividualForm):
    observer_email = EmailField(label=_('Email address'))

    class Meta:
        model = Individual
        fields = ['taxon', 'individual_count', 'behaviour', 'address', 'latitude', 'longitude',
                  'observation_time', 'comments',
                  'observer_email', 'observer_name', 'observer_phone',
        ]
        field_classes = {
            'observation_time': ISODateTimeField,
        }


class NestForm(ModelForm):
    redirect_to = ChoiceField(choices=(('index', 'index'), ('management', 'management')), initial='index')
    card_id = IntegerField()
    height = ChoiceField(label=_('Nest height'), choices=[('', '--------')] + list(Nest.HEIGHT_CHOICES))
    address = CharField(max_length=255)
    image_ids = CharField(max_length=255)

    class Meta:
        model = Nest
        fields = ['taxon', 'address', 'latitude', 'longitude',
                  'observation_time', 'size', 'height', 'comments',
                  'observer_name', 'observer_email', 'observer_phone'
        ]
        field_classes = {
            'observation_time': ISODateTimeField,
        }

    def clean(self):
        cleaned_data = self.cleaned_data

        if not cleaned_data['image_ids']:
            msg = 'You must add at least one picture'
            self.add_error(None, msg)
        return cleaned_data

    def save(self, *args, **kwargs):
        observation = super().save(*args, **kwargs)
        image_ids = [x for x in self.cleaned_data['image_ids'].strip().split(',') if x]
        for image_id in image_ids:
            np = NestPicture.objects.get(pk=image_id)
            np.observation = observation
            np.save()


class NestFormUnauthenticated(NestForm):
    observer_name = CharField(label=_('Name'), max_length=255)
    observer_email = EmailField(label=_('Email address'))
    observer_phone = CharField(label=_('Telephone number'), max_length=20)
    terms_of_service = BooleanField(label=_('Accept the privacy policy'))

    class Meta:
        model = Nest
        fields = ['taxon', 'address', 'latitude', 'longitude',
                  'observation_time', 'size', 'height', 'comments',
                  'observer_email', 'observer_name', 'observer_phone'
        ]
        field_classes = {
            'observation_time': ISODateTimeField,
        }

    def clean(self):
        cleaned_data = super().clean()

        toc = cleaned_data.get('terms_of_service')
        if not toc:
            msg = _("You must accept the privacy policy.")
            self.add_error('terms_of_service', msg)

        return cleaned_data

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