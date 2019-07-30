from vespawatch.management.commands._utils import VespaWatchCommand
from vespawatch.models import Nest
import requests
import time


class Command(VespaWatchCommand):
    help = '''Use this command to find the municipality of nests'''

    def get_municipality(self, longitude, latitude):
        r = requests.get('https://nominatim.openstreetmap.org/reverse',
                     {'format': 'jsonv2', 'lon': longitude, 'lat': latitude})
        time.sleep(0.2)  # avoid overhitting the API
        if r.ok:
            data = r.json()
            municip = ''
            if 'city' in data['address']:
                municip = data['address']['city']
            elif 'town' in data['address']:
                municip = data['address']['town']
            elif 'county' in data['address']:
                municip = data['address']['county']
            return municip

    def handle(self, *args, **options):
        for nest in Nest.objects.filter(municipality__isnull=True):
            municip = self.get_municipality(nest.longitude, nest.latitude)
            if municip:
                self.w(f'{nest} ({nest.pk}): {municip}')
                nest.municipality = municip
                nest.save()
            else:
                self.w(f'{nest} ({nest.pk}): no municipality found')
