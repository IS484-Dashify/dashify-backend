from flask import request, jsonify
from models import db, Users    
from helper import doesComponentExist, doesThresholdExist
from app import app

# @app.route('/get-user/<int:uid>', methods=['GET'])
# def get_user_by_id(uid):
#     user = Users.query.filter_by(uid=uid).first()
#     user = user.json()
#     return jsonify({'results': user})

@app.route('/get-user/<string:email>', methods=['GET'])
def get_user_by_email(email):
    user = Users.query.filter_by(email=email).first()
    if(user):
        user = user.json()
        return jsonify({'results': user})
    else:
        return jsonify({'results': {}})

@app.route('/get-all-users', methods=['GET'])
def get_all_users():
    all_users = Users.query.all()
    users = [user.json() for user in all_users]
    return jsonify({'results': users})

@app.route('/add-user', methods=['POST'])
def add_user():
    data = request.get_json()
    user = Users(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User added successfully'})

@app.route('/update-user/<string:email>', methods=['PUT'])
def update_user(email):
    user = Users.query.filter_by(email=email).first()
    data = request.get_json()
    user.update(**data)
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

@app.route('/delete-user/<string:email>', methods=['DELETE'])
def delete_user(email):
    user = Users.query.filter_by(email=email).first()
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5010)