# Amarillo

**CRUD for carpool offers**

An Amarillo is a [yellow-dressed person](https://www.cubatravelnetwork.com/de/autoverleih-in-kuba/autofahren-auf-kuba) helping others to find a car pool in Cuba. 

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

## Testing

In the top directory, run `pytest app/tests`.

## Docker

Based on [tiangolo/uvicorn-gunicorn:python3.9-slim](https://github.com/tiangolo/uvicorn-gunicorn-docker)

- build `docker build -t amarillo .`
- run `docker run -p 8000:80 -e ADMIN_TOKEN=%ADMIN_TOKEN% -e RIDE2GO_TOKEN=%RIDE2GO_TOKEN% -e TZ=Europe/Berlin -v $(pwd)/data:/app/data amarillo-gunicorn`
