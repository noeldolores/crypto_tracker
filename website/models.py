from flask_login import UserMixin
from . import db



class Currency(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(150))
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String(150), unique=True)
  password = db.Column(db.String(150))
  firstName = db.Column(db.String(150))
  currencies = db.relationship('Currency')