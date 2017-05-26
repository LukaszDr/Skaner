from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from flask_login import LoginManager
from flask_openid import OpenID
from config import basedir



basedir = os.path.abspath(os.path.dirname(__file__))

path = 'sqlite:///' + os.path.join(basedir, 'app.db')
engine=create_engine(path,convert_unicode=True)
db_session=scoped_session(sessionmaker(autocomit=False,autoflush=False,bind=engine))

Base = declarative_base()
Base.query=db_session.query_property()

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

db.engine._use_threadlocal = True

db.session=db.create_scoped_session()
db.session.expire_on_commit=True

lm = LoginManager()
lm.init_app(app)
oid = OpenID(app, os.path.join(basedir, 'tmp'))

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from app import views, models

#Base.metadata.create_all(bind=engine)
