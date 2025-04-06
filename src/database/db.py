from flask_sqlalchemy import SQLAlchemy
#from src.models import * #import all models to initialize the database


class DB:
    """
    Controls database access for resources from the application, centralizing calls to the database itself
    We're starting this model using ORM for organization purposes for later on, should the app's model grow. But for this case,
    a single SQL-based approach would work just fine. For performance reasons, queries can also be done mixing with ORM calls.
    """
    
    instance = None
    
    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(DB, cls).__new__(cls)
        return cls.instance
        
    def __init__(self):
        self._db = SQLAlchemy()
        
    # @property
    def get_instance():
        return DB.instance
    
    # @property
    @staticmethod
    def db_instance():
        if DB.instance is None:
            DB()
        return DB.get_instance()._db
    
    @staticmethod
    def initialize_db(app):
        db = DB.db_instance()
        db.init_app(app)
        with app.app_context():
            db.create_all()
            
    @staticmethod
    def end_db(app):
        db = DB.db_instance()
        with app.app_context():
            db.session.remove()