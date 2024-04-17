from flask import request, jsonify
from dotenv import load_dotenv
from helper import safe_convert
from models import db, Results
from helper import getStatusFromMetric, isObjectWithDatetimeInArray, findHighestZeroDatetime, calSystemDowntime
from app import app

@app.route('/get-all-results', methods=['GET'])
def get_all_results():
    all_results = Results.query.all()
    results = [result.json() for result in all_results]
    return jsonify({"results": results})

@app.route('/get-result/<int:cid>/<int:rows>', methods=['GET'])
def get_metrics_by_cid(cid, rows):
    minutesIntervalDict = {
        15: 1, # return rows every minute
        30: 1, # return rows every minute
        60: 1, # return rows every minute
        180: 3, # return rows every 3 minutes = 60 rows
        360: 5, # return rows every 5 minutes = 72 rows
        720: 6, # return rows every 6 minutes = 120 rows
        1440: 6, # return rows every 6 minutes = 240 rows
        10080: 15, # return rows every 15 minutes = 672 rows (1300, 1315, 1330, 1345)
        43200: 30, # return rows every 30 minutes = 1440 rows (1300, 1330, 1400, 1430)
        129600: 60 # return rows every 60 minutes = 2160 rows (1300, 1400, 1500, 1600)
    }
    try:
        results = Results.query.filter_by(cid=cid).order_by(Results.datetime.desc()).limit(129600)
        results = []
        response = {}
        if results:
            for row in results:
                results.append(row.json())

            aggregatedResults = {
                "CPU Usage": [],
                "Disk Usage": [],
                "Memory Usage": [],
                "Traffic In": [],
                "Traffic Out": [],
                "Traffic Metrics": []
            }
            tempTrafficResults = {
                "Traffic In": [],
                "Traffic Out": []
            }
            if cid != 1 and cid != 7: # if not live component
                for i in range(0, len(results), minutesIntervalDict[rows]):
                    aggregatedResults["CPU Usage"].append({"CPU Usage": results[i]["cpu_usage"], "Datetime": results[i]["datetime"]})
                    aggregatedResults["Disk Usage"].append({"Disk Usage": results[i]["disk_usage"], "Datetime": results[i]["datetime"]})
                    aggregatedResults["Memory Usage"].append({"Memory Usage": results[i]["memory_usage"], "Datetime": results[i]["datetime"]})
                    tempTrafficResults["Traffic In"].append({"Traffic In": results[i]["traffic_in"], "Datetime": results[i]["datetime"]})
                    tempTrafficResults["Traffic Out"].append({"Traffic Out": results[i]["traffic_out"], "Datetime": results[i]["datetime"]})
            else:
                for i in range(0, len(results)):
                    aggregatedResults["CPU Usage"].append({"CPU Usage": results[i]["cpu_usage"], "Datetime": results[i]["datetime"]})
                    aggregatedResults["Disk Usage"].append({"Disk Usage": results[i]["disk_usage"], "Datetime": results[i]["datetime"]})
                    aggregatedResults["Memory Usage"].append({"Memory Usage": results[i]["memory_usage"], "Datetime": results[i]["datetime"]})
                    tempTrafficResults["Traffic In"].append({"Traffic In": results[i]["traffic_in"], "Datetime": results[i]["datetime"]})
                    tempTrafficResults["Traffic Out"].append({"Traffic Out": results[i]["traffic_out"], "Datetime": results[i]["datetime"]})
            datetime_array = [
                item['Datetime'] for item in tempTrafficResults['Traffic In']
            ] + [
                item['Datetime'] for item in tempTrafficResults['Traffic Out']
            ]
            unique_datetime_array = set(datetime_array)
            sorted_datetime_array = sorted(unique_datetime_array, key=lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'))
            aggregatedResults["Traffic Metrics"] = []
            for datetime in sorted_datetime_array:
                traffic_in_arr = tempTrafficResults['Traffic In']
                traffic_out_arr = tempTrafficResults['Traffic Out']
                if isObjectWithDatetimeInArray(traffic_in_arr, datetime) and isObjectWithDatetimeInArray(traffic_out_arr, datetime):
                    aggregatedResults["Traffic Metrics"].append({
                        "Traffic In": traffic_in_arr["Traffic In"],
                        "Traffic Out": traffic_out_arr["Traffic Out"],
                        "Datetime": datetime
                    })
            sys_uptime = results[0]["system_uptime"]
            if sys_uptime == 0:
                earliestZeroDateString = findHighestZeroDatetime(results)['datetime']
                sys_downtime = calSystemDowntime(results[0]["datetime"], earliestZeroDateString)
            else:
                sys_downtime = 0
            response = {
                "msg": "success",
                "data": {
                    "CPU Usage": aggregatedResults["CPU Usage"],
                    "Disk Usage": aggregatedResults["Disk Usage"],
                    "Memory Usage": aggregatedResults["Memory Usage"],
                    "Traffic Metrics": aggregatedResults["Traffic Metrics"],
                    "System Uptime": sys_uptime,
                    "System Downtime": sys_downtime
                }
            }                    
            # Return JSON response with the single result
            return jsonify(response), 200
        else:
            # Return an empty response with status code 404 if no results are found
            return jsonify({}), 404

    except Exception as e:
        # Handle any exceptions that occur during query execution
        error_message = str(e)
        return jsonify({'error': error_message}), 500


@app.route('/get-result-status/<int:cid>/<int:mid>', methods=['POST'])
def get_last_result(cid, mid):
    thresholds = request.json
    # print(f"Thresholds: {thresholds}", flush=True)
    try:
        last_result = Results.query.filter_by(cid=cid, mid=mid).order_by(Results.datetime.desc()).first()
        # app.logger.info("Last Results: %s", last_result)
        # print("Last Results:", last_result, flush=True)

        # Check if any of the metrics exceed the threshold and return the status
        metricsList = ["disk_usage", "cpu_usage", "memory_usage"]

        if last_result:
            print("System uptime:", last_result.system_uptime)
            if last_result.system_uptime == 0:
                return jsonify({"status": "Critical"})
            
            statuses = []
            for metric in metricsList:
                metricValue = getattr(last_result, metric)
                if metricValue is not None:
                    status = getStatusFromMetric(metricValue, thresholds["warning"], thresholds["critical"])
                    # print(f"Metric: {metric}, Value: {metricValue}, Status: {status}", flush=True)
                    statuses.append(status)

            if last_result.traffic_in is not None:
                status = getStatusFromMetric(last_result.traffic_in, thresholds["traffic_in_warning"], thresholds["traffic_in_critical"])
                # print(f"Traffic In: {last_result.traffic_in}, Status: {status}", flush=True)
                statuses.append(status)
            
            if last_result.traffic_out is not None:
                status = getStatusFromMetric(last_result.traffic_out, thresholds["traffic_out_warning"], thresholds["traffic_out_critical"])
                # print(f"Traffic Out: {last_result.traffic_out}, Status: {status}", flush=True)
                statuses.append(status)
                
            if 'Critical' in statuses:
                return jsonify({"status": "Critical"})
            elif 'Warning' in statuses:
                return jsonify({"status": "Warning"})
            else:
                return jsonify({"status": "Normal"})

        else:
            return jsonify({"message": "No result found for the specified cid and mid."})
    except Exception as e:
        # Handle the exception
        error_message = str(e)
        return jsonify({'error': error_message}), 500
    
@app.route('/add-result', methods=['POST'])
def add_result():
    data = request.json

    newResult = Results(
        datetime = data['datetime'],
        mid = safe_convert(data['mid'], int),
        cid = safe_convert(data['cid'], int),
        disk_usage = safe_convert(data['disk_usage'], float),
        traffic_in = safe_convert(data['traffic_in'], int),
        traffic_out = safe_convert(data['traffic_out'], int),
        clock = safe_convert(data['clock'], float),
        cpu_usage = safe_convert(data['cpu_usage'], float),
        system_uptime = safe_convert(data['system_uptime'], float),
        memory_usage = safe_convert(data['memory_usage'], float)
    )
    # TODO: Take care of foreign key error
    try:
        db.session.add(newResult)
        db.session.commit()
        
        return jsonify({"message": "Result added successfully.", "data": data, "status_code": 200}), 200
    except Exception as e:  
        app.logger.error('An error occurred: %s', e)
        return jsonify({"error": "An unexpected error occurCritical", "details": str(e), "status_code": 500}), 500


@app.route('/delete-result', methods=['DELETE'])
def delete_result():
    try:
        # Assuming the JSON payload contains the criteria for deletion
        data = request.json
        
        # Extracting criteria from the JSON payload
        start_datetime = data['start_datetime']
        end_datetime = data['end_datetime']

        # Perform the deletion based on the provided criteria
        deleted_count = Results.query.filter(Results.datetime >= start_datetime, Results.datetime <= end_datetime).delete()
        
        # Commit the changes to the database
        db.session.commit()

        # Return a response indicating the number of rows deleted
        return jsonify({"message": f"{deleted_count} rows deleted successfully.", "status_code": 200}), 200
    
    except Exception as e:  
        # Log any errors that occur
        app.logger.error('An error occurred during deletion: %s', e)
        # Return an error response
        return jsonify({"error": "An unexpected error occurred during deletion.", "details": str(e), "status_code": 500}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)
