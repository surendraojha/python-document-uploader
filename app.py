# app.py
import os 
from flask import Flask
from flask_migrate import Migrate
from routes.cpa.auth import auth_bp 
from routes.cpa.cpa_customer import cpa_customer_bp 

from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from models import db

load_dotenv() 

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'fallback-jwt-key')

# Example MySQL config — change to match your setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/cpa_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db with the Flask app
db.init_app(app)

#INITIALIZE JWTManager WITH YOUR APP
jwt = JWTManager(app) 

# Initialize Flask-Migrate
migrate = Migrate(app, db)


# Register the auth blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(cpa_customer_bp)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return "App running with separated User and Business models."

if __name__ == '__main__':
    app.run(debug=True)

