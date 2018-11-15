from json import JSONDecodeError

from django.conf import settings
from pyinaturalist.rest_api import get_access_token, delete_observation
from requests import HTTPError

from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import Individual, Nest, InatObsToDelete


class Command(VespaWatchCommand):
    help = 'Execute the "push" part of iNaturalist sync process'

    def handle(self, *args, **options):
        self.w("Will push our observations to iNaturalist... (the observations that originate from iNaturalist won't "
               "be pushed.")

        observations = list(Individual.from_vespawatch_objects.all()) + list(Nest.from_vespawatch_objects.all())
        self.w(f"We currently have {len(observations)} pushable observations.")

        self.w("Getting an access token for iNaturalist...", ending="")
        token = get_access_token(username=settings.INAT_USER_USERNAME, password=settings.INAT_USER_PASSWORD,
                                 app_id=settings.INAT_APP_ID,
                                 app_secret=settings.INAT_APP_SECRET)
        self.w("OK")

        for obs in observations:
            self.w(f"Pushing our observation with id={obs.pk}...", ending="")
            if obs.exists_in_inaturalist:
                self.w("This observation was already pushed, we'll update. ", ending="")
                try:
                    obs.update_at_inaturalist(access_token=token)
                    self.w("OK")
                except HTTPError as exc:
                    self.w(self.style.ERROR("iNat returned an error: does the observation exists there and do we have "
                                            "the right to update it? Exception: ") + str(exc))
            else:
                self.w("This is a new observation, we'll create it at iNaturalist. ", ending="")
                obs.create_at_inaturalist(access_token=token)
                self.w("OK")

        self.w("Will now ensure locally deleted vespawatch observations are also deleted at iNaturalist...")
        for obs in InatObsToDelete.objects.all():
            self.w(f"Deleting iNaturalist observation #{obs.inaturalist_id}...", ending='')
            try:
                delete_observation(observation_id=obs.inaturalist_id, access_token=token)
            except JSONDecodeError:
                # (temporary?) iNaturalist API issue...
                pass
            obs.delete()
            self.w("OK")





