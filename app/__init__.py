import os
from flask import Flask, jsonify
from config import Config
from .extensions import db, bcrypt, migrate, jwt

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Assurez-vous que le dossier 'instance' existe
    os.makedirs(app.instance_path, exist_ok=True)
    # Définir l'URI de la base de données pour utiliser le dossier 'instance'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(app.instance_path, "digimarket.db")}'

    # Initialiser les extensions Flask
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Gestion des erreurs JWT personnalisées pour retourner du JSON
    @jwt.unauthorized_loader
    def unauthorized_response(callback):
        return jsonify({"message": "Missing Authorization Header"}), 401

    @jwt.invalid_token_loader
    def invalid_token_response(callback):
        return jsonify({"message": "Signature verification failed"}), 401

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return jsonify({"message": "Token has expired"}), 401

    @jwt.revoked_token_loader
    def revoked_token_response(jwt_header, jwt_payload):
        return jsonify({"message": "Token has been revoked"}), 401

    @jwt.needs_fresh_token_loader
    def needs_fresh_token_response(jwt_header):
        return jsonify({"message": "Fresh token required"}), 401

    # Importer et enregistrer les Blueprints
    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    from .products.routes import products_bp
    app.register_blueprint(products_bp, url_prefix='/api/products')
    from .orders.routes import orders_bp
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    from .categories.routes import categories_bp
    app.register_blueprint(categories_bp, url_prefix='/api/categories')

    # Importer les modèles pour que les migrations les détectent
    from . import models

    # Importer et enregistrer les commandes CLI
    from .commands import seed
    app.cli.add_command(seed)

    return app
