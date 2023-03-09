import datetime
from functools import wraps

import jwt
from flask import (Blueprint, Response, flash, jsonify, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse

from .forms import LoginForm, RegistrationForm
from .models import User, db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# JWT token configuration
JWT_SECRET_KEY = 'jwt-secret-key-goes-here'
JWT_EXPIRATION_DELTA = datetime.timedelta(days=1)

def jwt_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]

        if not token:
            token = request.cookies.get('jwt_token')

        if not token:
            return Response('Authorization token is missing.', status=401)

        try:
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except:
            return Response('Authorization token is invalid.', status=401)

        return func(*args, **kwargs)

    return wrapper




@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Check if username or email already exist
        if User.query.filter_by(email=email).first() is not None:
            flash('Email already registered')
            return redirect(url_for('auth.signup'))

        # Add new user to database
        user = User(email=email, name=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))

    return render_template('signup.html', title='Sign Up', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # Check if email is registered and password is correct
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash('Invalid email or password')
            return redirect(url_for('auth.login'))

        # Log user in and generate JWT token
        login_user(user, remember=form.remember_me.data)
        payload = {
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + JWT_EXPIRATION_DELTA
        }
        jwt_token_bytes = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        jwt_token_str = jwt_token_bytes

        response = redirect(url_for('main.index'))
        response.set_cookie('jwt_token', jwt_token_str, httponly=True, secure=True)
        flash('You have been logged in')
        return response

    return render_template('login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))