import random
import string
from flask import Blueprint, request, jsonify, current_app, render_template 
from flask_mail import  Message
from datetime import datetime # To get the current year for the template

def generate_random_string(length=8):
    """Generates a random string of specified length using alphanumeric characters."""
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for i in range(length))
    return random_string


def sendCustomerCredentialsEmail(recipient,password):
    
    try:
        subject = 'Welcome to CPA Application - Your Account Credentials'

        msg = Message(
                subject=subject,
                recipients=[recipient]
            )

        plain_body_content = render_template(
            'email/customer_credential_plain.txt',
            recipient_email=recipient,
            user_password=password,
            current_year=datetime.now().year
        )
        
        # --- Render the HTML email from template ---
        html_body_content = render_template(
            'email/customer_credential_html.html',
            recipient_email=recipient,
            user_password=password,
            current_year=datetime.now().year
        )
        
        msg.body = plain_body_content
        msg.html = html_body_content
        
            
        mail_instance = current_app.extensions.get('mail') 

            
        mail_instance.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {recipient}: {e}", exc_info=True)
        return False
    
