from datetime import datetime
import time
import pytest
import re
import requests

from app.routers.metrics import *

def test_prometheus_requests_count_first():
    #first call after startup
    response =requests.get("http://127.0.0.1:8000/metrics", auth=("user1", "pw1"))
    assert response.status_code == 200, "Invalid status code"

    response_text = response.text

    regex_pattern = r'total_requests{endpoint="/amarillo-metrics"} 1.0'

    assert re.search(regex_pattern, response_text) is not None, "This is not a fresh run of the site or there is no request counter"

def test_prometheus_requests_count_second():
    #second call after first run
    response =requests.get("http://127.0.0.1:8000/metrics", auth=("user1", "pw1"))
    assert response.status_code == 200, "Invalid status code"

    response_text = response.text

    regex_pattern = r'total_requests{endpoint="/amarillo-metrics"} 2.0'
    assert re.search(regex_pattern, response_text) is not None, "There is no total request counter or not the 2nd call for /amarillo-metrics"

def test_prometheus_region_counter_first():
    #check if there is no request for region (should be 0)
    response = requests.get("http://127.0.0.1:8000/metrics", auth=("user1", "pw1"))
    assert response.status_code == 200, "Invalid status code"

    response_text = response.text
    regex_pattern = r'total_requests{endpoint="/region"} 0.0'
    assert re.search(regex_pattern, response_text) is not None, "There is no total request counter or not the value is not 0 for /region"

def test_prometheus_region_counter_second():
    #call region endpoint, checks if it is the first request
    _ = requests.get("http://127.0.0.1:8000/region/")
    response =requests.get("http://127.0.0.1:8000/metrics", auth=("user1", "pw1"))
    assert response.status_code == 200, "Invalid status code"

    response_text = response.text
    regex_pattern = r'total_requests{endpoint="/region"} 1.0'
    assert re.search(regex_pattern, response_text) is not None, "There is no total request counter or not the 1st call for /region"


def test_custom_prometheus_field():

    response =requests.get("http://127.0.0.1:8000/metrics", auth=("user1", "pw1"))
    assert response.status_code == 200, "Invalid status code"

    response_text = response.text

    regex_pattern = r'amarillo_trips_number_total [0-9]{1,}\.0'
    assert re.search(regex_pattern, response_text) is not None, "There is no custom metric named 'amarillo_trips_number_total'"