import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity 

cpa_customer_bp = Blueprint('cpa_customer', __name__, url_prefix='/cpa')

from models import  Customer,User,db


# --- Registration  of customer  ---
@cpa_customer_bp.route('/create-customer', methods=['POST'])
@jwt_required() 
def createCustomer():
    """
    Handles new customer registration.
    Expects JSON payload with  'firstName', 'lastName', 'email',
    'phone', 'address', 'password', 'passwordConfirmation'.
    """

 
    current_user_id = get_jwt_identity()
    print(f"[DEBUG] JWT Identity (current_user_id): {current_user_id}") 
    current_user = User.query.filter_by(guid=current_user_id).first() 
    print(f"[DEBUG] Retrieved current_user object: {current_user}") 


    data = request.get_json()

    # Extract data from the request
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')
    phone = data.get('phone')
    address = data.get('address')
    pwd = data.get('password')
    password_confirmation = data.get('passwordConfirmation')

    # Server-side Validation
    errors = {}


    if not first_name:
        errors['firstName'] = 'First name is required.'
    if not last_name:
        errors['lastName'] = 'Last name is required.'

    if not email:
        errors['email'] = 'Email address is required.'
    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors['email'] = 'Email address is invalid.'

    if not phone:
        errors['phone'] = 'Phone is required.'
    if not address:
        errors['address'] = 'Address is required.'

    if not pwd:
        errors['password'] = 'Password is required.'
    elif len(pwd) < 8:
        errors['password'] = 'Password must be at least 8 characters.'
    elif pwd != password_confirmation:
        errors['passwordConfirmation'] = 'Passwords do not match.'

    # If any validation errors, return them
    if errors:
        return jsonify({"statuscode": 422, "errors": errors, "message": "Validation failed"}), 400

    # Check if user with this email already exists
    existing_user = Customer.query.filter_by(email=email).first()
    if existing_user:
        errors['email'] = 'Email address is already registered.'
        return jsonify({"statuscode": 422, "errors": errors, "message": "Email already registered"}), 409

    try:

        new_customer = Customer(
            business_id=current_user.business_id,
            firstname=first_name,
            lastname=last_name,
            email=email,
            phone=phone,
            address=address
        )

       
        new_customer.set_password(pwd) # Hash and set the password

        # Add to session and commit to database
        db.session.add(new_customer)
    
        db.session.commit()

        # Return success response
        return jsonify({"statuscode": 201, "message": "Customer registered successfully"}), 201

    except Exception as e:
        # Rollback in case of database error
        db.session.rollback()
        print(f"Database error during registration: {e}")
        # Return a generic server error
        return jsonify({"statuscode": 500, "message": "An internal server error occurred during registration."}), 500

