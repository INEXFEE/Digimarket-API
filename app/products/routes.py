from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from ..models import Product, Category
from ..extensions import db
from ..decorators import admin_required

# Créer le Blueprint pour les produits
products_bp = Blueprint('products', __name__)

# --- Routes Publiques ---

@products_bp.route('/', methods=['GET'])
def get_products():
    """Récupère la liste de tous les produits."""
    # Base de la requête
    query = Product.query

    # Filtre de recherche par nom (paramètre 'q')
    search_term = request.args.get('q')
    if search_term:
        query = query.filter(Product.name.ilike(f'%{search_term}%'))

    # Filtre par catégorie (paramètre 'category_id')
    category_id = request.args.get('category_id', type=int)
    if category_id:
        query = query.filter(Product.category_id == category_id)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    return jsonify({
        "products": [{
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "category_id": product.category_id,
            "category_name": product.category.name,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        } for product in products],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "next_page": pagination.next_num,
        "prev_page": pagination.prev_num
    }), 200

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Récupère un produit spécifique par son ID."""
    product = db.get_or_404(Product, product_id)
    return jsonify({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock,
        "category_id": product.category_id,
        "category_name": product.category.name,
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }), 200

# --- Routes Protégées (Admin/Vendeur) ---

@products_bp.route('/', methods=['POST'])
@admin_required()
def create_product():
    """Crée un nouveau produit."""
    data = request.get_json()
    required_fields = ['name', 'price', 'stock', 'category_id']
    if not data or not all(key in data for key in required_fields):
        return jsonify({"message": f"Données manquantes ou invalides. Champs requis: {', '.join(required_fields)}"}), 400
    
    category_id = data['category_id']
    if not db.session.get(Category, category_id):
        return jsonify({"message": f"La catégorie avec l'ID {category_id} n'existe pas"}), 404
    
    new_product = Product(
        name=data['name'],
        description=data.get('description'),
        price=data['price'],
        stock=data['stock'],
        category_id=category_id
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({
        "id": new_product.id,
        "name": new_product.name,
        "description": new_product.description,
        "price": new_product.price,
        "stock": new_product.stock,
        "category_id": new_product.category_id,
        "category_name": new_product.category.name,
        "created_at": new_product.created_at,
        "updated_at": new_product.updated_at
    }), 201

@products_bp.route('/<int:product_id>', methods=['PUT'])
@admin_required()
def update_product(product_id):
    """Met à jour un produit existant."""
    product = db.get_or_404(Product, product_id)
    
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)
    product.stock = data.get('stock', product.stock)

    if 'category_id' in data:
        category_id = data['category_id']
        if not db.session.get(Category, category_id):
            return jsonify({"message": f"La catégorie avec l'ID {category_id} n'existe pas"}), 404
        product.category_id = category_id

    db.session.commit()
    return jsonify({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "stock": product.stock,
        "category_id": product.category_id,
        "category_name": product.category.name,
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }), 200

@products_bp.route('/<int:product_id>', methods=['DELETE'])
@admin_required()
def delete_product(product_id):
    """Supprime un produit."""
    product = db.get_or_404(Product, product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Produit supprimé avec succès"}), 200