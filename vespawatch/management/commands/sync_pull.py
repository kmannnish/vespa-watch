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
from vespawatch.models import Individual, Nest, create_observation_from_inat_data, SpeciesMatchError, ParseDateError, \
    inat_observation_comes_from_vespawatch, update_loc_obs_taxon_according_to_inat

PULL_CRITERIA = {
    'project_id': settings.VESPAWATCH_PROJECT_ID,
}

class Command(VespaWatchCommand):
    help = 'Execute the "pull" part of iNaturalist sync process'

    def handle(self, *args, **options):
        self.w(f"Will import observations from project #{settings.VESPAWATCH_PROJECT_ID}...")

        observations = get_all_observations(params=PULL_CRITERIA)

        total_count = len(observations)
        success_count, from_us_count, from_inat_count = 0, 0 ,0

        self.w("Step 1: Will remove from our database all observations that originates from iNaturalist (they'll be recreated right after)...", ending="")
        Individual.from_inat_objects.all().delete()
        Nest.from_inat_objects.all().delete()
        self.w(self.style.SUCCESS("OK"))

        self.w(f"Step 2: Will parse the {total_count} matching observations reveived from iNaturalist.")
        for inat_observation_data in observations:
            inat_id = inat_observation_data['id']

            self.w(f"Now processing iNaturalist observation #{inat_id}...", ending="")

            if inat_observation_comes_from_vespawatch(inat_observation_data['id']):
                from_us_count = from_us_count + 1
                self.w("This observation initially comes from Vespa-Watch", ending="")
                # The only thing we do is updating the identification, if needed.
                update_loc_obs_taxon_according_to_inat(inat_observation_data)
                success_count = success_count + 1
                self.w(" ");
            else:
                from_inat_count = from_inat_count + 1
                self.w("This observation initially comes from a regular iNaturalist user. ", ending="")
                # All those observations have been dropped before: recreate
                self.w("We create a local observation for it. ", ending="")
                try:
                    create_observation_from_inat_data(inat_observation_data)
                    self.w(self.style.SUCCESS("OK"))
                    success_count = success_count + 1
                except SpeciesMatchError:
                    if inat_observation_data['taxon']['rank'] == 'genus':
                        self.w(self.style.WARNING("Observation at the Genus level, skipping."))
                    else:
                        self.w(self.style.ERROR("Error: cannot match species, skipping: " + str(inat_observation_data)))
                except ParseDateError:
                    self.w(self.style.ERROR("Error: cannot parse date, skipping: " + str(inat_observation_data)))

        self.w("DONE. Stats:")
        self.w(f"{total_count} observations processed (total).")
        self.w(f"{success_count} were successful, {total_count - success_count} had errors.")
        self.w(f"{from_us_count} were from the Vespa-Watch app, {from_inat_count} were regular iNaturalist observations.")