from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from .models import User
from .extensions import db

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # S'assure qu'un token JWT valide est présent
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = db.session.get(User, current_user_id)
            
            if user and user.role == 'admin':
                return fn(*args, **kwargs)
            else:
                return jsonify(message="Accès réservé aux administrateurs"), 403
        return decorator
    return wrapper