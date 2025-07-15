import re
from flask import Blueprint, request, jsonify, current_app 

mail_bp = Blueprint('mail', __name__, url_prefix='/cpa')


from flask import  request
from flask_mail import  Message

# --- Registration API Endpoint ---
@mail_bp.route('/send-email', methods=['POST'])
def sendEmail():

    if not request.is_json:
        return jsonify(error="Request must be JSON"), 400

    data = request.get_json()

    recipient_email = data.get('recipient')
    email_subject = data.get('subject')
    email_body = data.get('body')
    email_html = data.get('html') # Optional: for HTML content

    # Basic validation of required fields
    if not recipient_email or not email_subject or not (email_body or email_html):
        return jsonify(error="Missing required fields: recipient_email, subject, and either 'body' or 'html'"), 400

    try:
        msg = Message(
            subject=email_subject,
            recipients=[recipient_email]
        )
        
        # Set body or html based on what's provided
        if email_body:
            msg.body = email_body
        if email_html:
            msg.html = email_html
        
        mail_instance = current_app.extensions.get('mail') 

        
        mail_instance.send(msg)
        return jsonify(message=f"Email to {recipient_email} sent successfully!"), 200
    except Exception as e:
        # Log the error for debugging, but return a generic error to the client
        return jsonify(error=f"Failed to send email. Details: {str(e)}"), 500 # Return 500 for server errors
