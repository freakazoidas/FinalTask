from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# initialize extensions
db = SQLAlchemy()
bootstrap = Bootstrap()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # configure app
    app.config['SECRET_KEY'] = 'secret-key-goes-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    # initialize extensions with app
    db.init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    migrate = Migrate(app, db)

    # create tables
    with app.app_context():
        db.create_all()

    # import models to register with app
    # register blueprints with app
    from .auth import auth_bp
    from .models import (BillGroupIntermediary, BillGroups, Departments,
                         IndividualBill, Projects,
                         ProjectsDepartmentsIntermediary, User)
    app.register_blueprint(auth_bp)

    from .main import main
    app.register_blueprint(main)

    from .departments import departments_bp
    app.register_blueprint(departments_bp)

    # set up user loader for login manager
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
