import logging
from json import JSONDecodeError

from django.conf import settings
from django.utils import timezone
from pyinaturalist.exceptions import ObservationNotFound
from pyinaturalist.node_api import get_all_observations, get_observation
from pyinaturalist.rest_api import get_access_token, delete_observation

from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import Individual, Nest, InatObsToDelete, get_local_observation_with_inaturalist_id, \
    create_observation_from_inat_data, get_missing_at_inat_observations

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

    # def obs_created_in_inat_to_be_harvested(self):
    #     self.w("\n2. Pull new observations created through iNaturalist")
    #     observations = get_all_observations(params={'project_id': settings.VESPAWATCH_PROJECT_ID, 'taxon_id': 119019})  #TODO: Taxon ID is only 119019? No need for subspecies (see models.INAT_VV_TAXONS_IDS)?
    #     for inat_observation_data in observations:
    #         local_obs = get_local_observation_with_inaturalist_id(inat_observation_data['id'])
    #         if local_obs is None:
    #             # Ok we found a new one
    #             self.w(f"iNaturalist observation with ID #{inat_observation_data['id']} is not yet known, we'll create it locally...", ending='')
    #             create_observation_from_inat_data(inat_observation_data)  #TODO: check all the required fields are set. # TODO: set 'inat_vv_confirmed'
    #             self.w("OK")

    def obs_created_in_vespawatch(self, access_token):
        """Push/pull the nest and individuals that originates in VW"""
        # self.w("1. Push/pull the nest and individuals that originates in VW")
        #
        # self.w("1.1 Ensure locally deleted VespaWatch observations are also deleted at iNaturalist...")
        # for obs in InatObsToDelete.objects.all():
        #     self.w(f"Deleting iNaturalist observation #{obs.inaturalist_id}...", ending='')
        #     try:
        #         delete_observation(observation_id=obs.inaturalist_id, access_token=access_token)
        #     except JSONDecodeError:
        #         (temporary?) iNaturalist API issue...
        #         pass
        #     obs.delete()
        #     self.w("OK")

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

    def push_deletes(self, access_token):
        """
        Delete objects on iNaturalist that were deleted on vespawatch
        """
        self.w("1. Delete the nests and individuals that are deleted in VW")

        for obs in InatObsToDelete.objects.all():
            self.w(f"Deleting iNaturalist observation #{obs.inaturalist_id}...", ending='')
            try:
                delete_observation(observation_id=obs.inaturalist_id, access_token=access_token)
                obs.delete()  # Only delete locally if the API call succeeded
            except JSONDecodeError:
                # (temporary?) iNaturalist API issue...
                logging.warning(f'Delete observation {obs.inaturalist_id} raised a JSONDecodeError')
            self.w("OK")

    def push_created(self, access_token):
        """
        Create objects on iNaturalist that were newly created at vespawatch
        and don't have a iNaturalist id yet
        """
        self.w("2. Push the nest and individuals that originate in VW")
        if not settings.INATURALIST_PUSH:
            self.w("Not pushing objects because of settings.INATURALIST_PUSH")
            return

        local_observations_from_vespawatch = []
        for Model in OBSERVATION_MODELS:
            local_observations_from_vespawatch = local_observations_from_vespawatch + list(Model.new_vespawatch_objects.all())
        self.w(f"2.1 We currently have {len(local_observations_from_vespawatch)} local observations that originate in VW. Push/pull each of them, as needed")

        for obs in local_observations_from_vespawatch:
            self.w(f"Processing {obs.subject} #{obs.pk}...")
            self.w("2.2 This is a new observation, we'll create it at iNaturalist. ", ending="")
            obs.create_at_inaturalist(access_token=access_token)

    def pull(self):
        """
        Pull all observations from iNaturalist.
        If we don't have an observation with that iNaturalist ID, create one (check the vespawatch-evidence field to
        determine whether we should create a Nest or an Individual)
        If we do have an observation with that iNaturalist ID, update it.
        """
        self.w("\n3. Pull all observations from iNaturalist")
        observations = get_all_observations(params={'project_id': settings.VESPAWATCH_PROJECT_ID, 'taxon_id': 119019})  #TODO: Taxon ID is only 119019? No need for subspecies (see models.INAT_VV_TAXONS_IDS)?
        pulled_inat_ids = []
        for inat_observation_data in observations:
            pulled_inat_ids.append(inat_observation_data['id'])
            local_obs = get_local_observation_with_inaturalist_id(inat_observation_data['id'])
            if local_obs is None:
                # This is a new one. Check vespawatch-evidence and create a nest or individual
                self.w(f"iNaturalist observation with ID #{inat_observation_data['id']} is not yet known, we'll create it locally...", ending='')
                create_observation_from_inat_data(inat_observation_data)  #TODO: check all the required fields are set. # TODO: set 'inat_vv_confirmed'
                self.w("OK")
            else:
                # We already have an observation for this id. Update it
                local_obs.update_from_inat_data(inat_observation_data)  # TODO: implement this
        return pulled_inat_ids

    def check_missing_obs(self, observation):
        """
        Get the observation data from iNaturalist and update the observation.
        If that yields an ObservationNotFound error, the observation was deleted at iNaturalist and should be
        deleted at vespawatch too.
        """
        self.w("\n4. Check the observations that were not returned from iNaturalist")
        try:
            inat_obs_data = get_observation(observation.inaturalist_id)
            observation.update_from_inat_data(inat_obs_data)  # TODO: or add flags as indicated in the sheet specification
        except ObservationNotFound:
            observation.delete()

    def check_all_missing(self, missing_inat_ids):
        """
        Get all observations from vespawatch that have an iNaturalist id, but are not found in the
        data of the iNaturlist pull. Check the observations one by one.
        """
        missing_obs = get_missing_at_inat_observations(missing_inat_ids)
        for obs in missing_obs:
            self.check_missing_obs(obs)


    def handle(self, *args, **options):
        if settings.INATURALIST_PUSH:
            token = get_access_token(username=settings.INAT_USER_USERNAME, password=settings.INAT_USER_PASSWORD,
                                     app_id=settings.INAT_APP_ID,
                                     app_secret=settings.INAT_APP_SECRET)
        else:
            token = None

        self.push_deletes(token)
        self.push_created(token)
        # pulled_inat_ids = self.pull()
        # self.check_all_missing(pulled_inat_ids)
        self.w("\ndone\n")
