from flask import Blueprint, jsonify, request
from ..models import Category
from ..extensions import db
from ..decorators import admin_required

categories_bp = Blueprint('categories', __name__)

# --- Routes Publiques ---

@categories_bp.route('/', methods=['GET'])
def get_categories():
    """Récupère la liste de toutes les catégories."""
    categories = Category.query.all()
    return jsonify([
        {
            "id": category.id,
            "name": category.name,
            "description": category.description
        } for category in categories
    ]), 200

@categories_bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Récupère une catégorie spécifique par son ID."""
    category = db.get_or_404(Category, category_id)
    return jsonify({
        "id": category.id,
        "name": category.name,
        "description": category.description
    }), 200

# --- Routes Protégées (Admin) ---

@categories_bp.route('/', methods=['POST'])
@admin_required()
def create_category():
    """Crée une nouvelle catégorie."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"message": "Le nom de la catégorie est requis"}), 400
    
    if Category.query.filter_by(name=data['name']).first():
        return jsonify({"message": "Cette catégorie existe déjà"}), 409

    new_category = Category(name=data['name'], description=data.get('description'))
    db.session.add(new_category)
    db.session.commit()
    return jsonify({"id": new_category.id, "name": new_category.name, "description": new_category.description}), 201

@categories_bp.route('/<int:category_id>', methods=['PUT'])
@admin_required()
def update_category(category_id):
    """Met à jour une catégorie existante."""
    category = db.get_or_404(Category, category_id)
    data = request.get_json()
    category.name = data.get('name', category.name)
    category.description = data.get('description', category.description)
    db.session.commit()
    return jsonify({"id": category.id, "name": category.name, "description": category.description}), 200

@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@admin_required()
def delete_category(category_id):
    """Supprime une catégorie."""
    category = db.get_or_404(Category, category_id)
    db.session.delete(category)
    db.session.commit()
    return jsonify({"message": "Catégorie supprimée avec succès"}), 200