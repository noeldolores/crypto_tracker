from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin
from sqlalchemy.dialects.mysql import JSON
from . import db
from flask import current_app as app


class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  role = db.Column(db.String(150))
  email = db.Column(db.String(150), unique=True)
  password = db.Column(db.String(150))
  firstName = db.Column(db.String(150))
  settings = db.Column(JSON)
  currencies = db.relationship('Currency')

  def get_reset_token(self, expires_sec=1800):
    s = Serializer(app.config['SECRET_KEY'], expires_sec)
    return s.dumps({'user_id':self.id}).decode('utf-8')

  @staticmethod
  def verify_reset_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
      user_id = s.loads(token)['user_id']
    except:
      return None
    return User.query.get(user_id)


class Currency(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(150))
  quantity = db.Column(db.Integer)
  value = db.Column(db.Integer)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class CoinGeckoDb(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  coinID = db.Column(db.String(150))
  coinSymbol = db.Column(db.String(150))
  coinName = db.Column(db.String(150))