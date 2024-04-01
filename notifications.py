from flask import request, jsonify
from models import db, Notifications
from helper import safe_convert, isOngoingEvent
# from datetime import datetime
from app import app
from sqlalchemy import text

def get_notification_by_cid_and_reason(cid, reason):
    try:
        notification = Notifications.query.filter_by(cid=cid, reason=reason).order_by(Notifications.datetime.desc(), Notifications.nid.desc()).first()
        return notification
    except Exception as e:
        raise Exception(f"Error occurred while retrieving notification: {str(e)}")

@app.route('/get-all-notifications', methods=['GET'])
def get_all_notifications():
    all_notifications = Notifications.query.all()
    notifications = [notification.json() for notification in all_notifications]
    return jsonify(notifications)


@app.route('/mark-notification-as-read/<int:nid>', methods=['PUT'])
def mark_notification_as_read(nid):
    notification = Notifications.query.filter_by(nid=nid).first()
    print("Notification:", notification.json(), flush=True)
    if notification:
        try:
            notification.isread = True
            db.session.merge(notification)
            db.session.commit()
            print("Notification after update:", notification.json(), flush=True)
            return jsonify({"message": f"Notification with nid {nid} marked as read successfully"}), 200
        except Exception as e:
            db.session.rollback() 
            return jsonify({"error": "An error occurred while updating the notification."}), 500
    else:
        return jsonify({"error": f"Notification with nid {nid} not found"}), 404

@app.route('/mark-all-notifications-as-read', methods=['PUT'])
def mark_all_notifications_as_read():
    try:
        Notifications.query.update({Notifications.isread: True})
        db.session.commit()
        return jsonify({"message": "All notifications marked as read successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred while updating the notifications."}), 500

@app.route('/add-notification', methods=['POST'])
def add_notification():
    """
        Used to create a warning or critical alert if notification is not ongoing.
        Else, updates the lastchecked time of the ongoing notification.
        
        # An ongoing notification is:
        # 1. Is a notification of a given cid and same reason
        # 2. where the lastupdated time is within a X time frame of the current time
            for metrics: 'System Down', 'High Disk Usage', 'High CPU Usage', 'High Memory Usage': x is 3 minutes
            for metrics: 'High Traffic In', 'High Traffic Out', check if the notification is ongoing: x is 5 minutes
            
        If the notification is ongoing, the lastchecked time will be updated to current time
        
        However, if the notification is ongoing but the status has changed, a new notification will be created.
    """
    data = request.json

    newNotification = Notifications(
        cid = safe_convert(data['cid'], int),
        isread = data['isread'],
        reason = data['reason'],
        datetime = data['datetime'],
        lastchecked = data['datetime'],
        status = data['status']
    )
    
    metricReasonsArr1 = ["High Disk Usage", "High CPU Usage", "High Memory Usage", "System Down"]
    metricReasonsArr2 = ["High Traffic In", "High Traffic Out"]
    
    try:
        isOngoing = False
        
        existingNotification = get_notification_by_cid_and_reason(newNotification.cid, newNotification.reason)
        
        if existingNotification:
            if newNotification.reason in metricReasonsArr1:
                isOngoing = isOngoingEvent(existingNotification.lastchecked, newNotification['datetime'], 3)
            else:
                isOngoing = isOngoingEvent(existingNotification.lastchecked, newNotification['datetime'], 5)
        else:
            isOngoing = False
            
        print("Ongoing:", isOngoing)
        if not isOngoing:
            db.session.add(newNotification)
            db.session.commit()
            return jsonify({"message": "Notification added successfully.", "notification_added": newNotification.json(), "status_code": 200}), 200
        else:
            if (existingNotification.status != newNotification.status):
                db.session.add(newNotification)
                db.session.commit()
                return jsonify({"message": "Notification added successfully.", "notification_added": newNotification.json(), "status_code": 200}), 200
            else:
                existingNotification.lastchecked = data['datetime']
                # currentTime = datetime.strptime("2024-03-30 21:26:00", "%Y-%m-%d %H:%M:%S")
                # existingNotification.lastchecked = currentTime
                db.session.merge(existingNotification)
                db.session.commit()
                return jsonify({"message": "Notification is ongoing.", "notification_updated": existingNotification.json(), "status_code": 200}), 200
    except Exception as e:  
        app.logger.error('An error occurred: %s', e)
        return jsonify({"error": "An unexpected error occurred", "details": str(e), "status_code": 500}), 500
    
    
@app.route('/add-insight', methods=['POST'])
def add_insight():
    data = request.json

    newNotification = Notifications(
        cid = safe_convert(data['cid'], int),
        isread = data['isread'],
        reason = data['reason'],
        datetime = data['datetime'],
        lastchecked = data['datetime'],
        status = data['status']
    )
    
    try:
        db.session.add(newNotification)
        db.session.commit()
        return jsonify({"message": "Notification added successfully.", "notification_added": newNotification.json(), "status_code": 200}), 200
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e), "status_code": 500}), 500

@app.route('/delete-notification', methods=['DELETE'])
def delete_result():
    try:
        # Perform the deletion based on the provided criteria
        deleted_count = Notifications.query.filter_by(status='Analysis').delete()
        
        # Commit the changes to the database
        db.session.commit()

        # Return a response indicating the number of rows deleted
        return jsonify({"message": f"{deleted_count} rows deleted successfully.", "status_code": 200}), 200
    
    except Exception as e:  
        # Log any errors that occur
        app.logger.error('An error occurred during deletion: %s', e)
        # Return an error response
        return jsonify({"error": "An unexpected error occurred during deletion.", "details": str(e), "status_code": 500}), 500

# @app.route('/add-column', methods=['GET'])
# def add_column():
#     try:
#         # Execute SQL ALTER TABLE statement to add a new column
#         column_name = "LASTCHECKED"
#         sql_query = text(f"ALTER TABLE notifications ADD COLUMN {column_name} DATETIME")
#         db.session.execute(sql_query)
#         db.session.commit()
#         return jsonify({"message": f"Column '{column_name}' added successfully"}), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5008)