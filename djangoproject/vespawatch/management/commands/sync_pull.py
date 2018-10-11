# Pull observations from iNaturalist, as described in #2.
#
# See also sync_push.py for the other side of the coin
from django.conf import settings
from pyinaturalist.node_api import get_all_observations

from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import Observation

PULL_CRITERIA = {
    'project_id': settings.VESPAWATCH_PROJECT_ID,
}

class Command(VespaWatchCommand):
    help = 'Execute the "pull" part of iNaturalist sync process'

    def handle(self, *args, **options):
        self.w(f"Will import observations from project #{settings.VESPAWATCH_PROJECT_ID}...")

        observations = get_all_observations(params=PULL_CRITERIA)

        self.w(f"Got {len(observations)} matching observations from iNaturalist.")

        self.w("Step 1: Will remove from our database all observations that originates from iNaturalist (they'll be recreated right after)...", ending="")
        Observation.from_inat_objects.all().delete()
        self.w("OK")


        for inat_observation in observations:
            inat_id = inat_observation['id']