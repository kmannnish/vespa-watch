# First prototype of a Django command that retrieves all iNaturalist observations from the VespaWatch project and store
# them in the local database

from django.core.management.base import BaseCommand, CommandError

from inaturalist.node_api import get_observations

from django.conf import settings

class Command(BaseCommand):
    help = 'retrieves all iNaturalist observations from the Vespa-Watch project and store them in the database'

    def handle(self, *args, **options):
        r = get_observations(params = {
            'page': 1,
            'project_id': settings.VESPAWATCH_PROJECT_ID
        })

        for result in r['results']:
            self.stdout.write(str(result))