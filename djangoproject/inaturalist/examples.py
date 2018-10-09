import datetime

from inaturalist.node_api import get_all_observations
from inaturalist.rest_api import get_access_token, create_observations, add_photo_to_observation, \
    get_observation_fields, get_all_observation_fields

from inaturalist.credentials import VESPAWATCH_APP_SECRET, VESPAWATCH_USER_PASSWORD

token = get_access_token(username='vespawatch', password=VESPAWATCH_USER_PASSWORD,
                         app_id='d1d0f541791be42e234ce82a5bb8332ab816ff7ab35c6e27b12c0455939a5ea8',
                         app_secret=VESPAWATCH_APP_SECRET)


#obs = get_all_observations(params={'user_id': 'niconoe'})

# params = {'observation':{'taxon_id': 54327,  # Vespa Crabro
#                          'observed_on_string': datetime.datetime.now().isoformat(),
#                          'time_zone': 'Brussels',
#                          'description': 'This is a test for the VespaWatch project',
#                          'tag_list': 'vespawatch, wasp, Flanders',
#                          'latitude': 50.647143,
#                          'longitude': 4.360216,
#                          'positional_accuracy': 50 # meters
#                          },
#  }
#
# r = create_observations(params=params, access_token=token)
#
# r = add_photo_to_observation(observation_id=r[0]['id'], file_object=open('/Users/nicolasnoe/vespa.jpg', 'rb'), access_token=token)

r = get_all_observation_fields(search_query="DNA")
pass