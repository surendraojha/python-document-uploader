import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity 

customer_profile_bp = Blueprint('customer_profile', __name__, url_prefix='/customer')

from models import  Customer,User,db
from lib import helpers
from datetime import datetime


# Customer show API
@customer_profile_bp.route('/customer-profile', methods=['GET'])
@jwt_required() 
def show():
    current_customer_id = get_jwt_identity()
    
    try:
        current_user = Customer.query.filter_by(guid=current_customer_id).first() 
   
        return jsonify(current_user.to_dict(True)), 200

    except Exception as e:
        # Rollback in case of database error
        print(f"Database error during registration: {e}")
        # Return a generic server error
        return jsonify({"statuscode": 500, "message": "An internal server error occurred during registration."}), 500


