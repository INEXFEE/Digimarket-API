import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'une-cle-secrete-tres-difficile-a-deviner'
    # SQLALCHEMY_DATABASE_URI sera défini dynamiquement dans create_app pour utiliser app.instance_path
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'une-cle-secrete-jwt-par-defaut' # Clé secrète pour JWT