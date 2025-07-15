import re
from flask import Blueprint, request, jsonify

customer_auth_bp = Blueprint('auth', __name__, url_prefix='/customer')

from models import Customer,db
from flask_jwt_extended import create_access_token



# --- Login API Endpoint ---
@customer_auth_bp.route('/login', methods=['POST'])
def login():
    """
    Handles user login and issues a JWT access token.
    Expects JSON payload with 'email' and 'password'.
    """
    data = request.get_json()
    email = data.get('email')
    requestpassword = data.get('password')

    if not email or not requestpassword:
        return jsonify({"msg": "Missing email or password"}), 400


    customer = Customer.query.filter_by(email=email).first()

    if not customer:
        return jsonify({"msg": "Bad email or password"}), 401

   

    if not customer.check_password(requestpassword):
        return jsonify({"msg": "Bad email or password"}), 401

     # Prepare user information to send back to the client
    user_info = {
        "guid": customer.guid,
        "firstName": customer.firstname,
        "lastName": customer.lastname,
        "email": customer.email,
        "phone": customer.phone 
    }

    additional_claims = {"user_type": "customer"} 

    access_token = create_access_token(identity=customer.guid, additional_claims=additional_claims)

    return jsonify({
        "access_token": access_token,
        "customer": user_info
    }), 200
