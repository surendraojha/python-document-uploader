import uuid
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.dialects.mysql import DATETIME
from datetime import datetime  # Add this for using datetime.utcnow if needed

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text # <--- ADD THIS LINE
from . import db

#Business model 
class Business(db.Model):
    __tablename__ = 'businesses'

    id = db.Column(db.BigInteger, primary_key=True)
    guid = db.Column(CHAR(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    business_name = db.Column(db.String(50), nullable=False)
    business_phone = db.Column(db.String(20),nullable=False)
    contact_phone = db.Column(db.String(20),nullable=False)
    deleted = db.Column(db.Boolean,nullable=False,default=False)
    created_at = db.Column(DATETIME, nullable=False, default=datetime.utcnow, server_default= text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(DATETIME, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))

    def __repr__(self):
        return f"<Business {self.name}>"