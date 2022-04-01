import time

mock_trip_updated_added = {
  'id': 'carpool-update-123', 
  'tripUpdate': {
    'trip': {
      'tripId': 'carpool-update-123', 
      'startTime': '07:33:00',
      'startDate': '20220331', 
      'scheduleRelationship': 'ADDED', 
      'routeId': 'carpool-update-123',
      '[transit_realtime.trip_descriptor]': { 'tripUrl' : 'http://myurl'}
    },
    'stopTimeUpdate': [{
      'stopSequence': 1, 
      'departure': {
        'time': time.mktime((2022,3,31,7,33,0,0,0,0)), 
        'uncertainty': 600
      }, 
      'stopId': 'de:08115:4512:1:2', 
      'scheduleRelationship': 'SCHEDULED'
    },
    { 
      'stopSequence': 2, 
      'arrival': {
        'time': time.mktime((2022,3,31,8,3,0,0,0,0)), 
        'uncertainty': 600
      }, 
      'stopId': 'de:08115:5773:1:1', 
      'scheduleRelationship': 'SCHEDULED'
    }]
  }
  }