import os
import uuid
from datetime import datetime

import dateparser
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.timezone import is_naive, make_aware
from pyinaturalist.rest_api import create_observations, update_observation


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
    observation_time = dateparser.parse(inaturalist_data['observed_on_string'],
                                        settings={'TIMEZONE': inaturalist_data['observed_time_zone']})
    if observation_time is None:
        # Sometimes, dateparser doesn't understand the string but we have the bits and pieces in
        # inaturalist_data['observed_on_details']
        details = inaturalist_data['observed_on_details']
        observation_time = datetime(year=details['year'],
                                    month=details['month'],
                                    day=details['day'],
                                    hour=details['hour'])  # in the observed cases, we had nothing more precise than the
                                                           # hour

    # Sometimes, the time is naive (even when specifying it to dateparser), because (for the detected cases, at least)
    # The time is 00:00:00. In that case we make it aware to avoid Django warnings (in the local time zone since all
    # observations occur in Belgium
    if is_naive(observation_time):
        # Some dates (apparently)
        observation_time = make_aware(observation_time)

    if observation_time:
        # Reconcile the species
        try:
            species = Species.objects.get(inaturalist_pull_taxon_ids__contains=[inaturalist_data['taxon']['id']])
        except Species.DoesNotExist:
            raise SpeciesMatchError

        # Check if it has the vespawatch_evidence observation field value and if it's set to "nest"
        is_nest_ofv = next((item for item in inaturalist_data['ofvs'] if item["field_id"] == settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID), None)
        if is_nest_ofv and is_nest_ofv['value'] == "nest":
            Nest.objects.create(
                originates_in_vespawatch=False,
                inaturalist_id=inaturalist_data['id'],
                species=species,
                latitude=inaturalist_data['geojson']['coordinates'][1],
                longitude=inaturalist_data['geojson']['coordinates'][0],
                observation_time=observation_time)  # TODO: What to do with iNat observations without (parsable) time?
        else:  # Default is specimen
            Individual.objects.create(
                originates_in_vespawatch=False,
                inaturalist_id=inaturalist_data['id'],
                species=species,
                latitude=inaturalist_data['geojson']['coordinates'][1],
                longitude=inaturalist_data['geojson']['coordinates'][0],
                observation_time=observation_time)  # TODO: What to do with iNat observations without (parsable) time?
    else:
        raise ParseDateError

def update_loc_obs_taxon_according_to_inat(inaturalist_data):
    """Takes data coming from iNaturalist about one of our local observation, and update the taxon of said local obs,
    if necessary."""
    pass

def inat_observation_comes_from_vespawatch(inat_observation_id):
    """ Takes an observation_id from iNat API and returns True if this observation was first created from the
    VespaWatch website.

    Slow, since we need an API call to retrieve the observation_field_values
    """

    #TODO: implement
    return False
    # if 'observation_field_values' in inat_observation:
    #     for ofv in inat_observation['observation_field_values']:
    #         if ofv['observation_field_id'] == settings.OBSERVATION_FIELD_ID:
    #             return True
    #
    # return False


class AbstractObservation(models.Model):
    originates_in_vespawatch = models.BooleanField(default=True, help_text="The observation was first created in VespaWatch, not iNaturalist")
    species = models.ForeignKey(Species, on_delete=models.PROTECT, blank=True, null=True)  # Blank allows because some nests can't be easily identified
    location = models.CharField(max_length=255, blank=True)
    observation_time = models.DateTimeField()
    comments = models.TextField(blank=True)

    latitude = models.FloatField()
    longitude = models.FloatField()

    inaturalist_id = models.BigIntegerField(blank=True, null=True)
    inaturalist_species = models.CharField(max_length=100, blank=True, null=True)

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

    # Managers
    objects = models.Manager()  # The default manager.
    from_inat_objects = InatCreatedObservationsManager()
    from_vespawatch_objects = VespawatchCreatedObservationsManager()

    class Meta:
        abstract = True

    @property
    def can_be_edited_or_deleted(self):
        """Return True if this observation can be edited in Vespa-Watch (admin, ...)"""
        return self.originates_in_vespawatch  # We can't edit obs that comes from iNaturalist (they're never pushed).

    @property
    def exists_in_inaturalist(self):
        return self.inaturalist_id is not None

    def _params_for_inat(self):
        """(Create/update): Common ground for the pushed data to iNaturalist.

        taxon_id is not part of it because we rely on iNaturalist to correct the identification, if necessary.
        All the rest is pushed.
        """

        vespawatch_evidence_value = 'nest' if self.__name__ == 'Nest' else 'individual'

        return {'observed_on_string': self.observation_time.isoformat(),
                'time_zone': 'Brussels',
                'description': self.comments,
                'latitude': self.latitude,
                'longitude': self.longitude,

                # sets vespawatch_id (an observation field whose ID is 9613)
                'observation_field_values_attributes':
                    [{'observation_field_id': settings.OBSERVATION_FIELD_ID, 'value': self.pk},
                    {'observation_field_id': settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID, 'value': vespawatch_evidence_value}]
                }

    def update_at_inaturalist(self, access_token):
        """Update the iNaturalist observation for this obs

        :param access_token:
        :return:
        """
        p = { 'ignore_photos': 1,  # TODO: change that later if we decide to repush pictures in each time...
                'observation': self._params_for_inat()
            }

        return update_observation(observation_id=self.inaturalist_id, params=p, access_token=access_token)

    def create_at_inaturalist(self, access_token):
        """Creates a new observation at iNaturalist for this observation

        It will update the current object so self.inaturalist_id is properly set.
        On the other side, it will also set the vespawatch_id observation field so the observation can be found from
        the iNaturalist record.

        :param access_token: as returned by pyinaturalist.rest_api.get_access_token(
        """

        # TODO: push more fields
        # TODO: check the push works when optional fields are missing
        params_only_for_create = {'taxon_id': self.species.inaturalist_push_taxon_id}

        params = {
            'observation': {**params_only_for_create, **self._params_for_inat()}
        }

        r = create_observations(params=params, access_token=access_token)
        self.inaturalist_id = r[0]['id']
        self.save()


    def get_species_name(self):
        if self.species:
            return self.species.name
        else:
            return ''


