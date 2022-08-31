import datetime

from flask import Flask
from flask import jsonify
from flask import request
from flask_sqlalchemy import SQLAlchemy

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
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

app.config["JWT_SECRET_KEY"] = "super-secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=1)
jwt = JWTManager(app)




# db.create_all()



