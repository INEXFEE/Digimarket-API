import unittest
import json
from app import create_app
from app.extensions import db
from app.models import User, Product, Order, OrderItem, Category
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    BCRYPT_LOG_ROUNDS = 4
    JWT_SECRET_KEY = 'test-jwt-secret-key' # Explicitly set for tests

class OrdersTestCase(unittest.TestCase):
    """Cette classe teste les endpoints liés aux commandes."""

    def setUp(self):
        """Configuration initiale pour chaque test."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()
        self._setup_users_and_tokens()
        self._create_test_categories()
        self._create_test_products()

    def tearDown(self):
        """Nettoyage après chaque test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _setup_users_and_tokens(self):
        """Crée un utilisateur client et un utilisateur admin, et leurs tokens."""
        # Client user
        self.client_user = User(email='client@example.com', password='password123', role='client')
        # Admin user
        self.admin_user = User(email='admin@example.com', password='password123', role='admin')
        db.session.add_all([self.client_user, self.admin_user])
        db.session.commit()

        # Get client token
        res_client = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'client@example.com', 'password': 'password123'}),
            content_type='application/json'
        )
        client_token = json.loads(res_client.data)['token']
        self.client_headers = {'Authorization': f'Bearer {client_token}'}
        self.client_user_id = self.client_user.id

        # Get admin token
        res_admin = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'admin@example.com', 'password': 'password123'}),
            content_type='application/json'
        )
        admin_token = json.loads(res_admin.data)['token']
        self.admin_headers = {'Authorization': f'Bearer {admin_token}'}

    def _create_test_categories(self):
        """Méthode d'aide pour créer des catégories de test."""
        self.category1 = Category(name='Laptops')
        self.category2 = Category(name='Périphériques')
        db.session.add_all([self.category1, self.category2])
        db.session.commit()

    def _create_test_products(self):
        """Méthode d'aide pour créer des produits de test."""
        self.product1 = Product(name='Laptop Pro', price=1200.00, stock=50, category_id=self.category1.id)
        self.product2 = Product(name='Souris Gamer', price=75.50, stock=200, category_id=self.category2.id)
        db.session.add_all([self.product1, self.product2])
        db.session.commit()

    # --- Tests des routes protégées ---

    def test_create_order_success(self):
        """Teste la création d'une commande avec succès."""
        order_data = {
            'items': [
                {'product_id': self.product1.id, 'quantity': 2},
                {'product_id': self.product2.id, 'quantity': 1}
            ]
        }
        res = self.client.post(
            '/api/orders/',
            data=json.dumps(order_data),
            headers=self.client_headers,
            content_type='application/json'
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(data['message'], 'Commande créée avec succès')
        self.assertIn('order_id', data)

        # Vérifier que le stock a été mis à jour
        self.assertEqual(db.session.get(Product, self.product1.id).stock, 48)
        self.assertEqual(db.session.get(Product, self.product2.id).stock, 199)
        # Vérifier que la commande et les OrderItems ont été créés
        self.assertEqual(Order.query.count(), 1)
        self.assertEqual(OrderItem.query.count(), 2)

    def test_create_order_no_token(self):
        """Teste la création d'une commande sans token d'authentification."""
        order_data = {'items': [{'product_id': self.product1.id, 'quantity': 1}]}
        res = self.client.post(
            '/api/orders/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 401) # 401 Unauthorized

    def test_create_order_insufficient_stock(self):
        """Teste la création d'une commande avec un stock insuffisant."""
        order_data = {'items': [{'product_id': self.product1.id, 'quantity': 100}]} # Stock est 50
        res = self.client.post(
            '/api/orders/',
            data=json.dumps(order_data),
            headers=self.client_headers,
            content_type='application/json'
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertIn('stock insuffisant', data['message'])
        # Vérifier que le stock n'a pas changé
        self.assertEqual(db.session.get(Product, self.product1.id).stock, 50)

    def test_get_orders_as_client(self):
        """Teste qu'un client ne voit que ses propres commandes."""
        # Crée une commande et un OrderItem directement dans la DB pour ce test
        order = Order(user_id=self.client_user_id, total_amount=1275.50)
        item1 = OrderItem(order=order, product_id=self.product1.id, quantity=1, price_at_order=self.product1.price)
        db.session.add_all([order, item1])
        db.session.commit()
        
        res = self.client.get('/api/orders/', headers=self.client_headers)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['user_id'], self.client_user_id)

    def test_get_orders_as_admin(self):
        """Teste qu'un admin voit toutes les commandes."""
        # Crée une commande pour le client
        order1 = Order(user_id=self.client_user_id, total_amount=100)
        # Crée une commande pour l'admin
        order2 = Order(user_id=self.admin_user.id, total_amount=200)
        db.session.add_all([order1, order2])
        db.session.commit()

        res = self.client.get('/api/orders/', headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(json.loads(res.data)), 2)

    def test_get_single_order(self):
        """Teste la récupération d'une commande spécifique par ID."""
        # Crée une commande et des OrderItems directement dans la DB pour ce test
        order = Order(user_id=self.client_user_id, total_amount=1200.00)
        item1 = OrderItem(order=order, product_id=self.product1.id, quantity=1, price_at_order=self.product1.price)
        item2 = OrderItem(order=order, product_id=self.product2.id, quantity=1, price_at_order=self.product2.price)
        db.session.add_all([order, item1, item2])
        db.session.commit()
        order_id = order.id
        res = self.client.get(f'/api/orders/{order_id}', headers=self.client_headers)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['id'], order_id)
        self.assertEqual(data['user_id'], self.client_user_id)
        self.assertEqual(len(data['items']), 2)

    def test_get_non_existent_order(self):
        """Teste la récupération d'une commande qui n'existe pas."""
        res = self.client.get('/api/orders/999', headers=self.client_headers) # Pas de / final ici car c'est un ID
        self.assertEqual(res.status_code, 404)

    def test_get_other_user_order(self):
        """Teste qu'un utilisateur ne peut pas voir la commande d'un autre utilisateur."""
        # Créer un deuxième utilisateur
        user2 = User(email='other@example.com', password='password123')
        db.session.add(user2)
        db.session.commit()
        # Créer une commande pour le deuxième utilisateur
        order_other_user = Order(user_id=user2.id, total_amount=10.0)
        db.session.add(order_other_user)
        db.session.commit()

        # Tenter de récupérer la commande de l'autre utilisateur avec le token du client
        res = self.client.get(f'/api/orders/{order_other_user.id}', headers=self.client_headers)
        self.assertEqual(res.status_code, 404) # Doit être 404 car non trouvée pour cet utilisateur

    def test_update_order_status_as_admin(self):
        """Teste la mise à jour du statut d'une commande par un admin."""
        order = Order(user_id=self.client_user_id, total_amount=100)
        db.session.add(order)
        db.session.commit()

        res = self.client.patch(
            f'/api/orders/{order.id}',
            data=json.dumps({'status': 'shipped'}),
            headers=self.admin_headers,
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data)['status'], 'shipped')
        self.assertEqual(db.session.get(Order, order.id).status, 'shipped')

    def test_update_order_status_as_client(self):
        """Teste qu'un client ne peut pas mettre à jour le statut d'une commande."""
        order = Order(user_id=self.client_user_id, total_amount=100)
        db.session.add(order)
        db.session.commit()

        res = self.client.patch(
            f'/api/orders/{order.id}',
            data=json.dumps({'status': 'shipped'}),
            headers=self.client_headers,
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 403) # Forbidden

if __name__ == '__main__':
    unittest.main()