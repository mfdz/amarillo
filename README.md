# Amarillo

**CRUD for carpool offers**

An Amarillo is a [yellow-dressed person](https://www.cubatravelnetwork.com/de/autoverleih-in-kuba/autofahren-auf-kuba) helping others to find a car pool in Cuba. 

## Setup

- Python 3.9.2 with pip
- python3-venv

Create a virtual environment `python3 -m venv venv`.

Activate the environment and install the dependencies `pip install -r requirements.txt`.

Run `uvicorn app.main:app`. 

In development use `--reload`. In production use `--host 0.0.0.
0 --port 8000`.

## Testing

In the top directory, run `pytest app/tests`.
