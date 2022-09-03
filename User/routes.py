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
from functools import wraps

from flask import Flask
from flask import jsonify

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt
from flask_jwt_extended import JWTManager
from flask_jwt_extended import verify_jwt_in_request

from . import auth_blueprint
from .models import db, User, Facts

from .email_module import send_forgot_password_link


def admin_required():
    """ Decorator function for admin access """

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims["is_administrator"]:
                return fn(*args, **kwargs)
            else:
                return jsonify(msg="Admins only!"), 403

        return decorator

    return wrapper


""" ---------------------- Authentication routes ---------------------- """


@auth_blueprint.route("/auth/register/", methods=["POST"])
def register():
    """
    For registering new user
    Upon registering, 3 random facts will be added to his account
    """
    email = request.json.get("email")
    password = request.json.get("password")
    name = request.json.get("name")

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify("User already exists"), 403

    user = User(email=email, password=password, name=name)
    db.session.add(user)
    db.session.commit()

    user.generate_starting_facts()

    return jsonify('Registered')


@auth_blueprint.route("/auth/login/", methods=["POST"])
def login():
    """ Here auth token will be generated """

    email = request.json.get("email")
    password = request.json.get("password")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify("User not found"), 401

    if user.password == password:
        if user.is_admin:
            access_token = create_access_token(identity=email, additional_claims={"is_administrator": True})
            return jsonify(access_token=access_token, is_rf_admin=True)
        else:
            access_token = create_access_token(identity=email)
            return jsonify(access_token=access_token)
    else:
        return jsonify({"msg": "Bad username or password"}), 401


@auth_blueprint.route("/auth/forgot-password/", methods=["POST"])
def forgot_password():
    """ Reset code will be generated here if forgot password. """
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


""" ---------------------- User routes ---------------------- """


@auth_blueprint.route("/User/", methods=["GET", "POST"])
@admin_required()
def list_create_user():
    # Access the identity of the current user with get_jwt_identity
    # current_user = get_jwt_identity()

    if request.method == 'GET':
        users = User.query.all()
        return jsonify([user.serialize(include_facts=True) for user in users])

    elif request.method == 'POST':
        user = User.query.filter_by(email=request.json.get('email')).first()
        if user:
            return jsonify("User with email already exists"), 400

        try:
            user = User(name=request.json['name'], email=request.json['email'], password='createduser')
        except KeyError as e:
            return jsonify(f"Please send key: {e}"), 400
        else:
            for f in ['address', 'post_code', 'landmark', 'education', 'country', 'state']:
                if request.json.get(f):
                    setattr(user, f, request.json.get(f))
            db.session.add(user)
            db.session.commit()
            user.generate_starting_facts()
            return jsonify(user.serialize(include_facts=True)), 201


@auth_blueprint.route("/User/Profile/", methods=["GET", "PUT"])
@jwt_required()
def user_profile():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()

    user = User.query.filter_by(email=current_user).first()
    if request.method == 'GET':
        return jsonify(user.serialize(include_facts=True))

    elif request.method == 'PUT':
        for f in ['name', 'address', 'post_code', 'landmark', 'education', 'country', 'state']:
            if request.json.get(f):
                setattr(user, f, request.json.get(f))
        db.session.add(user)
        db.session.commit()
        return jsonify(user.serialize(include_facts=True)), 201


@auth_blueprint.route("/User/<user_id>/", methods=["GET", "DELETE", "PUT"])
@admin_required()
def retrieve_delete_user(user_id):
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return "User not found", 404

    if request.method == 'GET':
        return jsonify(user.serialize(include_facts=True, include_is_admin=True)), 200

    elif request.method == "PUT":
        user.is_admin = request.json.get('is_admin')

        for f in ['name', 'email', 'password', 'address', 'post_code', 'landmark', 'education', 'country', 'state']:
            if request.json.get(f):
                setattr(user, f, request.json.get(f))

        db.session.add(user)
        db.session.commit()

        return jsonify(user.serialize()), 201

    elif request.method == 'DELETE':
        if current_user == user.email:
            return jsonify("Cannot delete self"), 409
        db.session.delete(user)
        db.session.commit()

        return jsonify(f"{user.email} deleted"), 204


@auth_blueprint.route("/User/GetFacts/", methods=["GET"])
@jwt_required()
def get_user_facts():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()

    user = User.query.filter_by(email=current_user).first()
    if not user:
        return "User not found", 404

    response_data = user.serialize(include_facts=True)
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
