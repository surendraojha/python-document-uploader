from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .User import User
from .Business import Business
from .Customer import Customer
