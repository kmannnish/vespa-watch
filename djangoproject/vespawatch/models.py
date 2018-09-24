from django.db import models


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

    species = models.ForeignKey(Species, on_delete=models.PROTECT, blank=True, null=True)  # Blank allows because some nests can't be easily identified
    subject = models.CharField(max_length=2, choices=SUBJECT_CHOICES)
    nest_location = models.CharField(max_length=255, blank=True)

    latitude = models.FloatField()
    longitude = models.FloatField()

    inaturalist_id = models.BigIntegerField(blank=True, null=True)
    observation_time = models.DateTimeField()
    comments = models.TextField(blank=True)


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

    outcome = models.CharField(max_length=2, choices=OUTCOME_CHOICE)
    action_time = models.DateTimeField()
    person_name = models.CharField(max_length=255, blank=True)