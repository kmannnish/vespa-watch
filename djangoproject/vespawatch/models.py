from django.db import models
from django.urls import reverse


class Species(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return  self.name

    class Meta:
        verbose_name_plural = "species"


class Observation(models.Model):
    NEST = 'NE'
    SPECIMEN = 'SP'

    SUBJECT_CHOICES = (
        (NEST, 'Nest'),
        (SPECIMEN, 'Specimen'),
    )

    FOURAGING = 'FO'
    HUNTING = 'HU'
    FLOWER = 'FL'
    OTHER = 'OT'
    BEHAVIOUR_CHOICES = (
        (FOURAGING, 'Fouraging'),
        (HUNTING, 'Hunting at hive'),
        (FLOWER, 'At flower'),
        (OTHER, 'Other')
    )

    species = models.ForeignKey(Species, on_delete=models.PROTECT, blank=True, null=True)  # Blank allows because some nests can't be easily identified
    individual_count = models.IntegerField(blank=True, null=True)
    behaviour = models.CharField(max_length=2, choices=BEHAVIOUR_CHOICES, blank=True, null=True)
    subject = models.CharField(max_length=2, choices=SUBJECT_CHOICES)
    location = models.CharField(max_length=255, blank=True)
    observation_time = models.DateTimeField()
    comments = models.TextField(blank=True)

    latitude = models.FloatField()
    longitude = models.FloatField()

    inaturalist_id = models.BigIntegerField(blank=True, null=True)
    inaturalist_species = models.CharField(max_length=100, blank=True, null=True)

    originates_in_vespawatch = models.BooleanField(default=True, help_text="The observation was first created in VespaWatch, not iNaturalist")

    # Observer info
    observer_title = models.CharField(max_length=50, blank=True, null=True)
    observer_last_name = models.CharField(max_length=255, blank=True, null=True)
    observer_first_name = models.CharField(max_length=255, blank=True, null=True)
    observer_email = models.EmailField(blank=True, null=True)
    observer_phone = models.CharField(max_length=20, blank=True, null=True)
    observer_is_beekeeper = models.NullBooleanField()
    observer_approve_data_process = models.NullBooleanField(help_text='The observer approves that his data will be processed by Vespa-Watch')
    observer_approve_display = models.NullBooleanField(help_text='The observer approves that the observation will be displayed on the Vespa-Watch map')
    observer_approve_data_distribution = models.NullBooleanField(help_text='The observer approves that the recorded observation will be distributed to third parties')

    @property
    def exists_in_inaturalist(self):
        return self.inaturalist_id is not None

    def get_absolute_url(self):
        return reverse('vespawatch:observation-update', kwargs={'pk': self.pk})

    def as_dict(self):
        return {
            'id': self.pk,
            'species': self.inaturalist_species if self.inaturalist_species else self.species.name,
            'subject': self.get_subject_display(),
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'inaturalist_id': self.inaturalist_id,
            'observation_time': self.observation_time.timestamp() * 1000,
            'comments': self.comments,
            'imageUrls': [x.image.url for x in self.observationpicture_set.all()]
        }

    def __str__(self):
        return f'{self.get_subject_display()} of {self.species.name}, {self.observation_time.strftime("%Y-%m-%d")}'


class ObservationPicture(models.Model):
    observation = models.ForeignKey(Observation, on_delete=models.PROTECT)
    image = models.ImageField(upload_to='observation_pictures/')


class ManagementAction(models.Model):
    FULL_DESTRUCTION_NO_DEBRIS = 'FD'
    PARTIAL_DESTRUCTION_DEBRIS_LEFT = 'PD'
    EMPTY_NEST_NOTHING_DONE = 'ND'

    OUTCOME_CHOICE = (
        (FULL_DESTRUCTION_NO_DEBRIS, 'Full destruction, no debris'),
        (PARTIAL_DESTRUCTION_DEBRIS_LEFT, 'Partial destruction/debris left'),
        (EMPTY_NEST_NOTHING_DONE, 'Empty nest, nothing done'),
    )

    observation = models.ForeignKey(Observation, on_delete=models.PROTECT)
    outcome = models.CharField(max_length=2, choices=OUTCOME_CHOICE)
    action_time = models.DateTimeField()
    person_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f'{self.action_time.strftime("%Y-%m-%d")} {self.get_outcome_display()} on {self.observation}'
