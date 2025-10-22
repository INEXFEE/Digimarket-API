# API REST pour DigiMarket

Cette API REST, développée avec Flask, gère la boutique en ligne DigiMarket. Elle offre la gestion des produits, catégories, commandes et utilisateurs, avec une authentification robuste basée sur les rôles (Client/Administrateur).

## Fonctionnalités

- **Gestion des Utilisateurs** : Inscription, connexion (JWT), et gestion des rôles.
- **Gestion du Catalogue** : CRUD complet pour les produits et les catégories.
- **Gestion des Commandes** : Création de commandes par les clients, consultation et modification de statut par les administrateurs.
- **Sécurité** : Routes protégées par rôles, mots de passe hachés.
- **Architecture Modulaire** : Utilisation des Blueprints Flask pour une organisation claire.

## Prérequis

- Python 3.10+
- pip

## Installation

1.  **Clonez le dépôt :**
    ```bash
    git clone https://github.com/INEXFEE/Digimarket-API # N'oubliez pas de remplacer par l'URL réelle de votre dépôt
    cd DigiMarketAPI
    ```

2.  **Créez et activez un environnement virtuel :**
    ```bash
    # Pour Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Pour macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Installez les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

L'application utilise un fichier `.env` pour gérer les variables de configuration. Créez un fichier `.env` à la racine du projet avec le contenu suivant si vous souhaitez personnaliser les clés secrètes :

```
SECRET_KEY='votre_cle_secrete_flask'
JWT_SECRET_KEY='votre_cle_secrete_jwt'
```

## Utilisation

1.  **Initialisez la base de données :**
    La première fois, vous devez créer la structure de la base de données en appliquant les migrations.
    ```bash
    flask db upgrade
    ```

2.  **Peuplez la base de données avec des données initiales :**
    Cette commande crée un utilisateur administrateur et des catégories par défaut.
    - **Email** : `admin@digimarket.com`
    - **Mot de passe** : `adminpassword`
    ```bash
    flask seed
    ```

3.  **Lancez le serveur de développement :**
    ```bash
    python run.py
    ```
    L'API sera accessible à l'adresse `http://127.0.0.1:5000`.

## Lancer les tests

Pour exécuter la suite de tests unitaires et fonctionnels :
```bash
python -m unittest discover
```

## Documentation de l'API

### Authentification

- `POST /api/auth/register` : Inscription d'un nouvel utilisateur.
- `POST /api/auth/login` : Connexion et récupération d'un token JWT.

### Catégories

- `GET /api/categories/` : Lister toutes les catégories.
- `POST /api/categories/` : Créer une nouvelle catégorie (Admin requis).
- `PUT /api/categories/{id}` : Mettre à jour une catégorie (Admin requis).
- `DELETE /api/categories/{id}` : Supprimer une catégorie (Admin requis).

### Produits

- `GET /api/products/` : Lister tous les produits (avec pagination : `?page=1&per_page=10`).
- `GET /api/products/{id}` : Obtenir les détails d'un produit.
- `POST /api/products/` : Créer un nouveau produit (Admin requis).
- `PUT /api/products/{id}` : Mettre à jour un produit (Admin requis).
- `DELETE /api/products/{id}` : Supprimer un produit (Admin requis).

### Commandes

- `GET /api/orders/` : Lister les commandes (un client voit ses commandes, un admin voit tout).
- `GET /api/orders/{id}` : Obtenir les détails d'une commande.
- `POST /api/orders/` : Créer une nouvelle commande (Client).
- `PATCH /api/orders/{id}` : Mettre à jour le statut d'une commande (Admin requis).