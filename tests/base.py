import unittest
import json
from app import create_app
from app.extensions import db
from app.models import User
from config import Config

class TestConfig(Config):
    """Configuration spécifique pour les tests."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    BCRYPT_LOG_ROUNDS = 4
    JWT_SECRET_KEY = 'test-jwt-secret-key'

class BaseTestCase(unittest.TestCase):
    """Classe de base pour les tests qui configure l'application et la base de données."""

    def setUp(self):
        """Configuration initiale pour chaque test."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """Nettoyage après chaque test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _setup_users_and_tokens(self):
        """Crée un utilisateur client et un utilisateur admin, et leurs tokens."""
        self.client_user = User(email='client@example.com', password='password123', role='client')
        self.admin_user = User(email='admin@example.com', password='password123', role='admin')
        db.session.add_all([self.client_user, self.admin_user])
        db.session.commit()

        # Get client token
        res_client = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'client@example.com', 'password': 'password123'}),
            content_type='application/json'
        )
        self.client_token = json.loads(res_client.data)['token']
        self.client_headers = {'Authorization': f'Bearer {self.client_token}'}

        # Get admin token
        res_admin = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'admin@example.com', 'password': 'password123'}),
            content_type='application/json'
        )
        self.admin_token = json.loads(res_admin.data)['token']
        self.admin_headers = {'Authorization': f'Bearer {self.admin_token}'}