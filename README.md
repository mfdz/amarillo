# Amarillo

**CRUD for carpool offers**

An Amarillo is a [yellow-dressed person](https://www.dreamstime.com/sancti-spiritus-cuba-feb-road-spot-amarillos-yellow-ones-who-stop-cars-oblige-driver-to-give-lift-people-waiting-image130186034) helping others to find a car pool in Cuba. 

## Setup

- Python 3.9.2 with pip
- python3-venv

Create a virtual environment `python3 -m venv venv`.

Activate the environment and install the dependencies `pip install -r requirements.txt`.

Run `uvicorn amarillo.main:app`. 

In development, you can use `--reload`. 

## Environment Variables

- `env`
- `ADMIN_TOKEN`

## Security

All endpoints are protected by an API-Key in the HTTP header. 
There is a special *admin* user. 
For this user, the API-Key must be passed in as an environment variable when 
Amarillo is started.

The admin can create additional API-Keys in the `/users` endpoint. This
endpoint is always available but not always shown in `/docs`, especially not
when running in production. 
The Swagger docs for `/users` can be seen on the MFDZ demo server.

Permissions work this way
- the admin is allowed to call all operations on all resources. Only the admin
  can create new API-Keys by POSTing an `users` JSON object to `/users`.
- API-Keys for agencies are allowed to POST/PUT/GET/DELETE their own 
  resources and GET some public resources.  

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

Based on [tiangolo/uvicorn-gunicorn:python3.10-slim](https://github.com/tiangolo/uvicorn-gunicorn-docker)

- build `docker build -t amarillo --build-arg="PLUGINS=amarillo-metrics" .`
- run `docker run --rm --name amarillo -p 8000:80 -e MAX_WORKERS="1" -e ADMIN_TOKEN=$ADMIN_TOKEN -e RIDE2GO_TOKEN=$RIDE2GO_TOKEN -e TZ=Europe/Berlin -v $(pwd)/data:/app/data amarillo`
