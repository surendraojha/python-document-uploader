import uuid
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.dialects.mysql import DATETIME
from datetime import datetime
from . import db

# CustomerDocument model
class CustomerDocument(db.Model):
    __tablename__ = 'customer_documents'
    id = db.Column(db.BigInteger, primary_key=True)
    guid = db.Column(CHAR(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    business_id = db.Column(db.BigInteger,nullable=False)
    customer_id = db.Column(db.BigInteger,nullable=False)

    document_name = db.Column(db.String(50), nullable=False)
    document_path = db.Column(db.String(250),nullable=False)
    file_type = db.Column(db.String(25),nullable=False)
    file_size = db.Column(db.String(25),nullable=False)
    deleted = db.Column(db.Boolean,nullable=False,default=False)
    created_at = db.Column(DATETIME, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(DATETIME, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


    
    def to_dict(self):
        
        document_data = {
            'guid': self.guid,
            'documentName': self.document_name,
            'document_path': self.document_path,
            'fileType': self.file_type,
            'file_size': self.file_size,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
                   
        return document_data

def __repr__(self):
        return f"<Customer {self.email}>"