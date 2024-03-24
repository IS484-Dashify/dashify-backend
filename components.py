from flask import jsonify, request
from models import Components
from app import app, db
import requests
from dotenv import load_dotenv
from os import environ
import time
load_dotenv()

@app.route('/get-all-components', methods=['GET'])
def get_all_components():
    all_components = Components.query.all()
    components = [component.json() for component in all_components]
    return jsonify({"results": components})

@app.route('/get-component-details-by-cid/<int:cid>', methods=['GET'])
def get_component_details_by_cid(cid):
    component = Components.query.filter_by(cid=cid).first()
    return jsonify(component.json())

@app.route('/get-cid-by-mid/<int:mid>', methods=['GET'])
def get_cid_values_by_mid(mid):
    components = Components.query.filter_by(mid=mid).all()
    cids = [component.cid for component in components]
    return jsonify({"results": cids})

@app.route('/add-component', methods=['POST'])
def add_component():
    data = request.get_json()
    component = Components(data.get('cid'), data.get('mid'), data.get('name'))
    db.session.add(component)
    db.session.commit()
    time.sleep(10)
    try:
        componentExist = Components.query.filter_by(cid=data.get('cid')).first()
        print(componentExist)
    except Exception as e:
        return jsonify({'error': 'There was an error after calling the add component endpoint: ' + str(e)})
    
    try:
        requests.post(environ.get('createThresholdURL'), json={
            "cid": data.get('cid'),
            "Warning": 80,
            "Critical": 90,
            "TrafficInWarning": 800,
            "TrafficInCritical": 1000,
            "TrafficOutWarning": 50000,
            "TrafficOutCritical": 10000
        })
    except Exception as e:
        return jsonify({'error': 'There was an error creating the new component\'s threshold: ' + str(e)})

    try:
        requests.post(environ.get('setupEnvURL'), json={
            "cid": data.get('cid'),
            "email": environ.get('authorisedUserEmail'),
            "vmUsername": data.get('vmUsername'), # target vm's username
            "vmIpAddress": data.get('vmIpAddress'), # target vm's ip address
            "vmPassword": data.get('vmPassword') # target vm's password
        })
    except Exception as e:
        return jsonify({'error': 'There was an error setting up the log monitoring environment for the new component: ' + str(e)})
    
    return jsonify({'message': 'Component added successfully'})

@app.route('/update-component/<int:cid>', methods=['PUT'])
def update_component(cid):
    component = Components.query.filter_by(cid=cid).first()
    data = request.get_json()
    component.update(**data)
    db.session.commit()
    return jsonify({'message': 'Component updated successfully'})

@app.route('/delete-component/<int:cid>', methods=['DELETE'])
def delete_component(cid):
    component = Components.query.filter_by(cid=cid).first()
    db.session.delete(component)
    db.session.commit()
    return jsonify({'message': 'Component deleted successfully'})


    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
