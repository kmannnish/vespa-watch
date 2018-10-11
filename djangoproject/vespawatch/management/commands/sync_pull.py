# Pull observations from iNaturalist, as described in #2.
#
# Observations are taken from the Vespa-Watch project, the project criteria are
#   - Vespa genus
#   - In Belgium
#   - Date: January 1, 2015 to January 1, 2100
#
# See also sync_push.py for the other side of the coin
from django.conf import settings
from pyinaturalist.node_api import get_all_observations

from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import Observation, create_observation_from_inat_data, SpeciesMatchError, ParseDateError

PULL_CRITERIA = {
    'project_id': settings.VESPAWATCH_PROJECT_ID,
}

def inat_observation_comes_from_vespawatch(inat_observation):
    """ Takes an observation retrieved from iNat API and returns True if this observation was first created from VespaWatch"""
    return inat_observation['user']['id'] == settings.VESPAWATCH_USER_ID

class Command(VespaWatchCommand):
    help = 'Execute the "pull" part of iNaturalist sync process'

    def handle(self, *args, **options):
        self.w(f"Will import observations from project #{settings.VESPAWATCH_PROJECT_ID}...")

        observations = get_all_observations(params=PULL_CRITERIA)

        self.w(f"Got {len(observations)} matching observations from iNaturalist.")

        self.w("Step 1: Will remove from our database all observations that originates from iNaturalist (they'll be recreated right after)...", ending="")
        Observation.from_inat_objects.all().delete()
        self.w("OK")

        for inat_observation_data in observations:
            inat_id = inat_observation_data['id']

            self.w(f"Now processing iNaturalist observation #{inat_id}...", ending="")

            if inat_observation_comes_from_vespawatch(inat_observation_data):
                self.w("This observation initially comes from Vespa-Watch")

                # The only thing we do is updating the identification, if needed.
            else:
                self.w("This observation initially comes from a regular iNaturalist user.")
                # All those observations have been dropped before: recreate
                self.w("We create a local observation for it.")
                try:
                    create_observation_from_inat_data(inat_observation_data)
                except SpeciesMatchError:
                    self.w("Error: cannot match species, skipping: " + str(inat_observation_data))
                except ParseDateError:
                    self.w("Error: cannot parse date, skipping: " + str(inat_observation_data))