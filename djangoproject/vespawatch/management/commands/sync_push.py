from django.conf import settings
from pyinaturalist.rest_api import get_access_token

from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import Observation


class Command(VespaWatchCommand):
    help = 'Execute the "push" part of iNaturalist sync process'

    def handle(self, *args, **options):
        self.w("Will push our observations to iNaturalist... (the observations that originate from iNaturalist won't "
               "be pushed.")

        qs = Observation.from_vespawatch_objects.all()
        self.w(f"We currently have {qs.count()} pushable observations.")

        self.w("Getting an access token for iNaturalist...", ending="")
        token = get_access_token(username=settings.INAT_USER_USERNAME, password=settings.INAT_USER_PASSWORD,
                                 app_id=settings.INAT_APP_ID,
                                 app_secret=settings.INAT_APP_SECRET)
        self.w("OK")

        for obs in qs:
            self.w(f"Pushing our observation with id={obs.pk}...", ending="")
            if obs.exists_in_inaturalist:
                self.w("This observation was already pushed, we'll update. ", ending="")
            else:
                self.w("This is a new observation, we'll create it at iNaturalist. ", ending="")
                obs.create_at_inaturalist(access_token=token)
                self.w("OK")



