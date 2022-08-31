import datetime
import os

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from User import auth_blueprint
from User.models import db

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
CORS(app)

db.app = app
db.init_app(app)
app.register_blueprint(auth_blueprint)

app.config["JWT_SECRET_KEY"] = 'nitish-secret-key'
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=1)
jwt = JWTManager(app)

