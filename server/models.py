from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String)
    bio = db.Column(db.String)

    recipes = db.relationship('Recipe', backref='user')

    def __repr__(self):
        return f'User {self.username}, ID {self.id}'

    # Password property and hashing
    @property
    def password(self):
        raise AttributeError("Password is not accessible!")

    @password.setter
    def password(self, password):
        if not password:
            raise ValueError("Password cannot be empty.")
        # Generate hashed password and store it
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        # Check password against stored hash
        return bcrypt.check_password_hash(self._password_hash, password)

    def authenticate(self, password):
        # Alias for check_password, for test compatibility
        return self.check_password(password)

    # Validations
    @validates('username')
    def validate_username(self, key, username):
        if not username:
            raise ValueError("Username is required.")
        return username
    
class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer)

    # Hide user_id in serialized output and include nested user info
    serialize_rules = ('-user_id', 'user.id', 'user.username')

    # Validations
    @validates('title')
    def validate_title(self, key, title):
        if not title:
            raise ValueError("Title is required.")
        return title

    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if len(instructions) < 50:
            raise ValueError("Instructions must be at least 50 characters long.")
        return instructions