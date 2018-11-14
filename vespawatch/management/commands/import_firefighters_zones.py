from django.contrib.gis.utils import LayerMapping

from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import FirefightersZone


class Command(VespaWatchCommand):
    help = 'Import the firefighters zone data (name + geometry) from a shapefile.'

    def add_arguments(self, parser):
        parser.add_argument('path_to_shp')
        parser.add_argument(
            '--truncate',
            action='store_true',
            dest='truncate',
            default=False,
            help='Truncate Zones table prior to import',
        )

    def handle(self, *args, **options):
        if options['truncate']:
            self.w('Truncate zones table...', ending='')
            FirefightersZone.objects.all().delete()
            self.w(self.style.SUCCESS('Done.'))

        mapping = {'name': 'BWZone',  # The 'name' model field maps to the 'BWZone' layer field.
                   'mpolygon': 'POLYGON',  # For geometry fields use OGC name.
        }

        lm = LayerMapping(FirefightersZone, options['path_to_shp'], mapping, transaction_mode='autocommit')
        lm.save(stream=self.stdout, verbose=True)