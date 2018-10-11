import dateparser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse


class Species(models.Model):
    name = models.CharField(max_length=100)

    vernacular_name = models.CharField(max_length=100, blank=True)

    inaturalist_push_taxon_id = models.BigIntegerField(null=True, blank=True,
                                                       help_text="When pushing an observation to iNaturalist, we'll "
                                                                 "use this taxon_id")
    inaturalist_pull_taxon_ids = ArrayField(models.BigIntegerField(), blank=True, null=True,
                                            help_text="When pulling observations from iNaturalist, reconcile according "
                                                      "to those IDs.")

    def __str__(self):
        return  self.name

    class Meta:
        verbose_name_plural = "species"



class InatCreatedObservationsManager(models.Manager):
    """The queryset only contains observations that originates from iNaturalist (NOT Vespa-Watch)"""
    def get_queryset(self):
        return super().get_queryset().filter(originates_in_vespawatch=False)


class VespawatchCreatedObservationsManager(models.Manager):
    """The queryset only contains observations that originates from Vespa-Watch"""
    def get_queryset(self):
        return super().get_queryset().filter(originates_in_vespawatch=True)


class SpeciesMatchError(Exception):
    """Unable to match this (iNaturalist) taxon id to our Species table"""

class ParseDateError(Exception):
    """Cannot parse this date"""

def create_observation_from_inat_data(inaturalist_data):
    """ Creates an observation in our local database according to the data from iNaturalist API

    Raises:
        SpeciesMatchError
    """
    observation_time = dateparser.parse(inaturalist_data['observed_on_string'])

    if observation_time:
        # TODO: species: we have to reconcile with our Species table

        try:
            species = Species.objects.get(inaturalist_pull_taxon_ids__contains=[inaturalist_data['taxon']['id']])
        except Species.DoesNotExist:
            raise SpeciesMatchError

        Observation.objects.create(
            originates_in_vespawatch=False,
            subject=Observation.SPECIMEN,  # TODO: How to detect/manage properly?
            inaturalist_id=inaturalist_data['id'],
            species=species,
            latitude=inaturalist_data['geojson']['coordinates'][1],
            longitude=inaturalist_data['geojson']['coordinates'][0],
            observation_time=observation_time)  # TODO: What to do with iNat observations without (parsable) time?
    else:
        raise ParseDateError

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

    # Managers
    objects = models.Manager()  # The default manager.
    from_inat_objects = InatCreatedObservationsManager()
    from_vespawatch_objects = VespawatchCreatedObservationsManager()

    @property
    def can_be_edited_or_deleted(self):
        """Return True if this observation can be edited in Vespa-Watch (admin, ...)"""
        return self.originates_in_vespawatch  # We can't edit obs that comes from iNaturalist (they're never pushed).

    # Fields
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
