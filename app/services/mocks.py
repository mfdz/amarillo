import time

mock_trip_updated_added = {
  'id': 'carpool-update-123', 
  'tripUpdate': {
    'trip': {
      'tripId': 'carpool-update-123', 
      'startTime': '07:33:00',
      'startDate': '20220409', 
      'scheduleRelationship': 'ADDED', 
      'routeId': 'carpool-update-123',
      '[transit_realtime.trip_descriptor]': { 'tripUrl' : 'http://myurl'}
    },
    'stopTimeUpdate': [{
      'stopSequence': 1, 
      'arrival': {
        'time': time.mktime((2022,4,9,7,33,0,0,0,0)),
        'uncertainty': 600
      },
      'departure': {
        'time': time.mktime((2022,4,9,7,33,0,0,0,0)),
        'uncertainty': 600
      }, 
      'stopId': 'de:12073:900340108', 
      'scheduleRelationship': 'SCHEDULED'
    },
    { 
      'stopSequence': 2, 
      'arrival': {
        'time': time.mktime((2022,4,9,8,3,0,0,0,0)),
        'uncertainty': 600
      }, 
      'departure': {
        'time': time.mktime((2022,4,9,8,3,0,0,0,0)),
        'uncertainty': 600
      }, 
      'stopId': 'mfdz:Ang001', 
      'scheduleRelationship': 'SCHEDULED'
    }]
  }
}

mock_trip_updated_deleted = {
  'id': 'carpool-update-124', 
  'tripUpdate': {
    'trip': {
      'tripId': '141', 
      'startTime': '17:01:08',
      'startDate': '20220408', 
      'scheduleRelationship': 'CANCELED', 
      'routeId': '141'
    }
  }
}


