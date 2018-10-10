Python client for the [iNaturalist APIs](https://www.inaturalist.org/pages/api+reference)

# Status: work in progress. Currently implemented:

- Search occurrences (with pagination)
- (Username / password) authentication
- Creating observations
- Upload a picture and assign to an observation
- Search (globally available) observation fields (with pagination)


## TODO:
- Create packaging/setup.py (we depends on requests)
- Design decision: support Python 2 or not?
- Design decision: create a specific Data class (or similar) to act as an abstraction layer of 
iNaturalist?

## API questions:

- pagination: max page size
- how to exactly know which API we're using? prefix?
- Resource Owner Password Credentials... Do we really need an app (with app_client, app_secret, authorized users, ...)?

## Notes: API quirks:

- Searching observations: if using id_above/id_below, do NOT specify a page number, those will conflict 
(but page_size is fine)
- Searching observations: total_results means "remaining results according to your filters", not "total results". 
Hence, if total_results <= "# of requested results", we know the search is complete. 
 