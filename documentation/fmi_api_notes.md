# FMI API notes

The Finnish Meteorology Institute's open data API has certain things one should take care to note.

## Service limits

Services contain user specific request limitations:

- Download Service has limit of 20000 requests per day
- View Service has limit of 10000 requests per day
- Download and View Services have combined limit of 600 requests per 5 minutes
- Maximum of 744 Hours can be queried per request, i.e. 31 days exactly.