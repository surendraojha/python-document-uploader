import re
from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

from models import User, Business,db
from flask_jwt_extended import create_access_token


# --- Registration API Endpoint ---
@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Handles new user registration.
    Expects JSON payload with 'name', 'firstName', 'lastName', 'email',
    'businessPhone', 'contactPhone', 'password', 'passwordConfirmation'.
    """
    data = request.get_json()

    # Extract data from the request
    business_name = data.get('name')
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')
    business_phone = data.get('businessPhone')
    contact_phone = data.get('contactPhone')
    pwd = data.get('password')
    password_confirmation = data.get('passwordConfirmation')

    # Server-side Validation
    errors = {}

    if not business_name:
        errors['name'] = 'Business name is required.'
    if not first_name:
        errors['firstName'] = 'First name is required.'
    if not last_name:
        errors['lastName'] = 'Last name is required.'

    if not email:
        errors['email'] = 'Email address is required.'
    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors['email'] = 'Email address is invalid.'

    if not business_phone:
        errors['businessPhone'] = 'Business phone is required.'
    if not contact_phone:
        errors['contactPhone'] = 'Contact phone is required.'

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
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        errors['email'] = 'Email address is already registered.'
        return jsonify({"statuscode": 422, "errors": errors, "message": "Email already registered"}), 409

    try:

        new_business = Business(
            business_name=business_name,
            business_phone=business_phone,
            contact_phone=contact_phone
        )

        db.session.add(new_business)
        db.session.flush()  # Flush so new_business.id is generated but NOT committed yet

        # Create a new User instance
        new_user = User(
            business_id=new_business.id,
            firstname=first_name,
            lastname=last_name,
            email=email,
            phone=contact_phone
        )
        new_user.set_password(pwd) # Hash and set the password

        # Add to session and commit to database
        db.session.add(new_user)
    
        db.session.commit()

        # Return success response
        return jsonify({"statuscode": 201, "message": "User registered successfully"}), 201

    except Exception as e:
        # Rollback in case of database error
        db.session.rollback()
        print(f"Database error during registration: {e}")
        # Return a generic server error
        return jsonify({"statuscode": 500, "message": "An internal server error occurred during registration."}), 500

# --- Login API Endpoint ---
@auth_bp.route('/login', methods=['POST'])
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


    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"msg": "Bad email or password"}), 401

   

    if not user.check_password(requestpassword):
        return jsonify({"msg": "Bad email or password"}), 401

     # Prepare user information to send back to the client
    user_info = {
        "guid": user.guid,
        "firstName": user.firstname,
        "lastName": user.lastname,
        "email": user.email,
        "phone": user.phone 
    }

    additional_claims = {"user_type": "cpa"} 

    access_token = create_access_token(identity=user.guid, additional_claims=additional_claims)

    return jsonify({
        "access_token": access_token,
        "user": user_info
    }), 200
