from src.database import DB
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash


db = DB.db_instance()

class User(db.Model):
    __tablename__= 'users'
    id = db.Column(db.String(), primary_key=True, default=str(uuid4()))
    username = db.Column(db.String(),nullable=False)
    password = db.Column(db.Text(), nullable=False) #this CANNOT be commited like this. we need to store the cryptographed password value
    
    def __repr__(self):
        """
        Inherited from db.Model. Allows the representation of the data model as a human readable format
        """
        return f"User {self.username}"
    
    
    def set_password(self, password: str):
        self.password = generate_password_hash(password)
        
    def validate_password(self, password: str):
        return check_password_hash(self.password, password)
    
    @staticmethod
    def by_id(username):
        return User.query.filter_by(username=username).first()
    
    def save(self):
        db.session.add(self)
        db.session.commit()
        
    def delete(self):
        db.session.delete(self)
        db.session.commit()