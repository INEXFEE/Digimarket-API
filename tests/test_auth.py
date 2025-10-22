import unittest
import json
from app.extensions import db
from app.models import User
from .base import BaseTestCase

class AuthTestCase(BaseTestCase):
    """Cette classe teste les fonctionnalités d'authentification."""

    # Le setUp et le tearDown sont maintenant hérités de BaseTestCase

    def test_register_user(self):
        """Teste l'inscription d'un nouvel utilisateur."""
        res = self.client.post(
            '/api/auth/register',
            data=json.dumps({'email': 'test@example.com', 'password': 'password123'}),
            content_type='application/json'
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(data['message'], 'Nouvel utilisateur créé avec succès')

    def test_register_existing_user(self):
        """Teste l'inscription avec un email déjà existant."""
        # Crée un premier utilisateur directement dans la base de données
        user = User(email='test@example.com', password='password123')
        db.session.add(user)
        db.session.commit()

        # Tente de créer le même utilisateur à nouveau
        res = self.client.post(
            '/api/auth/register',
            data=json.dumps({'email': 'test@example.com', 'password': 'password123'}),
            content_type='application/json'
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 409)
        self.assertEqual(data['message'], 'Cet utilisateur existe déjà. Veuillez vous connecter.')

    def test_login_user(self):
        """Teste la connexion d'un utilisateur et la réception d'un token JWT."""
        # Crée un utilisateur pour le test directement dans la base de données
        user = User(email='test@example.com', password='password123')
        db.session.add(user)
        db.session.commit()
        
        res = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'test@example.com', 'password': 'password123'}),
            content_type='application/json'
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertIn('token', data)
        self.assertIsInstance(data['token'], str)

    def test_login_user_wrong_password(self):
        """Teste la connexion d'un utilisateur avec un mot de passe incorrect."""
        # Crée un utilisateur pour le test
        user = User(email='test@example.com', password='password123')
        db.session.add(user)
        db.session.commit()

        res = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'test@example.com', 'password': 'wrongpassword'}),
            content_type='application/json'
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(data['message'], 'Email ou mot de passe incorrect')

if __name__ == '__main__':
    unittest.main()