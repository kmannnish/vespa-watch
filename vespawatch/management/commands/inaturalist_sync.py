import datetime
from json import JSONDecodeError

from django.conf import settings
from django.utils import timezone
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.node_api import get_all_observations, get_observation
from pyinaturalist.rest_api import get_access_token, delete_observation

from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import Individual, Nest, InatObsToDelete, get_local_observation_with_inaturalist_id, \
    create_observation_from_inat_data

OBSERVATION_MODELS = [Individual, Nest]


class Command(VespaWatchCommand):
    help = 'Syncrhonize VespaWatch and iNaturalist. Full description: https://github.com/inbo/vespa-watch/issues/2'

    def obs_created_in_inat_and_harvested_before(self):
        self.w("\n3. Update observations created through iNaturalist that we already know of")
        local_observations_from_inat = []
        for Model in OBSERVATION_MODELS:
            local_observations_from_inat + list(Model.from_inat_objects.all())

        for obs in local_observations_from_inat:
            if obs.inaturalist_id: # This should always be the case, no?
                pass
                #TODO: case1: obs found: update all info and set inat_vv_confirmed
                #TODO: case2: obs deleted by iNat user, flag our record with a warning.

    def obs_created_in_inat_to_be_harvested(self):
        self.w("\n2. Pull new observations created through iNaturalist")
        observations = get_all_observations(params={'project_id': settings.VESPAWATCH_PROJECT_ID, 'taxon_id': 119019})  #TODO: Taxon ID is only 119019? No need for subspecies (see models.INAT_VV_TAXONS_IDS)?
        for inat_observation_data in observations:
            local_obs = get_local_observation_with_inaturalist_id(inat_observation_data['id'])
            if local_obs is None:
                # Ok we found a new one
                self.w(f"iNaturalist observation with ID #{inat_observation_data['id']} is not yet known, we'll create it locally...", ending='')
                create_observation_from_inat_data(inat_observation_data)  #TODO: check all the required fields are set. # TODO: set 'inat_vv_confirmed'
                self.w("OK")

    def obs_created_in_vespawatch(self, access_token):
        """Push/pull the nest and individuals that originates in VW"""
        self.w("1. Push/pull the nest and individuals that originates in VW")

        self.w("1.1 Ensure locally deleted VespaWatch observations are also deleted at iNaturalist...")
        for obs in InatObsToDelete.objects.all():
            self.w(f"Deleting iNaturalist observation #{obs.inaturalist_id}...", ending='')
            try:
                delete_observation(observation_id=obs.inaturalist_id, access_token=access_token)
            except JSONDecodeError:
                # (temporary?) iNaturalist API issue...
                pass
            obs.delete()
            self.w("OK")

        # Collect all the local observations that comes from us
        local_observations_from_vespawatch = []
        for Model in OBSERVATION_MODELS:
            local_observations_from_vespawatch = local_observations_from_vespawatch + list(Model.from_vespawatch_objects.all())

        self.w(f"1.2 We currently have {len(local_observations_from_vespawatch)} local observations that originates in VW. Push/pull each of them, as needed")

        for obs in local_observations_from_vespawatch:
            self.w(f"Processing {obs.subject} #{obs.pk}...")
            if not obs.exists_in_inaturalist:  #  not pushed yet: this is the first push, and there's no need to pull it
                self.w("1.2.1 This is a new observation, we'll create it at iNaturalist. ", ending="")
                if settings.INATURALIST_PUSH:
                    obs.create_at_inaturalist(access_token=access_token)
                    self.w("OK")
                else:
                    self.w("Push ignored because of settings.INATURALIST_PUSH")
            else:
                self.w("1.2.2 This observation has been previously pushed, let's pull", ending="")
                # Already pushed: there's nothing to push more (possible deletion was taken care of in 1.1), but we can pull
                # to update all information and set inat_vv_confirmed
                try:
                    inat_obs_data = get_observation(obs.inaturalist_id)
                    obs.update_from_inat_data(inat_obs_data) # TODO: implement this
                except ObservationNotFound:
                    self.w("This observation seems to have vanished of iNaturalist, let's flag it.")
                    r = obs.warnings.create(text="This observation seems to have vanished of iNaturalist!",
                                            datetime=timezone.now())



    def handle(self, *args, **options):
        if settings.INATURALIST_PUSH:
            token = get_access_token(username=settings.INAT_USER_USERNAME, password=settings.INAT_USER_PASSWORD,
                                     app_id=settings.INAT_APP_ID,
                                     app_secret=settings.INAT_APP_SECRET)
        else:
            token = None

        self.obs_created_in_vespawatch(token)
        self.obs_created_in_inat_to_be_harvested()
        self.obs_created_in_inat_and_harvested_before()