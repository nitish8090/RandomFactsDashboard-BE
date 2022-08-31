import uuid
import os
import random
import csv
from pathlib import Path
from flask import Flask
from flask import jsonify
from flask import request
from flask_sqlalchemy import SQLAlchemy

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

from . import auth_blueprint
from .models import db, User, Facts

from .email_module import send_forgot_password_link


@auth_blueprint.route("/auth/register/", methods=["POST"])
def register():
    email = request.json.get("email")
    password = request.json.get("password")

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify("User already exists"), 403

    user = User(email=email, password=password)
    db.session.add(user)
    db.session.commit()

    with open(os.path.join(Path(__file__).parent.parent, "random_facts.csv")) as csvfile:
        random_facts = [_[0] for _ in csv.reader(csvfile)]

        # Select 3 facts from the list at random
        db.session.add_all([Facts(user=user.id, fact_text=_) for _ in random.sample(random_facts, 3)])

    db.session.commit()

    return jsonify('Registered')


@auth_blueprint.route("/auth/login/", methods=["POST"])
def login():
    email = request.json.get("email")
    password = request.json.get("password")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify("User not found"), 401

    if user.password == password:
        access_token = create_access_token(identity=email)
        return jsonify(access_token=access_token)
    else:
        return jsonify({"msg": "Bad username or password"}), 401


@auth_blueprint.route("/auth/forgot-password/", methods=["POST"])
def forgot_password():
    email = request.json.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return "User not found", 401

    user.reset_code = str(uuid.uuid4())
    db.session.add(user)
    db.session.commit()

    # send_forgot_password_link(send_to_email=user.email, link_with_passcode='LOL')

    return jsonify({"reset_code": user.reset_code})


@auth_blueprint.route("/auth/reset-password/", methods=["POST"])
def reset_password():
    reset_code = request.json.get("reset_code")
    password = request.json.get("password")

    user = User.query.filter_by(reset_code=reset_code).first()
    if not user:
        return "User not found", 401

    user.password = password
    user.reset_code = None
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "success"})


@auth_blueprint.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


@auth_blueprint.route("/User/GetFacts/", methods=["GET"])
@jwt_required()
def get_user():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()

    user = User.query.filter_by(email=current_user).first()
    if not user:
        return "User not found", 404

    response_data = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "facts": [{"id": f.id, "fact_text": f.fact_text} for f in user.facts]
    }
    return jsonify(response_data), 200


@auth_blueprint.route("/User/<id>/Facts/", methods=["POST"])
@jwt_required()
def post_fact(id):
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()

    user = User.query.filter_by(id=id).first()
    if not user:
        return "User not found", 404

    new_fact = request.json.get("fact_text")
    db.session.add(Facts(user=user.id, fact_text=new_fact))
    db.session.commit()

    return jsonify(f"New facts added"), 200


@auth_blueprint.route("/User/<user_id>/Facts/<fact_id>/", methods=["DELETE"])
@jwt_required()
def delete_facts(user_id, fact_id):
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()

    fact = Facts.query.filter_by(id=fact_id, user=user_id).first()
    if not fact:
        return "fact not found", 404

    db.session.delete(fact)
    db.session.commit()

    return jsonify(f"fact deleted"), 200
