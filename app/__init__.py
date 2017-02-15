from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from flask_openid import OpenID
from config import basedir
import RPi.GPIO as GPIO
from encoder import encoder


GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
GPIO.setwarnings(False)

pierwszy=encoder(0,25,18,25)

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
oid = OpenID(app, os.path.join(basedir, 'tmp'))

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from app import views, models
