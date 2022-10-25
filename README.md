# Amarillo

**CRUD for carpool offers**

An Amarillo is a [yellow-dressed person](https://aworldkaleidoscope.com/kuba-spartipps-kuba-authentisch/) helping others to find a car pool in Cuba. 

## Setup

- Python 3.9.2 with pip
- python3-venv

Create a virtual environment `python3 -m venv venv`.

Activate the environment and install the dependencies `pip install -r requirements.txt`.

Run `uvicorn app.main:app`. 

In development, you can use `--reload`. 

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

## Testing

In the top directory, run `pytest app/tests`.

## Docker

Based on [tiangolo/uvicorn-gunicorn:python3.9-slim](https://github.com/tiangolo/uvicorn-gunicorn-docker)

- build `docker build -t amarillo .`
- run `docker run -p 8000:80 -e ADMIN_TOKEN=%ADMIN_TOKEN% -e RIDE2GO_TOKEN=%RIDE2GO_TOKEN% -e TZ=Europe/Berlin -v $(pwd)/data:/app/data amarillo`