class Nest(AbstractObservation):
    duplicate_of = models.ForeignKey('self', on_delete=models.PROTECT, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('vespawatch:nest-update', kwargs={'pk': self.pk})

    def as_dict(self):
        action = self.managementaction_set.first()

        return {
            'id': self.pk,
            'species': self.inaturalist_species if self.inaturalist_species else self.species.name,
            'subject': 'nest',
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'inaturalist_id': self.inaturalist_id,
            'observation_time': self.observation_time.timestamp() * 1000,
            'comments': self.comments,
            'imageUrls': [x.image.url for x in self.nestpicture_set.all()],
            'action': action.get_outcome_display() if action else None,
            'actionCode': action.outcome if action else None,
        }

    def __str__(self):
        return f'Nest of {self.get_species_name()}, {self.observation_time.strftime("%Y-%m-%d")}'


class Individual(AbstractObservation):

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

    # Fields
    individual_count = models.IntegerField(blank=True, null=True)
    behaviour = models.CharField(max_length=2, choices=BEHAVIOUR_CHOICES, blank=True, null=True)
    nest = models.ForeignKey(Nest, on_delete=models.CASCADE, blank=True, null=True)

    def get_absolute_url(self):
        return reverse('vespawatch:individual-update', kwargs={'pk': self.pk})

    def as_dict(self):
        return {
            'id': self.pk,
            'species': self.inaturalist_species if self.inaturalist_species else self.species.name,
            'subject': 'individual',
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'inaturalist_id': self.inaturalist_id,
            'observation_time': self.observation_time.timestamp() * 1000,
            'comments': self.comments,
            'imageUrls': [x.image.url for x in self.individualpicture_set.all()]
        }

    def __str__(self):
        return f'Individual of {self.get_species_name()}, {self.observation_time.strftime("%Y-%m-%d")}'


class IndividualPicture(models.Model):
    def get_file_path(instance, filename):
        ext = filename.split('.')[-1]
        filename = "%s.%s" % (uuid.uuid4(), ext)
        return os.path.join('individual_pictures/', filename)

    observation = models.ForeignKey(Individual, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=get_file_path)


class NestPicture(models.Model):
    def get_file_path(instance, filename):
        ext = filename.split('.')[-1]
        filename = "%s.%s" % (uuid.uuid4(), ext)
        return os.path.join('nest_pictures/', filename)

    observation = models.ForeignKey(Nest, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=get_file_path)



class ManagementAction(models.Model):
    FULL_DESTRUCTION_NO_DEBRIS = 'FD'
    PARTIAL_DESTRUCTION_DEBRIS_LEFT = 'PD'
    EMPTY_NEST_NOTHING_DONE = 'ND'

    OUTCOME_CHOICE = (
        (FULL_DESTRUCTION_NO_DEBRIS, 'Full destruction, no debris'),
        (PARTIAL_DESTRUCTION_DEBRIS_LEFT, 'Partial destruction/debris left'),
        (EMPTY_NEST_NOTHING_DONE, 'Empty nest, nothing done'),
    )

    nest = models.ForeignKey(Nest, on_delete=models.CASCADE)
    outcome = models.CharField(max_length=2, choices=OUTCOME_CHOICE)
    action_time = models.DateTimeField()
    person_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f'{self.action_time.strftime("%Y-%m-%d")} {self.get_outcome_display()} on {self.nest}'


class FirefightersZone(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Firefighters have a zone, other users (Admin, ...) don't.
    zone = models.ForeignKey(FirefightersZone, on_delete=models.PROTECT, null=True, blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
