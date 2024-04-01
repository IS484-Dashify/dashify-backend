from flask import jsonify, request
import requests
from helper import getStatusFromMetric
from app import app

@app.route('/', methods=['GET'])
def index():
    print("Hello, World!");
    return {'message': 'Hello, World!'}

@app.route('/processresult', methods=['POST'])
def processResult():
    metricNotifReason = {
        "traffic_in": "High Traffic In",
        "disk_usage": "High Disk Usage",
        "traffic_out": "High Traffic Out",
        "cpu_usage": "High CPU Usage",
        "memory_usage": "High Memory Usage",
        "system_uptime": "System Down"
    }
    try:
        data = request.json
        print("Raw Data:", data, flush=True)
        rawResult = {
            "mid": int(data['mid']),
            "cid": int(data['cid']),
            "datetime" : data['datetime'],
            "clock": float(data['clock']),
            "system_uptime": float(data['system_uptime']),
            # "disk_usage": float(data['disk_usage']),
            # "traffic_in": int(data['traffic_in']),
            # "traffic_out": int(data['traffic_out']),
            # "cpu_usage": float(data['cpu_usage']),
            # "memory_usage": float(data['memory_usage'])
        }
        if data['disk_usage'] != "NULL":
            rawResult["disk_usage"] = float(data['disk_usage'])
        else:
            rawResult["disk_usage"] = None
        if data['cpu_usage'] != "NULL":
            rawResult["cpu_usage"] = float(data['cpu_usage'])
        else:
            rawResult["cpu_usage"] = None
        if data['memory_usage'] != "NULL":
            rawResult["memory_usage"] = float(data['memory_usage'])
        else:
            rawResult["memory_usage"] = None
        if data['traffic_in'] != "NULL":
            rawResult["traffic_in"] = int(data['traffic_in'])
        else:
            rawResult["traffic_in"] = None
        if data['traffic_out'] != "NULL":
            rawResult["traffic_out"] = int(data['traffic_out'])
        else:
            rawResult["traffic_out"] = None
        cid = rawResult['cid']
        
        # * 0. Get threshold values from the database
        response = requests.get(f'http://127.0.0.1:5005/get-thresholds-by-cid/{cid}').json()
        thresholds = response['results']
        print("Retrieved thresholds:", thresholds, "for cid:", cid, flush=True)
        
        # * 1. Derive statuses from raw data
        # Data from nifi will not be None but string "NULL"
        metricsList = ["disk_usage", "cpu_usage", "memory_usage"]
        if rawResult:
            statuses = {}
            if rawResult['system_uptime'] is not None:
                if rawResult['system_uptime'] == 0:
                    statuses['system_uptime'] = 'Critical' # system is down
                else:
                    statuses['system_uptime'] = 'Normal'
                    
            if statuses['system_uptime'] == 'Normal':           
                for metric in metricsList:
                    if rawResult[metric] is not None:
                        metricStatus = getStatusFromMetric(rawResult[metric], thresholds['warning'], thresholds['critical'])
                        if metricStatus == 'Critical' or metricStatus == 'Warning':
                            statuses[metric] = metricStatus
                    
                if rawResult["traffic_in"] is not None:
                    metricStatus = getStatusFromMetric(rawResult["traffic_in"], thresholds['traffic_in_warning'], thresholds['traffic_in_critical'])
                    if metricStatus == 'Critical' or metricStatus == 'Warning':
                        statuses["traffic_in"] = metricStatus
                    
                if rawResult["traffic_out"] is not None:
                    metricStatus = getStatusFromMetric(rawResult["traffic_out"], thresholds['traffic_out_warning'], thresholds['traffic_out_critical'])
                    if metricStatus == 'Critical' or metricStatus == 'Warning':
                        statuses["traffic_out"] = metricStatus
        print("Statuses:", statuses, flush=True)
            
        # * 2. if any status are Critical/Warning, fire to notification system
        for metric, status in statuses.items():
            if(status == 'Critical' or status == 'Warning'):
                print("Firing notification for", metric, "with status", status, flush=True)
                notifJsonBody = {
                    "cid": rawResult['cid'],
                    "isread": False,
                    "reason": metricNotifReason[metric],
                    "datetime": rawResult['datetime'],
                    "status": status
                }
                requests.post("http://127.0.0.1:5008/add-notification", json=notifJsonBody, headers = {'Content-Type': 'application/json'})        

        # * 3. Store the data in the database
        response = requests.post("http://127.0.0.1:5004/add-result", 
            json=rawResult, 
            headers = {
                'Content-Type': 'application/json', 
            }
        )
        response = response.json()
        # print("Response status:", response)
        if response["status_code"] == 200:
            response_data = {
                'message': 'Data processed successfully',
                'status_code': response["status_code"]
            }
            print("Data added successfully", flush=True)
            return jsonify(response_data), 200
        else:
            # Return relevant information from the response
            response_data = {
                'error': 'Failed to process data',
                'status_code': response["status_code"]
            }
            return jsonify(response_data), 500
        
    except Exception as e:
        # Handle the exception
        print("Error message:", e, flush=True)
        error_message = str(e)
        return jsonify({'error': error_message}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5007)