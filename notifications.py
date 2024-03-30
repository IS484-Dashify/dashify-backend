from flask import request, jsonify
from models import db, Notifications
from helper import safe_convert
from app import app

@app.route('/get-all-notifications', methods=['GET'])
def get_all_notifications():
    all_notifications = Notifications.query.all()
    notifications = [notification.json() for notification in all_notifications]
    return jsonify(notifications)

@app.route('/get-notification/<int:cid>/<str:reason>', methods=['GET'])
def get_notification(cid, reason):
    notification = Notifications.query.filter_by(cid=cid, reason=reason).desc().first()
    if notification:
        return jsonify(notification.json()), 200
    else:
        return jsonify({"error": f"Notification with cid {cid} and reason {reason} not found"}), 404


@app.route('/mark-notification-as-read/<int:nid>', methods=['PUT'])
def mark_notification_as_read(nid):
    notification = Notifications.query.filter_by(nid=nid).first()
    if notification:
        try:
            notification.isRead = True
            db.session.merge(notification)
            db.session.commit()
            return jsonify({"message": f"Notification with nid {nid} marked as read successfully"}), 200
        except Exception as e:
            db.session.rollback() 
            return jsonify({"error": "An error occurred while updating the notification."}), 500
    else:
        return jsonify({"error": f"Notification with nid {nid} not found"}), 404

@app.route('/mark-all-notifications-as-read', methods=['PUT'])
def mark_all_notifications_as_read():
    try:
        Notifications.query.update({Notifications.isRead: True})
        db.session.commit()
        return jsonify({"message": "All notifications marked as read successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred while updating the notifications."}), 500

@app.route('/add-notification', methods=['POST'])
def add_notification():
    data = request.json

    newNotification = Notifications(
        cid = safe_convert(data['cid'], int),
        isread = data['isread'],
        reason = data['reason'],
        datetime = data['datetime'],
        lastupdated = data['datetime'],
        status = data['status']
    )
    
    # metricReasonsArr = ["High Traffic In", "High Disk Usage", "High Traffic Out", "High CPU Usage", "High Memory Usage", "System Down"]
    
    try:
        # isOngoing = False
        # for metrics: 'System Down', 'High Disk Ussage', 'High CPU Usage', 'High Memory Usage', check if the notification is ongoing
        # notification is ongoing if lastupdated is within 3 minutes of current time
        
        # for metrics: 'High Traffic In', 'High Traffic Out', check if the notification is ongoing
        # notification is ongoing if lastupdated is within 5 minute of current time
        
        
        
        
        db.session.add(newNotification)
        db.session.commit()
        
        return jsonify({"message": "Notification added successfully.", "data": data, "status_code": 200}), 200
    except Exception as e:  
        app.logger.error('An error occurred: %s', e)
        return jsonify({"error": "An unexpected error occurCritical", "details": str(e), "status_code": 500}), 500
    
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

    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5008)