# from app import db
# from datetime import datetime

# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     password = db.Column(db.String(128), nullable=False)  # hashed password
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     # Relationship to events
#     events = db.relationship('Event', backref='creator', lazy=True)

# class Event(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     name = db.Column(db.String(120), nullable=False)
#     description = db.Column(db.Text)
#     category = db.Column(db.String(120))
#     event_date = db.Column(db.DateTime)
#     location = db.Column(db.String(200))
#     num_attendees = db.Column(db.Integer, default=0)
#     is_public = db.Column(db.Boolean, default=True)
#     banner_image = db.Column(db.String(256))
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     albums = db.relationship('Album', backref='event', lazy=True)

# class Album(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
#     name = db.Column(db.String(120), nullable=False)
#     visibility = db.Column(db.String(10), nullable=False, default='private')  # 'public' or 'private'
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
