import unittest
import json
from app import create_app
from app.extensions import db
from app.models import User, Product, Category
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    BCRYPT_LOG_ROUNDS = 4
    JWT_SECRET_KEY = 'test-jwt-secret-key' # Explicitly set for tests

class ProductsTestCase(unittest.TestCase):
    """Cette classe teste les endpoints liés aux produits."""

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
        client_user = User(email='client@example.com', password='password123', role='client')
        # Admin user
        admin_user = User(email='admin@example.com', password='password123', role='admin')
        db.session.add_all([client_user, admin_user])
        db.session.commit()

        # Get client token
        res_client = self.client.post(
            '/api/auth/login',
            data=json.dumps({'email': 'client@example.com', 'password': 'password123'}),
            content_type='application/json'
        )
        client_token = json.loads(res_client.data)['token']
        self.client_headers = {'Authorization': f'Bearer {client_token}'}

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
        self.category1 = Category(name='Laptops', description='Ordinateurs portables')
        self.category2 = Category(name='Périphériques', description='Souris, claviers, etc.')
        db.session.add_all([self.category1, self.category2])
        db.session.commit()

    def _create_test_products(self):
        """Méthode d'aide pour créer des produits de test."""
        product1 = Product(name='Laptop Pro', price=1200.00, stock=50, category_id=self.category1.id)
        product2 = Product(name='Souris Gamer', price=75.50, stock=200, category_id=self.category2.id)
        db.session.add_all([product1, product2])
        db.session.commit()

    # --- Tests des routes publiques ---

    def test_get_all_products(self):
        """Teste la récupération de tous les produits (route publique)."""
        res = self.client.get('/api/products/?per_page=5')
        data = json.loads(res.data)['products']
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], 'Laptop Pro')

    def test_get_single_product(self):
        """Teste la récupération d'un seul produit par son ID (route publique)."""
        res = self.client.get('/api/products/1')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['name'], 'Laptop Pro')
        self.assertEqual(data['category_name'], 'Laptops')

    def test_get_non_existent_product(self):
        """Teste la récupération d'un produit qui n'existe pas."""
        res = self.client.get('/api/products/999')
        self.assertEqual(res.status_code, 404)

    # --- Tests des routes protégées ---

    def test_search_product_by_name(self):
        """Teste la recherche de produits par nom."""
        # Nous avons 'Laptop Pro' et 'Souris Gamer'
        res = self.client.get('/api/products/?q=Laptop')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(data['products']), 1)
        self.assertEqual(data['products'][0]['name'], 'Laptop Pro')

    def test_search_product_no_results(self):
        """Teste une recherche de produit qui ne retourne aucun résultat."""
        res = self.client.get('/api/products/?q=NonExistent')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(data['products']), 0)
        self.assertEqual(data['total'], 0)

    def test_filter_product_by_category(self):
        """Teste le filtrage des produits par catégorie."""
        res = self.client.get(f'/api/products/?category_id={self.category2.id}')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(data['products']), 1)
        self.assertEqual(data['products'][0]['name'], 'Souris Gamer')

    def test_create_product_as_admin(self):
        """Teste la création d'un produit par un admin."""
        product_data = {'name': 'Nouveau Clavier', 'price': 99.99, 'stock': 100, 'category_id': self.category2.id}
        res = self.client.post(
            '/api/products/',
            data=json.dumps(product_data),
            headers=self.admin_headers,
            content_type='application/json'
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(data['name'], 'Nouveau Clavier')
        self.assertEqual(data['category_id'], self.category2.id)
        self.assertEqual(Product.query.count(), 3)

    def test_create_product_with_non_existent_category(self):
        """Teste la création d'un produit avec une catégorie qui n'existe pas."""
        product_data = {'name': 'Produit Orphelin', 'price': 10.0, 'stock': 10, 'category_id': 999}
        res = self.client.post(
            '/api/products/',
            data=json.dumps(product_data),
            headers=self.admin_headers,
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 404)

    def test_create_product_as_client(self):
        """Teste qu'un client ne peut pas créer de produit."""
        product_data = {'name': 'Produit non autorisé', 'price': 10.0, 'stock': 10, 'category_id': self.category1.id}
        res = self.client.post(
            '/api/products/',
            data=json.dumps(product_data),
            headers=self.client_headers,
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 403) # 403 Forbidden

    def test_create_product_no_token(self):
        """Teste la création d'un produit sans token d'authentification."""
        product_data = {'name': 'Produit non autorisé', 'price': 10.0, 'stock': 10, 'category_id': self.category1.id}
        res = self.client.post(
            '/api/products/',
            data=json.dumps(product_data),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 401) # 401 Unauthorized

    def test_update_product_as_admin(self):
        """Teste la mise à jour d'un produit par un admin."""
        update_data = {'price': 1150.00, 'stock': 45, 'category_id': self.category2.id}
        res = self.client.put(
            '/api/products/1',
            data=json.dumps(update_data),
            headers=self.admin_headers,
            content_type='application/json'
        )
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['price'], 1150.00)
        self.assertEqual(db.session.get(Product, 1).stock, 45)
        self.assertEqual(db.session.get(Product, 1).category_id, self.category2.id)

    def test_delete_product_as_admin(self):
        """Teste la suppression d'un produit par un admin."""
        res = self.client.delete('/api/products/1', headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.data)['message'], 'Produit supprimé avec succès')
        self.assertIsNone(db.session.get(Product, 1))
        self.assertEqual(Product.query.count(), 1)

if __name__ == '__main__':
    unittest.main()