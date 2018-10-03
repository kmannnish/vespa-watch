This Python package holds the code used to access iNaturalist APIs.

Let's try to keep it clean/reusable enough so we can imagine releasing it as its own on PyPI later on.

# TODO: Package depends on requests, requires it (+second level-requirements?: certifi, chardet, idna, urllib3) here

- Design decision to be taken: create a specific Data class (or similar) to act as an abstraction layer of 
iNaturalist...

API questions:

- pagination: max page size
- how to exactly know which API we're using? prefix?

API quirks:

- Searching observations: if using id_above/id_below, do NOT specify a page number, those will conflict 
(but page_size is fine)
- Searching observations: total_results means "remaining results according to your filters", not "total results". 
Hence, if total_results <= "# of requested results", we know the search is complete. 
 