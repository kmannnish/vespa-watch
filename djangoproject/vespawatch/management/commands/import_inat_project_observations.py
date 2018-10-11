# First prototype of a Django command that retrieves all iNaturalist observations from the VespaWatch project and store
# them in the local database

from django.core.management.base import BaseCommand, CommandError
import dateparser

from pyinaturalist.node_api import get_all_observations

from django.conf import settings

from vespawatch.models import Observation, Species


class Command(BaseCommand):
    help = 'retrieves all iNaturalist observations from the Vespa-Watch project and store them in the database.'

    def handle(self, *args, **options):
        self.stdout.write(f"Will import observations from project #{settings.VESPAWATCH_PROJECT_ID}")

        observations = get_all_observations(params = {
            'project_id': settings.VESPAWATCH_PROJECT_ID,
        })

        for inat_observation in observations:
            inat_id = inat_observation['id']
            self.stdout.write(f'Processing iNaturalist observation #{inat_id}...', ending='')

            try:
                obs = Observation.objects.get(inaturalist_id=inat_id)
                self.stdout.write(f'Observation already exists, skipping.')
            except Observation.DoesNotExist:
                # New observation, we'll try to add it!
                raw_observed_on = inat_observation['observed_on_string']
                if not raw_observed_on:
                    self.stdout.write(f'No time information, skipping...')
                else:
                    observation_time = dateparser.parse(raw_observed_on)

                    if observation_time:
                        self.stdout.write(f'Ok, creating a new observation')
                        species, _ = Species.objects.get_or_create(name=inat_observation['taxon']['name'])

                        Observation.objects.create(
                            originates_in_vespawatch=False,
                            subject=Observation.SPECIMEN,  # TODO: How to detect/manage properly?
                            inaturalist_id=inat_observation['id'],
                            species=species,
                            latitude=inat_observation['geojson']['coordinates'][0],
                            longitude=inat_observation['geojson']['coordinates'][1],
                            observation_time=observation_time)  # TODO: What to do with iNat observations without (parsable) time?
                    else:
                        self.stdout.write(f'Cannot interpret time, skipping... observed_on_string={inat_observation["observed_on_string"]}')

        self.stdout.write("OK")


# Data questions:
#   - iNaturalist entries without datetime?
#   - iNaturalist entries datetime: how to assign timezone so it's not naive anymore
#   - Improve date parsing so it doesn't skip so many records.
#   - What to do when Taxon is subspecies or genus?
#   - How to distinguish a nest of a specimen?

# Other things to test soon:
#   - Make a class/helpers to abstract iNaturalist observations
#   - How to authenticate and create data at iNaturalist