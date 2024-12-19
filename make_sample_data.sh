#!/bin/sh

# 1. create user with random api key printed to console

file=data/agencyconf/sampleuser.json
if [ -e "$file" ]; then
    echo "Sample user already exists"
else 
    # https://security.stackexchange.com/questions/183948/unix-command-to-generate-cryptographically-secure-random-string
    api_key=$(LC_ALL=C tr -dc '[:alnum:]' < /dev/urandom | head -c20)

    sampleuser_json=`cat <<EOF
    {
        "agency_id":"sampleuser",
        "api_key": "$api_key"
    }
EOF
    `
    mkdir -p data/agencyconf;
    echo ${sampleuser_json} > $file && echo "sampleuser created with api key '$api_key'"
fi 

# 2. create "sampleagency"

file=data/agency/sample.json
if [ -e "$file" ]; then
    echo "Sample agency already exists"
else 
    agency_id="sample"

    sampleagency_json=`cat <<EOF
    {
    "id": "$agency_id",
    "name": "Sample Agency",
    "url": "http://mfdz.de",
    "timezone": "Europe/Berlin",
    "lang": "de",
    "email": "info@mfdz.de"
    }
EOF
    `

    mkdir -p data/agency;
    echo ${sampleagency_json} > data/agency/sample.json && echo "Created sampleagency"
fi 

# ------ CREATE TRIPS -----

now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Stuttgart to Berlin $today at 18:00
trip_id="1001"

trip_json=`cat <<EOF
{
    "id":"$trip_id",
    "agency":"$agency_id",
    "deeplink":"https://mfdz.de/trip/$trip_id",
    "stops":
    [
        {
            "name":"Stuttgart",
            "lat":48.783333,
            "lon":9.183333
        },
        {
            "name":"Berlin",
            "lat":52.520008,
            "lon":13.404954
        }
    ],
    "departureTime":"18:00:00","departureDate":"$(date -I)",
    "lastUpdated": "$now"
}
EOF
`
mkdir -p data/carpool/$agency_id;
echo ${trip_json} > "data/carpool/$agency_id/$trip_id.json" && echo "Created trip $trip_id (Stuttgart to Berlin today at 18:00)"

# --------
# Stuttgart to Frankfurt $tomorrow at 18:00
trip_id="1002"

trip_json=`cat <<EOF
{
    "id":"$trip_id",
    "agency":"$agency_id",
    "deeplink":"https://mfdz.de/trip/$trip_id",
    "stops":
    [
        {
            "name":"Stuttgart",
            "lat":48.783333,
            "lon":9.183333
        },
        {
            "name":"Frankfurt",
            "lat":50.110924,
            "lon":8.682127
        }
    ],
    "departureTime":"18:00:00","departureDate":"$(date -I --date 'next day' )",
    "lastUpdated": "$now"
}
EOF
`
mkdir -p data/carpool/$agency_id;
echo ${trip_json} > "data/carpool/$agency_id/$trip_id.json" && echo "Created trip $trip_id (Stuttgart to Frankfurt tomorrow at 18:00)"

# --------
# Stuttgart to Herrenberg every weekday 7:00
trip_id="1003"

trip_json=`cat <<EOF
{
    "id":"$trip_id",
    "agency":"$agency_id",
    "deeplink":"https://mfdz.de/trip/$trip_id",
    "stops":
    [
        {
            "name":"Stuttgart",
            "lat":48.783333,
            "lon":9.183333
        },
        {
            "name":"Herrenberg",
            "lat":48.596142,
            "lon":8.870090
        }
    ],
    "departureTime":"07:00:00","departureDate":["monday", "tuesday", "wednesday", "thursday", "friday"],
    "lastUpdated": "$now"
}
EOF
`
mkdir -p data/carpool/$agency_id;
echo ${trip_json} > "data/carpool/$agency_id/$trip_id.json" && echo "Created trip $trip_id (Stuttgart to Herrenberg every weekday 7:00)"

# --------
# Stuttgart to München one week ahead at 12:00
trip_id="1004"

trip_json=`cat <<EOF
{
    "id":"$trip_id",
    "agency":"$agency_id",
    "deeplink":"https://mfdz.de/trip/$trip_id",
    "stops":
    [
        {
            "name":"Stuttgart",
            "lat":48.783333,
            "lon":9.183333
        },
        {
            "name":"München",
            "lat":48.135124,
            "lon":11.581981
        }
    ],
    "departureTime":"12:00:00","departureDate":"$(date -I --date 'next week')",
    "lastUpdated": "$now"
}
EOF
`
mkdir -p data/carpool/$agency_id;
echo ${trip_json} > "data/carpool/$agency_id/$trip_id.json" && echo "Created trip $trip_id (Stuttgart to München one week ahead at 12:00)" 
