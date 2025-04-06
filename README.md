# Amarillo

**CRUD for carpool offers**

An Amarillo is a [yellow-dressed person](https://oncubanews.com/canaldigital/galerias/por-el-camino/los-amarillos/) helping others to find a car pool in Cuba. 

## Setup

- Python 3.12.9 with pip
- python3-venv

Create a virtual environment `python3 -m venv venv`.

Activate the environment and install the dependencies `pip install -r requirements.txt`.

Amarillo consists of two services: 

* a web service, providing an api for carpool agencies to push carpool data to and for consumers to download the GTFS and GTFS-Realtime date generated from these, and
* an enhancer service, which performs background processes like enhancing carpool offers or schedule-based GTFS and GTFS-RT generation.

To start the webservice, run `ADMIN_TOKEN=<your admin token> uvicorn amarillo.main:app`. In development, you can add `--reload` to have uvicorn detect and reload code changes. 

To start the enhancer service, run `python enhancer.py`.

## Environment Variables

- `env`
- `ADMIN_TOKEN`

## Security

All endpoints are protected by an API-Key in the HTTP header. 
There is a special *admin* user. 
For this user, the API-Key must be passed in as an environment variable when 
Amarillo is started.

The admin can create additional API-Keys in the `/agencyconf` endpoint. This 
endpoint is always available but not always shown in `/docs`, especially not
when running in production. 
The Swagger docs for `/agencyconf` can be seen on the MFDZ demo server. 

Permissions work this way
- the admin is allowed to call all operations on all resources. Only the admin
  can create new API-Keys by POSTing an `AgencyConf` JSON object to `/agencyconf`. 
- API-Keys for agencies are allowed to POST/PUT/GET/DELETE their own 
  resources and GET some public resources.  

## Integrating new carpool agencies

To add a new carpool agency, you need to provide agency metadata, which will be used to generated the GTFS agency.txt and an `agencyconf`, which defines how the agency's carpool 
data is synced and access options. 

### Agency Metadata
To provide agency metadata information, create a json config file `conf/agency/<agency_id>.json`and specify the following information:

```json
{
  "id": "mfdz",
  "name": "MITFAHR|DE|ZENTRALE",
  "url": "http://mfdz.de",
  "timezone": "Europe/Berlin",
  "lang": "de",
  "email": "no-reply@mfdz.de"
}
```

Note: The value of `id` must match the filename's name (without suffix `.json`).

### Agency configuration

For agency configuration, create a file `data/agencyconf/<agency_id>.json` and specify the following information:

```json
{
  "agency_id": "mfdz", 
  "api_key": "<a secret api key, at least 20 chars>",
  "offers_download_url": "http://mfdz.de/carpools/", // url providing an endpoint serving a json array of carpool offers according to Amarillo carpool schema 
  "roles": [
    "carpool_agency", // if agencyconf has role carpool_agency, it may push carpool offers
    "consumer" // if agencyconf has consumer role, it may download gtfs and gtfs-rt data
  ],
  "add_dropoffs_and_pickups": true, // if additional stops along the route should be added, default is true
  "replace_carpool_stops_by_closest_transit_stops": true // if origin and destination should be snapped to closest stop, default is true.
}
```

Note: The value of `agency_id` must match the filename's name (without suffix `.json`).

Note: `add_dropoffs_and_pickups` and `replace_carpool_stops_by_closest_transit_stops` is currently not supported for carpool offers which provide a route geometry (path) instead of having it calculated by Amarillo. For such agencies, `add_dropoffs_and_pickups` and `replace_carpool_stops_by_closest_transit_stops` must be set to `false`.

### Custom Importer
In case an agency does not provide an endpoint serving carpool offers in Amarillo schema, 
a custom importer can be implemented and integrated.

For examples, see `amarillo/services/importing`.

They need to be added in `amarillo/services/sync.py`:

```python
    ...
    async def sync(self, agency_id: str, offers_download_url = None):
      ...  
      elif agency_id == "my-custom-agency":
        importer = MyCustomAgencyImporter(offers_download_url)
      ...
```

## Development

### GTFS-RT python bindings

In case you modify or update the proto-files in amarillo/proto, you'll need to regenerate the python bindings. First, create the python files:

```sh
$ cd amarillo/proto
$ protoc --version
libprotoc 3.21.6
$ protoc --proto_path=. --python_out=../services/gtfsrt gtfs-realtime.proto realtime_extension.proto
$ sed 's/import gtfs_realtime_pb2/import amarillo.services.gtfsrt.gtfs_realtime_pb2/g' ../services/gtfsrt/realtime_extension_pb2.py | sponge ../services/gtfsrt/realtime_extension_pb2.py
```

## Testing

In the top directory, run `pytest amarillo/tests`.

## Docker

Based on [python:3.12-slim](https://hub.docker.com/_/python/)

- build `docker build -t amarillo .`
- run `docker run --rm --name amarillo -p 8000:80 -e MAX_WORKERS="1" -e ADMIN_TOKEN=$ADMIN_TOKEN -e RIDE2GO_TOKEN=$RIDE2GO_TOKEN -e TZ=Europe/Berlin -v $(pwd)/data:/app/data amarillo`
