import datetime
from flask import request, jsonify
from models import *
from datetime import datetime, timedelta

# .first() returns either the item or None, can't use len()
def doesComponentExist(cid):
    """
    A function that checks if a component exists in the database

    Parameters:
    cid (int): The component id
    mid (int): The machine id

    Returns:
    component (object): The component object if it exists, False otherwise
    """
    component = Components.query.filter_by(cid=cid).first()
    if component:
        return component
    else:
        return False
    
# .first() returns either the item or None, can't use len()
def doesThresholdExist(cid):
    """
    A function that checks if a threshold exists in the database

    Parameters:
    cid (int): The component id
    mid (int): The machine id

    Returns:
    threshold (object): The threshold object if it exists, False otherwise
    """
    threshold = Thresholds.query.filter_by(cid=cid).first()
    if threshold:
        return threshold
    else:
        return False
    
def convertLocationToList(location):
    location = location.strip('[').strip(']').split(', ') 
    return location


def safe_convert(value, target_type):
    """
    A function that safely converts a value to a target type
    """
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return None
    
def getStatusFromMetric(metric, warning, critical):
    """
    A function that returns the status of a metric based on the warning and critical thresholds
    """
    if metric > critical:
        return 'Critical'
    elif metric > warning:
        return 'Warning'
    else:
        return 'Normal'
    
def getObjectWithDatetimeInArray(array, datetime, trafficType):
    for obj in array:
        print("obj:", obj)
        if obj["Datetime"] == datetime and obj[trafficType] != "NULL" and obj[trafficType] is not None:
            return obj
    return None

def findHighestZeroDatetime(rawResults):
    earliest_zero_datetime = rawResults[0]
    print("Earliest Zero Datetime:", earliest_zero_datetime)
    for i in range(0, len(rawResults)):
        if rawResults[i].system_uptime == 0:
            earliest_zero_datetime = rawResults[i]
    # print("Earliest Zero Datetime:", earliest_zero_datetime)
    return earliest_zero_datetime

def calSystemDowntime(currentDateString, earliestZeroDateString):
    return (datetime.strptime(currentDateString, '%Y-%m-%d %H:%M:%S') - datetime.strptime(earliestZeroDateString, '%Y-%m-%d %H:%M:%S')).total_seconds()
def isOngoingEvent(lastCheckedTime, currentTime, threshold):
    """
    A function that returns whether a notification is ongoing or not
    """
    # currentTime = datetime.now()
    # currentTime = datetime.strptime("2024-03-30 21:26:00", "%Y-%m-%d %H:%M:%S")
    # lastCheckedTime = datetime.strptime(lastCheckedTime, "%Y-%m-%d %H:%M:%S")
    
    timeDifference = currentTime - lastCheckedTime
    maximumAllowedDifference = timedelta(minutes=threshold)
    print("Current time:", currentTime, "Last checked time:", lastCheckedTime)
    print("Time difference:", timeDifference, "Maximum allowed difference:", maximumAllowedDifference)
    if timeDifference < maximumAllowedDifference:
        return True
    else:
        return False
