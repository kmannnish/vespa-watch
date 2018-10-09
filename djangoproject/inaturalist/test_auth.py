# Test with just sending the username, password and grant_type=password: error 500
# WORKS: We need an app, with its id and secret (we don't really use it, since the app is not linked to the user account, only

import requests

# We need an app_id and secret, even if we only want to access the user content and have his/her password.
# (but no need for the user to authorize the app - creating the app and configuring its user and password is enough)

site = "https://www.inaturalist.org"
app_id = 'd1d0f541791be42e234ce82a5bb8332ab816ff7ab35c6e27b12c0455939a5ea8'
app_secret = ''
username = 'vespawatch'
password = ''

# Send a POST request to /oauth/token with the username and password
payload = {
    'client_id': app_id,
    'client_secret': app_secret,
    'grant_type': "password",
    'username': username,
    'password': password
}
print("POST %s/oauth/token, payload: %s" % (site, payload))
response = requests.post(("%s/oauth/token" % site), payload)
print("RESPONSE")
print(response.content)

# response will be a chunk of JSON looking like
# {
#   "access_token":"xxx",
#   "token_type":"bearer",
#   "expires_in":null,
#   "refresh_token":null,
#   "scope":"write"
# }

# Store the token (access_token) in your app. You can now use it to make authorized
# requests on behalf of the user, like retrieving profile data:
token = response.json()["access_token"]

print("GET %s/users/edit.json, headers: %s" % (site, headers))
print("RESPONSE")
print(requests.get(("%s/users/edit.json" % site), headers=headers).content)
pass