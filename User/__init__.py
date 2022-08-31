from flask import Blueprint

auth_blueprint = Blueprint('user_blueprint', __name__)

from . import routes
from . import models
