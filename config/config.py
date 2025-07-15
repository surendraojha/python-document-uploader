import os
# No need to load_dotenv here again if it's already done in app.py

class Config:
    # Database configuration
    # Ensure these match your .env keys for the database
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI") 
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AWS S3 Configuration
    # These must match your .env keys
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

    # Flask-JWT-Extended Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") # This is crucial for JWT
    # Other JWT settings if you have them, e.g., token expiry
    # JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # Flask Mail (if you're using it)
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')

    # Flask CORS (if you need specific origins)
    # CORS_ORIGINS = os.getenv("CORS_ORIGINS").split(',') if os.getenv("CORS_ORIGINS") else ["*"]
    # ... any other configuration you have ...

    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() in ('true', '1', 't') # For development
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "a_super_secret_key_that_should_be_long_and_random") # Flask app secret key