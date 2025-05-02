from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50))
    entry_timestamp = db.Column(db.DateTime)
    product = db.Column(db.String(50))
    mwh_value = db.Column(db.Float)
    buy_sell = db.Column(db.String(10))  # ✅ NOVÉ POLE
    volume = db.Column(db.Float)
    entry_price = db.Column(db.Float)
    strategy = db.Column(db.String(50))
    exit_price = db.Column(db.Float, nullable=True)
    exit_timestamp = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50))
    exposure = db.Column(db.Float)
    comment = db.Column(db.String(255), nullable=True)


class DictionaryItem(db.Model):
    __tablename__ = 'dictionary_item'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    value = db.Column(db.Integer)  # String to Integer
    __table_args__ = (db.UniqueConstraint('type', 'value', name='_type_value_uc'),)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(50))
    entry_timestamp = db.Column(db.DateTime)
    product = db.Column(db.String(50))
    mwh_value = db.Column(db.Integer)
    buy_sell = db.Column(db.String(10))
    volume = db.Column(db.Float)
    entry_price = db.Column(db.Float)
    strategy = db.Column(db.String(50))
    exit_price = db.Column(db.Float)
    exit_timestamp = db.Column(db.DateTime, nullable=True)
    exposure = db.Column(db.Float)
    comment = db.Column(db.String(255))

def init_db():
    db.create_all()
    seed_dictionaries()

def seed_dictionaries():
    default_values = {
        'source': ['Manual', 'Import'],
        'strategy': ['Strategy 1', 'Strategy 2', 'Strategy 3', 'Strategy 4', 'Strategy 5'],
        'status': ['Open', 'Closed'],
        'mwh_value': [24, 48, 168, 672, 720, 744, 8760],
        'var': [1000000]
        # 'product' intentionally excluded – imported from CSV
    }
    for dict_type, values in default_values.items():
        for value in values:
            exists = DictionaryItem.query.filter_by(type=dict_type, value=value).first()
            if not exists:
                item = DictionaryItem(type=dict_type, value=value)
                db.session.add(item)
    db.session.commit()