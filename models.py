from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Machines(db.Model):
    __tablename__ = 'MACHINES'
    mid = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer, db.ForeignKey('SERVICES.sid'))
    name = db.Column(db.Text)
    location = db.Column(db.Text)
    country = db.Column(db.Text)
    iso = db.Column(db.Text)

    def json(self):
        return {
            "mid": self.mid,
            "sid": self.sid,
            "name": self.name,
            "location": self.location,
            "country": self.country,
            "iso":self.iso,
        }

class Results(db.Model):
    __tablename__ = 'RESULTS'
    datetime = db.Column(db.DateTime, primary_key=True)
    mid = db.Column(db.Integer, db.ForeignKey('MACHINES.mid'), primary_key=True)
    cid = db.Column(db.Integer, db.ForeignKey('COMPONENTS.cid'), primary_key=True)
    disk_usage = db.Column(db.Float)
    traffic_in = db.Column(db.Integer)
    traffic_out = db.Column(db.Integer)
    clock = db.Column(db.Float)
    cpu_usage = db.Column(db.Float)
    system_uptime = db.Column(db.Float)
    memory_usage = db.Column(db.Float)

    __table_args__ = (
        db.PrimaryKeyConstraint(datetime, mid, cid),
    )

    def json(self):
        return {
            "datetime": self.datetime.strftime('%Y-%m-%d %H:%M:%S'),  # Format datetime as string
            "mid": self.mid,
            "cid": self.cid,
            "disk_usage": self.disk_usage,
            "traffic_in": self.traffic_in,
            "traffic_out": self.traffic_out,
            "clock": self.clock,
            "cpu_usage": self.cpu_usage,
            "system_uptime": self.system_uptime,
            "memory_usage": self.memory_usage
        }

class Services(db.Model):
    __tablename__ = 'SERVICES'
    sid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)

    def json(self):
        return {
            "sid": self.sid,    
            "name": self.name
        }
    
class Components(db.Model):
    __tablename__ = 'COMPONENTS'
    cid = db.Column(db.Integer, primary_key=True)
    mid = db.Column(db.Integer, db.ForeignKey('MACHINES.mid'))
    name = db.Column(db.Text)

    def json(self):
        return {
            "cid": self.cid,
            "mid": self.mid,
            "name": self.name
        }

class Thresholds(db.Model):
    __tablename__ = 'THRESHOLDS'
    cid = db.Column(db.Integer, db.ForeignKey('COMPONENTS.cid'), primary_key=True)
    warning = db.Column(db.Float)
    critical = db.Column(db.Float)
    traffic_in_warning = db.Column(db.Float)
    traffic_in_critical = db.Column(db.Float)
    traffic_out_warning = db.Column(db.Float)
    traffic_out_critical = db.Column(db.Float)

    def json(self):
        return {
            "cid": self.cid,
            "warning": self.warning,
            "critical": self.critical,
            "traffic_in_warning": self.traffic_in_warning,
            "traffic_in_critical": self.traffic_in_critical,
            "traffic_out_warning" : self.traffic_out_warning,
            "traffic_out_critical": self.traffic_out_critical
        }
    
class Pusher(db.Model):
    __tablename__ = 'PUSHER'
    pid = db.Column(db.Integer, primary_key=True)
    appId = db.Column(db.Text)
    key = db.Column(db.Text)
    secret = db.Column(db.Text)
    cluster = db.Column(db.Text)
    useTLS = db.Column(db.Boolean)

    def json(self):
        return {
            "pid": self.pid,
            "appId": self.appId,
            "key": self.key,
            "secret": self.secret,
            "cluster": self.cluster,
            "useTLS": self.useTLS
        }
    
class Notifications(db.Model):
    __tablename__ = 'NOTIFICATIONS'

    nid = db.Column(db.Integer, primary_key=True)
    cid = db.Column(db.Integer, db.ForeignKey('COMPONENTS.cid'))
    isread = db.Column(db.Boolean, default=False)
    reason = db.Column(db.Text)
    datetime = db.Column(db.DateTime)
    lastchecked = db.Column(db.DateTime)
    status = db.Column(db.Text)

    def json(self):
        return {
            "nid": self.nid,
            "cid": self.cid,
            "isread": self.isread,
            "reason": self.reason,
            "datetime": self.datetime.strftime('%Y-%m-%d %H:%M:%S'),  # Format datetime as string
            "status": self.status
        }

class Users(db.Model):
    __tablename__ = 'USERS'
    uid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text)

    def json(self):
        return {
            "uid": self.uid,
            "email": self.email
        }