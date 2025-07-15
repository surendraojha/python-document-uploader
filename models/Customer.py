import uuid
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.dialects.mysql import DATETIME
from datetime import datetime
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
# User model
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.BigInteger, primary_key=True)
    guid = db.Column(CHAR(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    business_id = db.Column(db.BigInteger,nullable=False)
    firstname = db.Column(db.String(25), nullable=False)
    lastname = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(50),nullable=False,unique=True)
    password = db.Column(db.String(200),nullable=False)
    phone = db.Column(db.String(20),nullable=False)
    street_address = db.Column(db.String(100),nullable=False)
    city = db.Column(db.String(25),nullable=False)
    state = db.Column(db.String(2),nullable=False)
    zip_code = db.Column(db.String(5),nullable=False)

    deleted = db.Column(db.Boolean,nullable=False,default=False)
    account_verified = db.Column(db.Boolean,nullable=False,default=True)
    created_at = db.Column(DATETIME, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(DATETIME, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password, pwd)
    
    
    def to_dict(self,include_all=False):
        
        customer_data = {
            'guid': self.guid,
            'firstName': self.firstname,
            'lastName': self.lastname,
            'email': self.email,
            'phone': self.phone
        }
        
        if include_all:
            customer_data.update({
                'streetAddress': self.street_address,
                'city': self.city,
                'state': self.state,
                'zipCode': self.zip_code,

            })
        customer_data.update({
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        })
        
        return customer_data

def __repr__(self):
        return f"<Customer {self.email}>"