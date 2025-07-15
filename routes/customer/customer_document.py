import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from sqlalchemy.exc import SQLAlchemyError

from flask_jwt_extended import jwt_required, get_jwt_identity
import tempfile

# Assuming these are defined in your models.py
from models import Customer, db, CustomerDocument
from flask import send_file

# Assuming helpers contains get_s3_client or similar if you moved it
customer_document_bp = Blueprint('customer_document', __name__, url_prefix='/customer')

# Allowed file extensions (can be moved to config.py for better centralization)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'xlsx', 'xls', 'ppt', 'pptx'}

def allowed_file(filename):
    """
    Checks if the uploaded file's extension is in the allowed list.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_s3_client():
    """
    Initializes and returns an S3 client using credentials from Flask's current_app config.
    This ensures the client uses the app's loaded configuration.
    """
    return boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_REGION']
    )

@customer_document_bp.route('/document-upload', methods=['POST'])
@jwt_required() # Ensures only authenticated users can access this route
def upload_customer_document():
    """
    Handles the upload of a customer document to AWS S3 and saves its metadata to the database.

    Expects:
    - A file in the request.files dictionary under the key 'file'.
    - JWT token for authentication, which provides the current customer's GUID.
    - Assumes the Customer model has 'guid', 'customer_id', and 'business_id' attributes.
    """
    # Get the current authenticated customer's GUID from the JWT
    current_customer_guid = get_jwt_identity()
    document_name = request.form.get('document_name')

    if not document_name:
        return jsonify({"statuscode": 422, "message": "Document Name field is required"}), 422


    # 1. Fetch Customer details from the database using the GUID
    # This step is crucial to get the BIGINT customer_id and business_id for the CustomerDocument schema.
    try:
        customer_obj = Customer.query.filter_by(guid=current_customer_guid).first()
        if not customer_obj:
            return jsonify({"statuscode": 404, "message": "Authenticated customer not found."}), 404

        # Extract the customer_id and business_id (BIGINT) from the fetched Customer object
        customer_id_for_db = customer_obj.id
        business_id_for_db = customer_obj.business_id

    except Exception as e:
        # Log the error for debugging purposes
        current_app.logger.error(f"Error fetching customer details for GUID {current_customer_guid}: {e}")
        return jsonify({"statuscode": 500, "message": "Failed to retrieve customer information."}), 500

    # 2. Check for file in the request
    if 'file' not in request.files:
        return jsonify({"statuscode": 400, "message": "No file part in the request"}), 400
    file = request.files['file']

    # 3. Check if a file was actually selected (filename is not empty)
    if file.filename == '':
        return jsonify({"statuscode": 400, "message": "No selected file"}), 400

    # 4. Validate the file type/extension
    if not allowed_file(file.filename):
        return jsonify({"statuscode": 400, "message": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    # Proceed with file processing if all checks pass
    if file:
        original_filename = file.filename
        file_extension = original_filename.rsplit('.', 1)[1].lower()

        # Read the entire file content to get its size.
        # IMPORTANT: After reading, the file stream's position is at the end.
        # We must seek(0) to reset it for boto3.upload_fileobj to read from the beginning.
        file_content_bytes = file.read()
        file_size = len(file_content_bytes)
        file.seek(0) # Reset stream position to the beginning

        # Generate a unique filename for S3 to prevent collisions and ensure uniqueness.
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Define the S3 object key (path within the S3 bucket).
        # This structure helps organize files by business and customer.
        s3_object_key = f"businesses/{business_id_for_db}/customers/{customer_id_for_db}/documents/{unique_filename}"

        # Get the S3 client and bucket name from the application configuration
        s3_client_instance = get_s3_client()
        bucket_name = current_app.config['S3_BUCKET_NAME']
        # aws_region = current_app.config['AWS_REGION'] # Not directly used in upload_fileobj, but good for constructing public URLs if needed

        try:
            # 5. Upload the file to AWS S3
            s3_client_instance.upload_fileobj(
                file, # The file-like object from request.files
                bucket_name,
                s3_object_key,
                ExtraArgs={
                    'ContentType': file.content_type or f'application/{file_extension}', # Set MIME type
                    'ACL': 'private' # Set ACL to private for security. Access via presigned URLs.
                }
            )

            # Construct the internal S3 path to store in the database.
            # This is more robust than a public URL if bucket names or regions change.
            s3_object_path_for_db = f"s3://{bucket_name}/{s3_object_key}"

            # 6. Save document metadata to the database using SQLAlchemy
            new_document = CustomerDocument(
                business_id=business_id_for_db,
                customer_id=customer_id_for_db,
                document_name=document_name,
                document_path=s3_object_path_for_db, # Store the internal S3 path
                file_type=file_extension,
                file_size=str(file_size), # Convert file size to string as per your VARCHAR(25) schema
                created_at=datetime.utcnow() # Set the creation timestamp
            )

            db.session.add(new_document) # Add the new document object to the session
            db.session.commit() # Commit the transaction to save to the database

            # Return a success response with relevant metadata
            return jsonify({
                "statuscode": 201,
                "message": "File uploaded successfully and metadata saved!",
                "document_id": new_document.id, # The auto-generated ID from the DB
                "document_guid": new_document.guid, # The auto-generated GUID
                "original_filename": original_filename,
                "s3_object_key": s3_object_key, # The key used in S3
                "file_size": file_size
            }), 201

        except NoCredentialsError:
            db.session.rollback() # Rollback DB session if AWS credentials are missing
            current_app.logger.error("AWS credentials not available or configured incorrectly.")
            return jsonify({"statuscode": 500, "message": "AWS credentials not available or configured incorrectly."}), 500
        except ClientError as e:
            db.session.rollback() # Rollback DB session on S3 client errors
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            current_app.logger.error(f"S3 Client Error: {error_code} - {error_message}")
            return jsonify({"statuscode": 500, "message": f"S3 upload failed: {error_message}"}), 500
        except SQLAlchemyError as e:
            db.session.rollback() # Rollback DB session on SQLAlchemy errors
            current_app.logger.error(f"Database error saving document metadata: {e}")
            return jsonify({"statuscode": 500, "message": "Error saving document metadata to database", "error": str(e)}), 500
        except Exception as e:
            db.session.rollback() # Rollback DB session on any other unexpected error
            current_app.logger.error(f"An unexpected error occurred during document upload: {e}")
            return jsonify({"statuscode": 500, "message": f"An unexpected error occurred: {str(e)}"}), 500

    # Fallback if no file was processed (should be caught by earlier checks, but good to have)
    return jsonify({"statuscode": 400, "message": "Something went wrong during file processing"}), 400


# --- New Download Route ---
@customer_document_bp.route('/document-download/<string:document_guid>', methods=['GET'])
@jwt_required()
def download_customer_document(document_guid):
    """
    Generates a pre-signed URL for downloading a specific customer document from S3.
    Requires a 'document_id' as a query parameter.
    """
    current_customer_guid = get_jwt_identity()

    # 1. Get the document_id from query parameters
    if not document_guid:
        return jsonify({"statuscode": 400, "message": "Missing 'document_id' query parameter."}), 400


    # 2. Fetch authenticated customer details for authorization
    try:
        customer_obj = Customer.query.filter_by(guid=current_customer_guid).first()
        if not customer_obj:
            return jsonify({"statuscode": 404, "message": "Authenticated customer not found."}), 404

    except Exception as e:
        current_app.logger.error(f"Error fetching customer details for download: {e}")
        return jsonify({"statuscode": 500, "message": "Failed to retrieve customer information for authorization."}), 500

    # 3. Retrieve the document metadata from the database
    try:
        document = db.session.query(CustomerDocument).filter_by(
            guid=document_guid,
            customer_id=customer_obj.id, # Ensure document belongs to the authenticated customer
            business_id=customer_obj.business_id   # Ensure document belongs to the customer's business
        ).first()

        if not document:
            return jsonify({"statuscode": 404, "message": "Document not found or unauthorized access."}), 404

    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error retrieving document for download: {e}")
        return jsonify({"statuscode": 500, "message": "Error retrieving document metadata from database."}), 500

    # 4. Extract S3 object key from the stored document_path
    s3_client_instance = get_s3_client()
    bucket_name = current_app.config['S3_BUCKET_NAME']

    # document.document_path is stored as "s3://bucket-name/path/to/object.ext"
    # We need to extract just "path/to/object.ext"
    s3_path_prefix = f"s3://{bucket_name}/"
    if not document.document_path.startswith(s3_path_prefix):
        current_app.logger.error(f"Invalid S3 path format in DB for document {document_id}: {document.document_path}")
        return jsonify({"statuscode": 500, "message": "Internal error: Invalid S3 path stored."}), 500

    s3_object_key = document.document_path[len(s3_path_prefix):]

    # 5. Generate a pre-signed URL for the S3 object
    try:
        # 'get_object' is the S3 action for downloading
        # ExpiresIn sets the validity duration of the URL in seconds (e.g., 300 = 5 minutes)
        # presigned_url = s3_client_instance.generate_presigned_url(
        #     'get_object',
        #     Params={
        #         'Bucket': bucket_name,
        #         'Key': s3_object_key,
        #         'ResponseContentDisposition': f'attachment; filename="{document.document_name}"' # Suggests a filename for download
        #     },
        #     ExpiresIn=300 
        # )
        
        
        s3_response = s3_client_instance.get_object(Bucket=bucket_name, Key=s3_object_key)
        file_data = s3_response['Body'].read()

        # Save to a temp file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file_data)
            tmp_file_path = tmp_file.name

        # Send file to frontend
        return send_file(
            tmp_file_path,
            as_attachment=True,
            download_name=document.document_name,
            mimetype=f"application/{document.file_type or 'octet-stream'}"
        )


        # return jsonify({
        #     "statuscode": 200,
        #     "message": "Pre-signed URL generated successfully.",
        #     "download_url": presigned_url,
        #     "document_name": document.document_name,
        #     "file_type": document.file_type
        # }), 200

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        current_app.logger.error(f"S3 Client Error generating presigned URL for {s3_object_key}: {error_code} - {error_message}")
        return jsonify({"statuscode": 500, "message": f"Error generating download link: {error_message}"}), 500
    except NoCredentialsError:
        current_app.logger.error("AWS credentials not available for presigned URL generation.")
        return jsonify({"statuscode": 500, "message": "AWS credentials not configured correctly."}), 500
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during presigned URL generation: {e}")
        return jsonify({"statuscode": 500, "message": f"An unexpected error occurred: {str(e)}"}), 500



@customer_document_bp.route('/document-list', methods=['GET'])
@jwt_required()
def document_list():
   
    current_customer_guid = get_jwt_identity()

    try:
        customer = Customer.query.filter_by(guid=current_customer_guid).first()
        if not customer:
            return jsonify({"statuscode": 404, "message": "Authenticated customer not found."}), 404

    except Exception as e:
        current_app.logger.error(f"Error fetching customer details for document list: {e}")
        return jsonify({"statuscode": 500, "message": "Failed to retrieve customer information."}), 500

    # 2. Get pagination parameters from query string
    try:
        page = int(request.args.get('page', 1))  # Default to page 1
        per_page = int(request.args.get('perPage', 10)) # Default to 10 items per page

        # Validate parameters to ensure they are positive
        if page < 1 or per_page < 1:
            return jsonify({"statuscode": 400, "message": "Page and per_page parameters must be positive integers."}), 400
        
        # Optional: Limit the maximum per_page to prevent excessively large queries
        if per_page > 100: # Example: allow a maximum of 100 items per page
            per_page = 100

    except ValueError:
        return jsonify({"statuscode": 400, "message": "Invalid 'page' or 'per_page' format. Must be integers."}), 400

    try:
        
        documentLists = CustomerDocument.query.filter_by(
                        customer_id=customer.id,
                        business_id=customer.business_id,
                        deleted=0
                    ).paginate(page=page, per_page=per_page, error_out=False)
   
   
        # Prepare customer data for JSON serialization
        # You'll need to define a way to serialize your Customer model instances.
        # A common approach is to add a .to_dict() method to your model.
        documents_data = [doc.to_dict() for doc in documentLists.items]
      
        # Use Flask-SQLAlchemy's .paginate() method
        # error_out=False prevents raising a 404 error if the page number is out of range,
        # instead it returns an empty items list and appropriate metadata.

        response_data = {
            'documents': documents_data,
            'pagination': {
                'total_items': documentLists.total,
                'total_pages': documentLists.pages,
                'current_page': documentLists.page,
                'per_page': documentLists.per_page,
                'has_next': documentLists.has_next,
                'has_prev': documentLists.has_prev,
                'next_page_num': documentLists.next_num,
                'prev_page_num': documentLists.prev_num,
            },
            'message': 'Customers fetched successfully',
            'status': 200
        }
        return jsonify(response_data), 200

    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error retrieving document list: {e}")
        return jsonify({"statuscode": 500, "message": "Error retrieving document list from database."}), 500
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during document list retrieval: {e}")
        return jsonify({"statuscode": 500, "message": f"An unexpected error occurred: {str(e)}"}), 500
