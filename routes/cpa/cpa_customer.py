import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity 

cpa_customer_bp = Blueprint('cpa_customer', __name__, url_prefix='/cpa')

from models import  Customer,User,db
from lib import helpers
from datetime import datetime


# Customer list API
@cpa_customer_bp.route('/customer-list', methods=['GET'])
@jwt_required() 
def list():
    """
    Handles new customer registration.
    Expects JSON payload with  'firstName', 'lastName', 'email',
    'phone', 'address', 'password', 'passwordConfirmation'.
    """

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('perPage', 10, type=int)
    
    if per_page > 100: 
        per_page = 100
        
    current_user_id = get_jwt_identity()
    current_user = User.query.filter_by(guid=current_user_id).first() 
 
 
    try:
        customerLists = Customer.query.filter_by(
                        business_id=current_user.business_id,
                        deleted=0
                    ).paginate(page=page, per_page=per_page, error_out=False)
   
   
        # Prepare customer data for JSON serialization
        # You'll need to define a way to serialize your Customer model instances.
        # A common approach is to add a .to_dict() method to your model.
        customers_data = [customer.to_dict() for customer in customerLists.items]

        # Construct the response payload
        response_data = {
            'customers': customers_data,
            'pagination': {
                'total_items': customerLists.total,
                'total_pages': customerLists.pages,
                'current_page': customerLists.page,
                'per_page': customerLists.per_page,
                'has_next': customerLists.has_next,
                'has_prev': customerLists.has_prev,
                'next_page_num': customerLists.next_num,
                'prev_page_num': customerLists.prev_num,
            },
            'message': 'Customers fetched successfully',
            'status': 200
        }
        return jsonify(response_data), 200

    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error fetching customers: {e}")
        return jsonify({
            'message': 'An error occurred while fetching customers.',
            'status': 500,
            'error': str(e) # Only include detailed error in development, not production
        }), 500


# Customer show API
@cpa_customer_bp.route('/customer-show/<string:customer_guid>', methods=['GET'])
@jwt_required() 
def show(customer_guid):
    current_user_id = get_jwt_identity()
    current_user = User.query.filter_by(guid=current_user_id).first() 
    
    try:
        customer = Customer.query.filter_by(
                        guid=customer_guid,
                        business_id=current_user.business_id,
                        deleted=0
                    ).first()
   
   
   
        return jsonify(customer.to_dict(True)), 200

    except Exception as e:
        # Rollback in case of database error
        print(f"Database error during registration: {e}")
        # Return a generic server error
        return jsonify({"statuscode": 500, "message": "An internal server error occurred during registration."}), 500



# --- Registration  of customer  ---
@cpa_customer_bp.route('/create-customer', methods=['POST'])
@jwt_required() 
def store():
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
    street_address = data.get('streetAddress')
    city = data.get('city')
    state = data.get('state')
    zip_code = data.get('zipCode')
    pwd = helpers.generate_random_string(8)

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
   
    if not street_address:
        errors['streetAddress'] = 'streetAddress is required.'
        
    if not city:
        errors['city'] = 'City is required.'
        
    if not state:
        errors['state'] = 'State is required.'
        
    if len(state) != 2:
        errors['state'] = 'State must be a 2-character abbreviation.'
        
    if not zip_code:
        errors['zipCode'] = 'zip code is required.'
    
    if len(zip_code) != 5:
        errors['state'] = 'Zip code must be a 5-characters long.'
    # If any validation errors, return them
    if errors:
        return jsonify({"statuscode": 422, "errors": errors, "message": "Validation failed"}), 400

    # Check if user with this email already exists
    existing_user = Customer.query.filter_by(email=email,deleted=0).first()
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
            street_address=street_address,
            city=city,
            state=state,
            zip_code=zip_code,

        )

       
        new_customer.set_password(pwd) # Hash and set the password

        # Add to session and commit to database
        db.session.add(new_customer)
    
        db.session.commit()
        
        helpers.sendCustomerCredentialsEmail(email,pwd)

        # Return success response
        return jsonify({"statuscode": 201, "message": "Customer registered successfully"}), 201

    except Exception as e:
        # Rollback in case of database error
        db.session.rollback()
        print(f"Database error during registration: {e}")
        # Return a generic server error
        return jsonify({"statuscode": 500, "message": "An internal server error occurred during registration."}), 500


# --- Update  of customer  ---
@cpa_customer_bp.route('/update-customer/<string:customer_guid>', methods=['PUT','PATCH'])
@jwt_required() 
def update(customer_guid):
    """
    Handles new customer registration.
    Expects JSON payload with  'firstName', 'lastName', 'email',
    'phone', 'address', 'password', 'passwordConfirmation'.
    """

 
    current_user_id = get_jwt_identity()
    print(f"[DEBUG] JWT Identity (current_user_id): {current_user_id}") 
    current_user = User.query.filter_by(guid=current_user_id).first() 
    print(f"[DEBUG] Retrieved current_user object: {current_user}") 

    customer = Customer.query.filter_by(guid=customer_guid,business_id=current_user.business_id,deleted=0).first()

    # 404 Not Found if customer doesn't exist or doesn't belong to current business
    if not customer:
        return jsonify({
            'message': 'Customer not found or does not belong to your business.',
            'status': 404
        }), 404

    data = request.get_json()

    # Extract data from the request
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')
    phone = data.get('phone')
    street_address = data.get('streetAddress')
    city = data.get('city')
    state = data.get('state')
    zip_code = data.get('zipCode')
    pwd = helpers.generate_random_string(8)

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
   
    if not street_address:
        errors['streetAddress'] = 'streetAddress is required.'
        
    if not city:
        errors['city'] = 'City is required.'
        
    if not state:
        errors['state'] = 'State is required.'
        
    if len(state) != 2:
        errors['state'] = 'State must be a 2-character abbreviation.'
        
    if not zip_code:
        errors['zipCode'] = 'zip code is required.'
    
    if len(zip_code) != 5:
        errors['state'] = 'Zip code must be a 5-characters long.'
  
  
    existing_customer_with_email = Customer.query.filter(
                Customer.email == email,
                Customer.guid != customer_guid, 
                Customer.deleted == 0
            ).first()
    
    if existing_customer_with_email:
                errors['email'] = 'Email address is already registered by another customer in this business.'

    # If any validation errors, return them
    if errors:
        return jsonify({"statuscode": 422, "errors": errors, "message": "Validation failed"}), 400

    try:

        customer.firstname = first_name
        customer.lastname = last_name
        customer.email = email
        customer.phone = phone 
        customer.street_address = street_address
        customer.city = city 
        customer.state = state 
        customer.zip_code = zip_code 
        customer.updated_at = datetime.utcnow()

        # Add to session and commit to database
    
        db.session.commit()
        
        helpers.sendCustomerCredentialsEmail(email,pwd)

        # Return success response
        return jsonify({"statuscode": 201, "message": "Customer registered successfully"}), 201

    except Exception as e:
        # Rollback in case of database error
        db.session.rollback()
        print(f"Database error during registration: {e}")
        # Return a generic server error
        return jsonify({"statuscode": 500, "message": "An internal server error occurred during registration."}), 500

