from datetime import datetime
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from unittest import mock
from vespawatch.models import Individual, InatObsToDelete, Nest, Taxon


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

        # Create mock classes
        self.get_all_mock = self.get_all_patcher.start()
        self.get_obs_mock = self.get_obs_patcher.start()
        self.get_token_mock = self.get_token_patcher.start()
        self.delete_mock = self.delete_patcher.start()
        self.create_at_inat_mock = self.create_at_inat_patcher.start()
        self.update_at_inat_mock = self.update_at_inat_patcher.start
        self.add_photo_from_inat_mock = self.add_photo_from_inat_patcher.start

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

        # Delete all objects that have been created
        InatObsToDelete.objects.all().delete()
        Individual.objects.all().delete()
        Nest.objects.all().delete()
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

        # Create an Individual that already exists in iNaturalist after a previous push
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

