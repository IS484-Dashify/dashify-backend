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
        rawResult = {
            "mid": int(data['mid']),
            "cid": int(data['cid']),
            "datetime" : data['datetime'],
            "disk_usage": float(data['disk_usage']),
            "traffic_in": int(data['traffic_in']),
            "traffic_out": int(data['traffic_out']),
            "clock": float(data['clock']),
            "cpu_usage": float(data['cpu_usage']),
            "system_uptime": float(data['system_uptime']),
            "memory_usage": float(data['memory_usage'])
        }
        cid = rawResult['cid']
        
        # * 0. Get threshold values from the database
        response = requests.get(f'http://127.0.0.1:5005/get-thresholds-by-cid/{cid}').json()
        thresholds = response['results']
        
        # * 1. Derive statuses from raw data
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
            
        # * 2. if any status are Critical/Warning, fire to notification system
        print("Statuses:", statuses)
        for metric, status in statuses.items():
            if(status == 'Critical' or status == 'Warning'):
                print("Firing notification for", metric, "with status", status)
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
        error_message = str(e)
        return jsonify({'error': error_message}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5007)