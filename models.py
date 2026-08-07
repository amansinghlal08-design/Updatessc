import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), unique=True, index=True)
    username = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), index=True)
    subcategory = db.Column(db.String(100))
    test_number = db.Column(db.Integer, default=1)
    question = db.Column(db.Text)
    options = db.Column(db.Text)
    correct = db.Column(db.Integer)
    explanation = db.Column(db.Text, default='')

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(50))
    subcategory = db.Column(db.String(100))
    total = db.Column(db.Integer)
    correct = db.Column(db.Integer)
    wrong = db.Column(db.Integer)
    skipped = db.Column(db.Integer)
    pct = db.Column(db.Float)
    time_sec = db.Column(db.Integer)
    mode = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class WeakQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    wrong_count = db.Column(db.Integer, default=1)
    last_wrong = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class UserStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    xp = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    last_active = db.Column(db.Date, default=datetime.date.today)
