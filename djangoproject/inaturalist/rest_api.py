# Code used to access the (read/write, but slow) Rails based API of iNaturalist
# See: https://www.inaturalist.org/pages/api+reference
import requests

INAT_BASE_URL = "https://www.inaturalist.org"


class AuthenticationError(Exception):
    pass


def get_access_token(username, password, app_id, app_secret):
    """
    Get an access token using the user's iNaturalist username and password.

    (you still need an iNaturalist app to do this)

    :param username:
    :param password:
    :param app_id:
    :param app_secret:
    :return: the access token, example use: headers = {"Authorization": "Bearer %s" % access_token}
    """
    payload = {
        'client_id': app_id,
        'client_secret': app_secret,
        'grant_type': "password",
        'username': username,
        'password': password
    }

    response = requests.post(("{base_url}/oauth/token".format(base_url=INAT_BASE_URL)), payload)
    try:
        return response.json()["access_token"]
    except KeyError:
        raise AuthenticationError("Authentication error, please check credentials.")


def _build_auth_header(access_token):
    return {"Authorization": "Bearer %s" % access_token}


def add_photo_to_observation(observation_id, file_object, access_token):
    data = {'observation_photo[observation_id]': observation_id}
    file_data = {'file': file_object}

    response = requests.post(url="{base_url}/observation_photos".format(base_url=INAT_BASE_URL),
                             headers=_build_auth_header(access_token),
                             data=data,
                             files=file_data)

    return response.json()

def create_observations(params, access_token):
    """Create a single or several (if passed an array) observations).

    allowed params: see https://www.inaturalist.org/pages/api+reference#post-observations

    Example:

        params = {'observation':
            {'species_guess': 'Pieris rapae'},
        }

    TODO investigate: according to the doc, we should be able to pass multiple observations (in an array, and in
    renaming observation to observations, but as far as I saw they are not created (while a status of 200 is returned)
    """
    response = requests.post(url="{base_url}/observations.json".format(base_url=INAT_BASE_URL),
                             json=params,
                             headers=_build_auth_header(access_token))
    return response.json()