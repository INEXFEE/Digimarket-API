from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Order, OrderItem, Product, User
from ..extensions import db
from ..decorators import admin_required

# Créer le Blueprint pour les commandes
orders_bp = Blueprint('orders', __name__)

def serialize_order(order):
    """Fonction d'aide pour sérialiser un objet Order en dictionnaire."""
    return {
        'id': order.id,
        'user_id': order.user_id,
        'order_date': order.order_date.isoformat(),
        'total_amount': order.total_amount,
        'status': order.status,
        'shipping_address': order.shipping_address,
        'shipping_city': order.shipping_city,
        'shipping_postal_code': order.shipping_postal_code,
        'shipping_country': order.shipping_country,
        'items': [{
            'product_id': item.product_id,
            'quantity': item.quantity,
            'price_at_order': item.price_at_order
        } for item in order.items]
    }

@orders_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    """Récupère toutes les commandes de l'utilisateur actuellement authentifié."""
    # Récupérer l'utilisateur actuel pour vérifier son rôle
    current_user_id_str = get_jwt_identity()
    current_user = db.session.get(User, int(current_user_id_str))
    
    if current_user and current_user.role == 'admin':
        orders = Order.query.all() # Les administrateurs voient toutes les commandes
    else:
        orders = Order.query.filter_by(user_id=int(current_user_id_str)).all() # Les clients voient leurs propres commandes
    return jsonify([serialize_order(order) for order in orders]), 200

@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Récupère une commande spécifique par son ID."""
    current_user_id_str = get_jwt_identity()
    current_user = db.session.get(User, int(current_user_id_str))

    if current_user and current_user.role == 'admin':
        # L'admin peut voir n'importe quelle commande
        order = db.get_or_404(Order, order_id)
    else:
        # Un client ne peut voir que ses propres commandes
        order = Order.query.filter_by(id=order_id, user_id=int(current_user_id_str)).first_or_404()
    
    return jsonify(serialize_order(order)), 200

@orders_bp.route('/', methods=['POST'])
@jwt_required()
def create_order():
    """Crée une nouvelle commande."""
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    required_fields = ['items', 'shipping_address', 'shipping_city', 'shipping_postal_code', 'shipping_country']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": "Données de commande invalides"}), 400

    total_amount = 0
    order_items_to_create = []

    # Extraire les informations d'adresse
    shipping_address = data['shipping_address']
    shipping_city = data['shipping_city']
    shipping_postal_code = data['shipping_postal_code']
    shipping_country = data['shipping_country']

    try:
        for item_data in data['items']:
            product = db.session.get(Product, item_data['product_id'])
            quantity_requested = item_data.get('quantity', 1)
            if not product or product.stock < quantity_requested:
                # Un rollback n'est pas nécessaire ici car aucune modification n'a été faite à la session
                return jsonify({"message": f"Produit {item_data['product_id']} non disponible ou stock insuffisant"}), 400
            
            total_amount += product.price * quantity_requested
            product.stock -= quantity_requested # Décrémenter le stock
            order_items_to_create.append(OrderItem(product_id=product.id, quantity=quantity_requested, price_at_order=product.price))

        new_order = Order(
            user_id=current_user_id, 
            total_amount=total_amount,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_postal_code=shipping_postal_code,
            shipping_country=shipping_country
        )
        new_order.items.extend(order_items_to_create)

        db.session.add(new_order)
        db.session.commit()

        return jsonify({"message": "Commande créée avec succès", "order_id": new_order.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Une erreur est survenue lors de la création de la commande.", "error": str(e)}), 500

@orders_bp.route('/<int:order_id>/lignes', methods=['GET'])
@jwt_required()
def get_order_items(order_id):
    """Consulte les lignes d'une commande spécifique."""
    current_user_id_str = get_jwt_identity()
    current_user = db.session.get(User, int(current_user_id_str))

    if current_user and current_user.role == 'admin':
        order = db.get_or_404(Order, order_id)
    else:
        order = Order.query.filter_by(id=order_id, user_id=int(current_user_id_str)).first_or_404()
    
    items = [{
        'product_id': item.product_id,
        'quantity': item.quantity,
        'price_at_order': item.price_at_order
    } for item in order.items]
    
    return jsonify(items), 200

@orders_bp.route('/<int:order_id>', methods=['PATCH'])
@admin_required()
def update_order_status(order_id):
    """Met à jour le statut d'une commande (Admin uniquement)."""
    order = db.get_or_404(Order, order_id)
    data = request.get_json()

    if not data or 'status' not in data:
        return jsonify({"message": "Le statut est requis"}), 400

    new_status = data['status']
    allowed_statuses = ['pending', 'validated', 'shipped', 'cancelled']

    if new_status not in allowed_statuses:
        return jsonify({"message": f"Statut invalide. Les statuts autorisés sont : {', '.join(allowed_statuses)}"}), 400

    # Si la commande est annulée, réintégrer le stock
    if new_status == 'cancelled' and order.status != 'cancelled':
        for item in order.items:
            product = db.session.get(Product, item.product_id)
            if product:
                product.stock += item.quantity

    order.status = new_status
    db.session.commit()

    return jsonify(serialize_order(order)), 200
