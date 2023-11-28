import json
import logging
import os
import random
from typing import Callable

from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from prometheus_client.exposition import generate_latest
from prometheus_client import Gauge, Counter
from prometheus_fastapi_instrumentator.metrics import Info
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import PlainTextResponse

from app.services.secrets import secrets

logger = logging.getLogger(__name__)

security = HTTPBasic()

def amarillo_trips_number_total() -> Callable[[Info], None]:
    METRIC = Gauge("amarillo_trips_number_total", "Total number of trips.")

    def instrumentation(info: Info) -> None:
        trips_count = sum([len(files) for r, d, files in os.walk("./data/carpool")])
        METRIC.set(trips_count)

    return instrumentation


router = APIRouter(
    prefix="/metrics",
    tags=["amarillo_metrics"]
)

@router.get("/")
def metrics(credentials: HTTPBasicCredentials = Depends(security)):
    if (credentials.username != secrets.metrics_user 
        or credentials.password != secrets.metrics_password):

        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    # total_requests_metric.labels(endpoint="/amarillo-metrics").inc()
    return PlainTextResponse(content=generate_latest())
