from flask import request, jsonify
from dotenv import load_dotenv
from helper import safe_convert
from models import db, Results
from helper import getStatusFromMetric
from app import app

@app.route('/get-all-results', methods=['GET'])
def get_all_results():
    all_results = Results.query.all()
    results = [result.json() for result in all_results]
    return jsonify({"results": results})

@app.route('/get-result/<int:cid>/<int:rows>', methods=['GET'])
def get_metrics_by_cid(cid, rows):
    try:
        results = Results.query.filter_by(cid=cid).order_by(Results.datetime.desc()).limit(rows)
        results_json = []
        if results:

            for row in results:
                results_json.append(row.json())
                
            # Return JSON response with the single result
            return jsonify(results_json), 200
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
    
    try:
        # Delete all results where cid = 8
        Results.query.filter_by(cid=8).delete()
        
        # Add mock data
        db.session.add_all([result1, result2, result3])
        db.session.commit()
        
        return jsonify({"message": "CID 8 Reset Successfully", "status_code": 200}), 200
    except Exception as e:  
        app.logger.error('An error occurred: %s', e)
        return jsonify({"error": "An unexpected error occurred", "details": str(e), "status_code": 500}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)
