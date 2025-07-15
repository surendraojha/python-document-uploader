# app.py
import os 

from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
# Ensure this runs before any imports that rely on env vars
dotenv_path = find_dotenv()
if dotenv_path:
    print(f"DEBUG: Found .env at: {dotenv_path}")
    load_dotenv(dotenv_path, verbose=True)
else:
    print("DEBUG: WARNING: .env file not found. Ensure it's in your project root.")

from flask import Flask
from flask_migrate import Migrate

from routes.cpa.auth import auth_bp 
from routes.cpa.mail import mail_bp 
from routes.cpa.cpa_customer import cpa_customer_bp 

from routes.customer.auth import customer_auth_bp 
from routes.customer.customer_profile import customer_profile_bp
from routes.customer.customer_document import customer_document_bp

from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from models import db
from flask_cors import CORS 

from config.config import Config 





app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)




# JWTManager WITH YOUR APP
jwt = JWTManager(app) 

# Flask-Migrate
migrate = Migrate(app, db)

CORS(app, origins=["http://localhost:3000","http://localhost:3001"], supports_credentials=True)


# register CPA blueprints
app.register_blueprint(auth_bp, name='cpa_auth')
app.register_blueprint(cpa_customer_bp)
app.register_blueprint(mail_bp)


# register customer blueprints
app.register_blueprint(customer_auth_bp, name='customer_auth')
app.register_blueprint(customer_profile_bp)
app.register_blueprint(customer_document_bp)


with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return "App running with separated User and Business models."


if __name__ == '__main__':
    app.run(debug=True)

