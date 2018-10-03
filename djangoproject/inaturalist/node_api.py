# Code to access the (read-only, but fast) Node based public iNaturalist API
# See: http://api.inaturalist.org/v1/docs/

import requests
from requests.compat import urljoin

INAT_NODE_API_BASE_URL = "https://api.inaturalist.org/v1/"

# Pagination: should we aim for two versions:
#   - Low-level: the package user manage pagination
#   - High-level: we loop so user doesn't need to handle pagination. Should we block then return all results or use
#     yield?


def make_inaturalist_api_get_call(endpoint, params, **kwargs):
    """Make an API call to iNaturalist.

    endpoint is a string such as 'observations' !! do not put / in front
    method: 'GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE'
    kwargs are passed to requests.request
    Returns a requests.Response object
    """
    headers = {'Accept': 'application/json'}

    return requests.get(urljoin(INAT_NODE_API_BASE_URL, endpoint), params, headers=headers, **kwargs)

def get_observations(params):
    """Search observations, see: http://api.inaturalist.org/v1/docs/#!/Observations/get_observations.

    Returns the parsed JSON returned by iNaturalist (observations in r.results)
    """

    '''TODO: Doc says: "The large size of the observations index prevents us from supporting the page parameter when
    retrieving records from large result sets. If you need to retrieve large numbers of records, use the per_page
    and id_above or id_below parameters instead.'''
    r = make_inaturalist_api_get_call('observations', params=params)
    return r.json()

