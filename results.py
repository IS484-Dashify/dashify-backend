from datetime import datetime, timedelta
from flask import request, jsonify
from dotenv import load_dotenv
from helper import safe_convert
from models import db, Results
from helper import getStatusFromMetric, getObjectWithDatetimeInArray, findHighestZeroDatetime, calSystemDowntime
from app import app

@app.route('/get-all-results', methods=['GET'])
def get_all_results():
    all_results = Results.query.all()
    results = [result.json() for result in all_results]
    return jsonify({"results": results})
    
@app.route('/get-result/<int:cid>/<int:mins>', methods=['GET'])
def get_metrics_by_cid(cid, mins):
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
        first_entry = Results.query.filter_by(cid=cid).order_by(Results.datetime.desc()).first()
        response = {}
        if first_entry:
            ninetyDaysAGo = first_entry.datetime - timedelta(minutes=129600) 
            # Retrieve all rows where datetime is within the last 90 days of the first entry in descending order
            rawTrafficResults = Results.query.filter(
                Results.cid == cid,
                Results.datetime >= ninetyDaysAGo,
                Results.traffic_in.isnot(None),
                Results.traffic_out.isnot(None)
            ).order_by(Results.datetime.desc())

            rawResults = Results.query.filter(
                Results.cid == cid,
                Results.datetime >= ninetyDaysAGo
            ).order_by(Results.datetime.desc())
            aggregatedResults = {
                "CPU Usage": [],
                "Disk Usage": [],
                "Memory Usage": [],
                "Traffic Metrics": [],
            }
            rawResultsList = rawResults.all()
            rawTrafficResultsList = rawTrafficResults.all()
            startTime = first_entry.datetime - timedelta(minutes=mins) # refers to lower boundary of selectedTimeRange

            for i in range(0, len(rawResultsList), minutesIntervalDict[mins]):
                if rawResultsList[i].datetime >= startTime:
                    formatted_datetime = rawResultsList[i].datetime.strftime("%d %b %y, %#I:%M:%S%p")
                    aggregatedResults["CPU Usage"].append({"CPU Usage": rawResultsList[i].cpu_usage, "Datetime": formatted_datetime})
                    aggregatedResults["Disk Usage"].append({"Disk Usage": rawResultsList[i].disk_usage, "Datetime": formatted_datetime })
                    aggregatedResults["Memory Usage"].append({"Memory Usage": rawResultsList[i].memory_usage, "Datetime": formatted_datetime})

            for i in range(0, len(rawTrafficResultsList), minutesIntervalDict[mins]):
                if rawResultsList[i].datetime >= startTime:
                    formatted_datetime = rawTrafficResultsList[i].datetime.strftime("%d %b %y, %#I:%M:%S%p")
                    aggregatedResults["Traffic Metrics"].append({"Traffic In": rawTrafficResultsList[i].traffic_in, "Traffic Out": rawTrafficResultsList[i].traffic_out, "Datetime": formatted_datetime })

            sys_uptime = rawResultsList[0].system_uptime
            if sys_uptime == 0:
                earliestZeroDateString = findHighestZeroDatetime(rawResultsList)['datetime']
                sys_downtime = calSystemDowntime(rawResultsList[0]["datetime"], earliestZeroDateString)
            else:
                sys_downtime = 0
                
            response = {
                "msg": "successfully retrieved results for cid " + str(cid),
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
            return jsonify({"msg": "No results found for cid " + str(cid)}), 404

    except Exception as e:
        # Handle any exceptions that occur during query execution
        print("Error message: ", str(e))
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

@app.route('/reset-cid-8', methods=['GET'])
def reset_cid_8():

    # Create mock data
    result1 = Results(datetime = "2024-04-05 21:00:00", mid = 3, cid = 8, disk_usage = 0.35, traffic_in = 80, traffic_out = 5000, clock = 1709200000.0, cpu_usage = 2.35, system_uptime = 500, memory_usage = 0.35)
    result2 = Results(datetime = "2024-04-05 21:01:00", mid = 3, cid = 8, disk_usage = 0.4, traffic_in = 90, traffic_out = 5100, clock = 1709200000.0, cpu_usage = 2.45, system_uptime = 600, memory_usage = 0.35)
    result3 = Results(datetime = "2024-04-05 21:02:00", mid = 3, cid = 8, disk_usage = 0.38, traffic_in = 86, traffic_out = 5200, clock = 1709200000.0, cpu_usage = 2.56, system_uptime = 700, memory_usage = 0.45)
    result4 = Results(datetime = "2024-04-05 21:03:00", mid = 3, cid = 8, disk_usage = 0.42, traffic_in = 95, traffic_out = 5300, clock = 1709200000.0, cpu_usage = 2.65, system_uptime = 800, memory_usage = 0.55)
    result5 = Results(datetime = "2024-04-05 21:04:00", mid = 3, cid = 8, disk_usage = 0.45, traffic_in = 100, traffic_out = 5400, clock = 1709200000.0, cpu_usage = 2.75, system_uptime = 900, memory_usage = 0.65)
    result6 = Results(datetime = "2024-04-05 21:05:00", mid = 3, cid = 8, disk_usage = 0.48, traffic_in = 105, traffic_out = 5500, clock = 1709200000.0, cpu_usage = 2.85, system_uptime = 1000, memory_usage = 0.75)
    result7 = Results(datetime = "2024-04-05 21:06:00", mid = 3, cid = 8, disk_usage = 0.5, traffic_in = 110, traffic_out = 5600, clock = 1709200000.0, cpu_usage = 2.95, system_uptime = 1100, memory_usage = 0.85)
    result8 = Results(datetime = "2024-04-05 21:07:00", mid = 3, cid = 8, disk_usage = 0.55, traffic_in = 115, traffic_out = 5700, clock = 1709200000.0, cpu_usage = 3.05, system_uptime = 1200, memory_usage = 0.95)
    result9 = Results(datetime = "2024-04-05 21:08:00", mid = 3, cid = 8, disk_usage = 0.6, traffic_in = 120, traffic_out = 5800, clock = 1709200000.0, cpu_usage = 3.15, system_uptime = 1300, memory_usage = 1.05)
    result10 = Results(datetime = "2024-04-05 21:09:00", mid = 3, cid = 8, disk_usage = 0.65, traffic_in = 125, traffic_out = 5900, clock = 1709200000.0, cpu_usage = 3.25, system_uptime = 1400, memory_usage = 1.15)
    
    try:
        # Delete all results where cid = 8
        Results.query.filter_by(cid=8).delete()
        
        # Add mock data
        db.session.add_all([result1, result2, result3, result4, result5, result6, result7, result8, result9, result10])
        db.session.commit()
        
        return jsonify({"message": "CID 8 Reset Successfully", "status_code": 200}), 200
    except Exception as e:  
        app.logger.error('An error occurred: %s', e)
        return jsonify({"error": "An unexpected error occurred", "details": str(e), "status_code": 500}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)
