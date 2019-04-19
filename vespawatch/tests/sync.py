from datetime import datetime
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from pyinaturalist.exceptions import ObservationNotFound
from unittest import mock, SkipTest
from vespawatch.models import Individual, InatObsToDelete, Nest, NestPicture, Taxon, INAT_VV_TAXONS_IDS
import requests


class TestSync(TestCase):
    def setUp(self):
        # Set up patchers
        self.get_all_patcher = mock.patch('vespawatch.management.commands.inaturalist_sync.get_all_observations')
        self.get_obs_patcher = mock.patch('vespawatch.management.commands.inaturalist_sync.get_observation')
        self.get_token_patcher = mock.patch('vespawatch.management.commands.inaturalist_sync.get_access_token')
        self.delete_patcher = mock.patch('vespawatch.management.commands.inaturalist_sync.delete_observation')
        self.create_at_inat_patcher = mock.patch('vespawatch.models.create_observations')
        self.update_at_inat_patcher = mock.patch('vespawatch.models.update_observation')
        self.add_photo_from_inat_patcher = mock.patch('vespawatch.models.add_photo_to_observation')
        self.requests_patcher = mock.patch('vespawatch.models.requests.get')

        # Create mock classes
        self.get_all_mock = self.get_all_patcher.start()
        self.get_obs_mock = self.get_obs_patcher.start()
        self.get_token_mock = self.get_token_patcher.start()
        self.delete_mock = self.delete_patcher.start()
        self.create_at_inat_mock = self.create_at_inat_patcher.start()
        self.update_at_inat_mock = self.update_at_inat_patcher.start()
        self.add_photo_from_inat_mock = self.add_photo_from_inat_patcher.start()
        self.requests_mock = self.requests_patcher.start()

        # Set a return value for the create_at_inat_mock
        self.create_at_inat_mock.return_value = [{'id': 999}]

        # Set a return value for the get_token_mock
        self.get_token_mock.return_value = 'TESTTOKEN'

        self.vv_taxon = Taxon(
            name='Vespa velutina',
            vernacular_name='test wasp',
            inaturalist_push_taxon_id=1,
            inaturalist_pull_taxon_ids=[1],
            identification_priority=1
        )
        self.vv_taxon.save()

    def tearDown(self):
        # Stop all patchers
        self.get_all_patcher.stop()
        self.get_obs_patcher.stop()
        self.get_token_patcher.stop()
        self.delete_patcher.stop()
        self.create_at_inat_patcher.stop()
        self.update_at_inat_patcher.stop()
        self.add_photo_from_inat_patcher.stop()
        self.requests_patcher.stop()

        # Delete all objects that have been created
        InatObsToDelete.objects.all().delete()
        Individual.objects.all().delete()
        Nest.objects.all().delete()
        NestPicture.objects.all().delete()
        Taxon.objects.all().delete()

    @override_settings(INATURALIST_PUSH=True)
    def test_sync_push_new_individual(self):
        """
        Create a test individual and run the sync command.
        Assert that the mocked iNaturalist API is called with the
        individual data + the vespawatch_evidence field set to 'individual'
        """

        # Create an Individual with minimum info
        ind = Individual(
            originates_in_vespawatch=True,
            taxon=self.vv_taxon,
            observation_time=datetime(2019, 4, 1, 10),
            latitude=51.2003,
            longitude=4.9067
        )
        ind.save()

        individual_data_to_inaturalist = {
            'taxon_id': ind.taxon.inaturalist_push_taxon_id,
            'observed_on_string': '2019-04-01T08:00:00+00:00',
            'time_zone': 'Brussels',
            'description': '',
            'latitude': ind.latitude, 'longitude': ind.longitude, 'place_guess': '',
            'observation_field_values_attributes': [
                {'observation_field_id': settings.VESPAWATCH_ID_OBS_FIELD_ID, 'value': ind.pk},
                {'observation_field_id': settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID, 'value': 'individual'}
            ]
        }
        call_command('inaturalist_sync')
        self.create_at_inat_mock.assert_called_once()
        self.create_at_inat_mock.assert_called_with(access_token='TESTTOKEN', params={'observation': individual_data_to_inaturalist})

    @override_settings(INATURALIST_PUSH=True)
    def test_sync_push_new_nest(self):
        """
        Create a test nest and run the sync command.
        Assert that the mocked iNaturalist API is called with the
        nest data + the vespawatch_evidence field set to 'nest'
        """

        # Create a Nest with minimum info
        ind = Nest(
            originates_in_vespawatch=True,
            taxon=self.vv_taxon,
            observation_time=datetime(2019, 4, 1, 10),
            latitude=51.2003,
            longitude=4.9067
        )
        ind.save()

        individual_data_to_inaturalist = {
            'taxon_id': ind.taxon.inaturalist_push_taxon_id,
            'observed_on_string': '2019-04-01T08:00:00+00:00',
            'time_zone': 'Brussels',
            'description': '',
            'latitude': ind.latitude, 'longitude': ind.longitude, 'place_guess': '',
            'observation_field_values_attributes': [
                {'observation_field_id': settings.VESPAWATCH_ID_OBS_FIELD_ID, 'value': ind.pk},
                {'observation_field_id': settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID, 'value': 'nest'}
            ]
        }
        call_command('inaturalist_sync')
        self.create_at_inat_mock.assert_called_once()
        self.create_at_inat_mock.assert_called_with(access_token='TESTTOKEN', params={'observation': individual_data_to_inaturalist})

    @override_settings(INATURALIST_PUSH=True)
    def test_sync_push_deleted_indiv(self):
        """
        An observation that was created in vespawatch and deleted in vespawatch after it was synced, should be
        deleted on iNaturalist
        """

        # Create an Individual that already exists in iNaturalist after a previous push
        ind = Individual(
            inaturalist_id=30,
            latitude=51.2003,
            longitude=4.9067,
            observation_time=datetime(2019, 4, 1, 10),
            originates_in_vespawatch=True,
            taxon=self.vv_taxon
        )
        ind.save()
        ind.delete()  # When the observation is deleted, it is actually added to the InatObsToDelete table

        self.assertEqual(len(InatObsToDelete.objects.all()), 1)
        self.assertEqual(InatObsToDelete.objects.all()[0].inaturalist_id, 30)

        # Now a sync is called. The InatObsToDelete observation is deleted on iNaturalist and removed from the db
        call_command('inaturalist_sync')
        self.delete_mock.assert_called_once_with(observation_id=30, access_token='TESTTOKEN')

    @override_settings(INATURALIST_PUSH=True)
    def test_sync_no_push_deleted_indiv(self):
        """
        An observation that was deleted on vespawatch before it was synced to iNaturalist should not be deleted on
        iNaturalist
        """

        # Create an Individual that does not exist in iNaturalist
        ind = Individual(
            latitude=51.2003,
            longitude=4.9067,
            observation_time=datetime(2019, 4, 1, 10),
            originates_in_vespawatch=True,
            taxon=self.vv_taxon
        )
        ind.save()
        ind.delete()  # When the observation is deleted, it is deleted without creating a InatObsToDelete object

        self.assertEqual(len(InatObsToDelete.objects.all()), 0)

        # Now a sync is called. Since there are no InatObsToDelete, the delete_mock is never called
        call_command('inaturalist_sync')
        self.delete_mock.assert_not_called()


    @override_settings(INATURALIST_PUSH=True)
    def test_sync_push_deleted_nest(self):
        """
        An observation that was created in vespawatch and deleted in vespawatch after it was synced, should be
        deleted on iNaturalist
        """

        # Create a Nest that already exists in iNaturalist after a previous push
        nest = Nest(
            inaturalist_id=30,
            latitude=51.2003,
            longitude=4.9067,
            observation_time=datetime(2019, 4, 1, 10),
            originates_in_vespawatch=True,
            taxon=self.vv_taxon
        )
        nest.save()
        nest.delete()  # When the observation is deleted, it is actually added to the InatObsToDelete table

        self.assertEqual(len(InatObsToDelete.objects.all()), 1)
        self.assertEqual(InatObsToDelete.objects.all()[0].inaturalist_id, 30)

        # Now a sync is called. The InatObsToDelete observation is deleted on iNaturalist and removed from the db
        call_command('inaturalist_sync')
        self.delete_mock.assert_called_once_with(observation_id=30, access_token='TESTTOKEN')

    @override_settings(INATURALIST_PUSH=True)
    def test_sync_no_push_deleted_nest(self):
        """
        An observation that was deleted on vespawatch before it was synced to iNaturalist should not be deleted on
        iNaturalist
        """

        # Create an Individual that already exists in iNaturalist after a previous push
        nest = Individual(
            latitude=51.2003,
            longitude=4.9067,
            observation_time=datetime(2019, 4, 1, 10),
            originates_in_vespawatch=True,
            taxon=self.vv_taxon
        )
        nest.save()
        nest.delete()  # When the observation is deleted, it is deleted without creating a InatObsToDelete object

        self.assertEqual(len(InatObsToDelete.objects.all()), 0)

        # Now a sync is called. Since there are no InatObsToDelete, the delete_mock is never called
        call_command('inaturalist_sync')
        self.delete_mock.assert_not_called()

    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_create_ind_full_datetime(self):
        # assert no Individuals exist in the database
        self.assertEqual(len(Individual.objects.all()), 0)

        # Set a return value for the self.get_all_mock. It should return only data for an observation
        # with iNaturalist id = 30
        self.get_all_mock.return_value = [
            {
                'id': 30,
                'community_taxon_id': INAT_VV_TAXONS_IDS[0],
                'geojson': {
                    'coordinates': [10, 20]
                },
                'observed_on_string': '2019-04-01T11:20:00+00:00',
                'observed_time_zone': 'Europe/Brussels',
                'photos': [],
                'taxon': {
                    'id': INAT_VV_TAXONS_IDS[0]
                }
            }
        ]
        call_command('inaturalist_sync')
        # Assert that the individual is created now
        self.assertEqual(len(Individual.objects.filter(inaturalist_id=30)), 1)
        # And assert that it does not originate in vespawatch
        self.assertFalse(Individual.objects.filter(inaturalist_id=30)[0].originates_in_vespawatch)

    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_create_ind_datetime_parts(self):
        # assert no Individuals exist in the database
        self.assertEqual(len(Individual.objects.all()), 0)

        # Set a return value for the self.get_all_mock. It should return only data for an observation
        # with iNaturalist id = 30
        self.get_all_mock.return_value = [
            {
                'id': 30,
                'community_taxon_id': INAT_VV_TAXONS_IDS[0],
                'geojson': {
                    'coordinates': [10, 20]
                },
                'observed_on_string': '',
                'observed_on_details': {
                    'year': 2019, 'month': 4, 'day': 1, 'hour': 10
                },
                'observed_time_zone': 'Europe/Brussels',
                'photos': [],
                'taxon': {
                    'id': INAT_VV_TAXONS_IDS[0]
                }
            }
        ]
        call_command('inaturalist_sync')
        # Assert that the individual is created now
        self.assertEqual(len(Individual.objects.filter(inaturalist_id=30)), 1)
        # And assert that it does not originate in vespawatch
        self.assertFalse(Individual.objects.filter(inaturalist_id=30)[0].originates_in_vespawatch)


    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_create_ind_no_nest_ofv(self):
        # assert no Individuals exist in the database
        self.assertEqual(len(Individual.objects.all()), 0)

        # Set a return value for the self.get_all_mock. It should return only data for an observation
        # with iNaturalist id = 30
        self.get_all_mock.return_value = [
            {
                'id': 30,
                'community_taxon_id': INAT_VV_TAXONS_IDS[0],
                'geojson': {
                    'coordinates': [10, 20]
                },
                'observed_on_string': '2019-04-01T11:20:00+00:00',
                'observed_time_zone': 'Europe/Brussels',
                'ofvs': [
                    {'field_id': settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID, 'value': 'no-nest'}
                ],
                'photos': [],
                'taxon': {
                    'id': INAT_VV_TAXONS_IDS[0]
                }
            }
        ]
        call_command('inaturalist_sync')
        # Assert that the individual is created now
        self.assertEqual(len(Individual.objects.filter(inaturalist_id=30)), 1)
        # And assert that it does not originate in vespawatch
        self.assertFalse(Individual.objects.filter(inaturalist_id=30)[0].originates_in_vespawatch)

    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_create_nest(self):
        # assert no Nests exist in the database
        self.assertEqual(len(Nest.objects.all()), 0)

        self.get_all_mock.return_value = [
            {
                'id': 30,
                'community_taxon_id': INAT_VV_TAXONS_IDS[0],
                'geojson': {
                    'coordinates': [10, 20]
                },
                'observed_on_string': '2019-04-01T11:20:00+00:00',
                'observed_time_zone': 'Europe/Brussels',
                'ofvs': [
                    {'field_id': settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID, 'value': 'nest'}
                ],
                'photos': [],
                'taxon': {
                    'id': INAT_VV_TAXONS_IDS[0]
                }
            }
        ]

        call_command('inaturalist_sync')
        # Assert that the nest is created now
        self.assertEqual(len(Nest.objects.filter(inaturalist_id=30)), 1)
        # And assert that it does not originate in vespawatch
        self.assertFalse(Nest.objects.filter(inaturalist_id=30)[0].originates_in_vespawatch)

    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_create_update_images(self):
        """
        When creating a new observation based on iNaturalist data, a Picture should also be created.
        When we pull again and the API returns additional images, those are not added. This is done
        because we insert a UUID in the filename when we pull it. The result of that is that we cannot
        compare that image with the image url that we retrieve from iNaturalist. So to prevent adding
        the same image again and again with subsequent pulls, we only add images when the observation
        has none.
        """
        # Fetching images will do so by calling requests. Let's add a fake response as return value
        fake_response = requests.Response()
        fake_response._content = 'test'
        fake_response._content_consumed = True
        fake_response.status_code = 200
        self.requests_mock.return_value = fake_response

        # assert no Nests exist in the database
        self.assertEqual(len(Nest.objects.all()), 0)

        self.get_all_mock.return_value = [
            {
                'id': 13,
                'community_taxon_id': INAT_VV_TAXONS_IDS[0],
                'geojson': {
                    'coordinates': [10, 20]
                },
                'observed_on_string': '2019-04-01T11:20:00+00:00',
                'observed_time_zone': 'Europe/Brussels',
                'ofvs': [
                    {'field_id': settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID, 'value': 'nest'}
                ],
                'photos': [{'url': '/notexisting/square.jpg'}],
                'taxon': {
                    'id': INAT_VV_TAXONS_IDS[0]
                }
            }
        ]

        call_command('inaturalist_sync')
        # Assert that the nest is created now
        self.assertEqual(len(Nest.objects.filter(inaturalist_id=13)), 1)
        nest = Nest.objects.filter(inaturalist_id=13)[0]
        self.requests_mock.assert_called_once()
        # And assert that it does not originate in vespawatch
        self.assertFalse(nest.originates_in_vespawatch)

        # Assert there is only 1 picture
        self.assertEqual(len(nest.pictures.all()), 1)

        first_pic = nest.pictures.all()[0]
        base_name = first_pic.image.name.split('/')[-1]
        self.assertTrue(base_name.startswith('large'))

        # When pulling again, a new image should not be added again
        self.get_all_mock.return_value[0]['photos'].append({'url': '/anothernotexistingfile/square.jpg'})
        call_command('inaturalist_sync')
        # Assert there is still only 1 picture
        self.assertEqual(len(nest.pictures.all()), 1)

        # If we delete the image and pull again, it is added again
        NestPicture.objects.filter(observation=nest)[0].delete()
        self.assertEqual(len(nest.pictures.all()), 0)  # assert the image is deleted now
        call_command('inaturalist_sync')
        # Assert that the two images in the response are added now
        self.assertEqual(len(nest.pictures.all()), 2)

    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_update_fields_ind(self):
        """
        When an individual exists and we get updated info from iNaturalist for that individual,
        the fields should be updated
        """
        # Create an Individual that already exists in iNaturalist after a previous push
        ind = Individual(
            inaturalist_id=30,
            latitude=51.2003,
            longitude=4.9067,
            observation_time=datetime(2019, 4, 1, 10),
            originates_in_vespawatch=True,
            taxon=self.vv_taxon
        )
        ind.save()

        # Set a return value for the self.get_all_mock. It should return only data for the observation
        # with iNaturalist id = 30
        # Here we will assume the community_taxon_id is set to a vespawatch taxon and the coordiantes are changed
        self.get_all_mock.return_value = [
            {
                'id': 30,
                'community_taxon_id': INAT_VV_TAXONS_IDS[0],
                'geojson': {
                    'coordinates': [10, 20]
                },
                'photos': []
            }
        ]

        # Run inaturalist sync.
        call_command('inaturalist_sync')
        self.get_all_mock.assert_called_once()

        # The individual is now changed
        ind = Individual.objects.all().filter(inaturalist_id=30)[0]

        self.assertEqual(ind.longitude, 10)
        self.assertEqual(ind.latitude, 20)
        self.assertTrue(ind.inat_vv_confirmed)

    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_deleted_obs(self):
        """
        We have an observation in our database with a iNaturalist ID, but when we pull from the iNaturalist API
        this observation is not returned.
        So we check the observation individually and in this case we conclude it no longer exist.
        In this scenario, the observation should be deleted locally
        """
        # Create an Individual that already exists in iNaturalist after a previous push
        ind = Individual(
            inaturalist_id=30,
            latitude=51.2003,
            longitude=4.9067,
            observation_time=datetime(2019, 4, 1, 10),
            originates_in_vespawatch=True,
            taxon=self.vv_taxon
        )
        ind.save()

        # Set a return value for the self.get_all_mock. It should return no observations
        self.get_all_mock.return_value = []

        # Set a side effect for the self.get_obs_mock. It should raise a ObservationNotFound exception
        self.get_obs_mock.side_effect = ObservationNotFound()

        # Run inaturalist sync.
        call_command('inaturalist_sync')
        # Assert that the individual is deleted
        self.assertEqual(len(Individual.objects.all()), 0)

    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_obs_out_project(self):
        """
        We have an observation in our database with a iNaturalist ID, but when we pull from the iNaturalist API
        this observation is not returned.
        So we check the observation individually and in this case we conclude it is no longer part of the Vespawatch project.
        It doesn't matter where this observation comes from, we should flag it as "not in vespawatch project"
        """
        # Create an Individual that already exists in iNaturalist after a previous push
        ind = Individual(
            inaturalist_id=30,
            latitude=51.2003,
            longitude=4.9067,
            observation_time=datetime(2019, 4, 1, 10),
            originates_in_vespawatch=True,
            taxon=self.vv_taxon
        )
        ind.save()

        # Set a return value for the self.get_all_mock. It should return no observations
        self.get_all_mock.return_value = []

        # Set a side effect for the self.get_obs_mock. It should return an observation that has no vespawatch project id
        self.get_obs_mock.return_value = {
            'id': 30,
            'community_taxon_id': INAT_VV_TAXONS_IDS[0],
            'geojson': {
                'coordinates': [10, 20]
            },
            'photos': [],
            'project_ids': [999]  # not vespawatch
        }

        # Assert that the individual had no warning before the sync
        self.assertEqual(len(Individual.objects.filter(inaturalist_id=30)[0].warnings.all()), 0)
        # Run inaturalist sync.
        call_command('inaturalist_sync')
        # Assert that the individual has a warning now
        self.assertEqual(len(Individual.objects.filter(inaturalist_id=30)[0].warnings.all()), 1)
        self.assertEqual(Individual.objects.filter(inaturalist_id=30)[0].warnings.all()[0].text, 'not in vespawatch project')

    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_obs_taxon_changed(self):
        """
        We have an observation in our database with a iNaturalist ID, but when we pull from the iNaturalist API
        this observation is not returned.
        So we check the observation individually and in this case we conclude the taxon is not one of the vespawatch taxa.
        It doesn't matter where this observation comes from, we should flag it as "unknown taxon"
        """
        # Create an Individual that already exists in iNaturalist after a previous push
        ind = Individual(
            inaturalist_id=30,
            latitude=51.2003,
            longitude=4.9067,
            observation_time=datetime(2019, 4, 1, 10),
            originates_in_vespawatch=True,
            taxon=self.vv_taxon
        )
        ind.save()

        # Set a return value for the self.get_all_mock. It should return no observations
        self.get_all_mock.return_value = []

        # Set a side effect for the self.get_obs_mock. It should return an observation that has no vespawatch project id
        self.get_obs_mock.return_value = {
            'id': 30,
            'community_taxon_id': 2165,
            'geojson': {
                'coordinates': [10, 20]
            },
            'photos': [],
            'project_ids': [settings.VESPAWATCH_PROJECT_ID]
        }

        # Assert that the individual had no warning before the sync
        self.assertEqual(len(Individual.objects.filter(inaturalist_id=30)[0].warnings.all()), 0)
        # Run inaturalist sync.
        call_command('inaturalist_sync')
        # Assert that the individual has a warning now
        self.assertEqual(len(Individual.objects.filter(inaturalist_id=30)[0].warnings.all()), 1)
        self.assertEqual(Individual.objects.filter(inaturalist_id=30)[0].warnings.all()[0].text, 'unknown taxon')

    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_obs_vw_evidence_changed_to_indiv(self):
        """

        """
        nest = Nest(
            inaturalist_id=30,
            latitude=51.2003,
            longitude=4.9067,
            observation_time=datetime(2019, 4, 1, 10),
            originates_in_vespawatch=True,
            taxon=self.vv_taxon
        )
        nest.save()

        self.get_all_mock.return_value = [
            {
                'id': 30,
                'community_taxon_id': INAT_VV_TAXONS_IDS[0],
                'geojson': {
                    'coordinates': [10, 20]
                },
                'ofvs': [
                    {'field_id': settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID, 'value': 'indiv'}
                ],
                'photos': []
            }
        ]
        # Run inaturalist sync.
        call_command('inaturalist_sync')
        # Assert that the nest has a warning now
        self.assertEqual(len(nest.warnings.all()), 1)
        self.assertEqual(nest.warnings.all()[0].text, 'individual at inaturalist')

    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_obs_vw_evidence_changed_to_nest_orig_vw(self):
        """
        An individual was flagged as a nest on iNaturalist
          -> the observation originated in vespawatch => flag as "nest at inaturalist"

        """
        # Create an Individual that already exists in iNaturalist after a previous push
        ind = Individual(
            inaturalist_id=30,
            latitude=51.2003,
            longitude=4.9067,
            observation_time=datetime(2019, 4, 1, 10),
            originates_in_vespawatch=True,
            taxon=self.vv_taxon
        )
        ind.save()

        self.get_all_mock.return_value = [
            {
                'id': 30,
                'community_taxon_id': INAT_VV_TAXONS_IDS[0],
                'geojson': {
                    'coordinates': [10, 20]
                },
                'ofvs': [
                    {'field_id': settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID, 'value': 'nest'}
                ],
                'photos': []
            }
        ]
        # Run inaturalist sync.
        call_command('inaturalist_sync')
        # Assert that the nest has a warning now
        self.assertEqual(len(ind.warnings.all()), 1)
        self.assertEqual(ind.warnings.all()[0].text, 'nest at inaturalist')

    @override_settings(INATURALIST_PUSH=False)
    def test_sync_pull_obs_vw_evidence_changed_to_nest_orig_inat(self):
        """
        An individual was flagged as a nest on iNaturalist
          -> the observation originated in inaturalist => delete the individual and create a nest

        """
        # Create an Individual that already exists in iNaturalist after a previous push
        ind = Individual(
            inaturalist_id=30,
            latitude=51.2003,
            longitude=4.9067,
            observation_time=datetime(2019, 4, 1, 10),
            originates_in_vespawatch=False,
            taxon=self.vv_taxon
        )
        ind.save()

        self.get_all_mock.return_value = [
            {
                'id': 30,
                'community_taxon_id': INAT_VV_TAXONS_IDS[0],
                'geojson': {
                    'coordinates': [10, 20]
                },
                'ofvs': [
                    {'field_id': settings.VESPAWATCH_EVIDENCE_OBS_FIELD_ID, 'value': 'nest'}
                ],
                'observed_on_string': '2019-04-01T11:20:00+00:00',
                'observed_time_zone': 'Europe/Brussels',
                'photos': [],
                'taxon': {
                    'id': INAT_VV_TAXONS_IDS[0]
                }
            }
        ]

        # Assert no nests exist before syncing
        self.assertEqual(len(Nest.objects.all()), 0)

        # Run inaturalist sync.
        call_command('inaturalist_sync')
        # Assert that the nest exists now
        self.assertEqual(len(Nest.objects.all()), 1)
        # Assert that the individual is deleted
        self.assertEqual(len(Individual.objects.all()), 0)
        # And that it is not added to the InatObsToDelete (otherwise we will delete it on iNaturalist at the next push)
        self.assertEqual(len(InatObsToDelete.objects.all()), 0)
