from .extensions import db, bcrypt
from datetime import datetime, timezone

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Increased length for bcrypt hash
    role = db.Column(db.String(50), nullable=False, default='client') # 'client' or 'admin'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relation
    orders = db.relationship('Order', back_populates='user', cascade="all, delete-orphan")

    def __init__(self, email, password, role='client'):
        self.email = email
        # La magie opère ici : assigner à .password déclenche le @password.setter
        self.password = password
        self.role = role

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relations
    category = db.relationship('Category', back_populates='products')
    order_items = db.relationship('OrderItem', back_populates='product')

    def __repr__(self):
        return f'<Product {self.name}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Relation
    products = db.relationship('Product', back_populates='category')

    def __repr__(self):
        return f'<Category {self.name}>'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending') # e.g., pending, completed, cancelled

    shipping_address = db.Column(db.String(255), nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_postal_code = db.Column(db.String(20), nullable=False)
    shipping_country = db.Column(db.String(100), nullable=False)

    # Relations
    user = db.relationship('User', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Order {self.id} by User {self.user_id}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_order = db.Column(db.Float, nullable=False) # Price at the time of order

    # Relations
    order = db.relationship('Order', back_populates='items')
    product = db.relationship('Product', back_populates='order_items')

    def __repr__(self):
        return f'<OrderItem {self.id} Order {self.order_id} Product {self.product_id}>'
