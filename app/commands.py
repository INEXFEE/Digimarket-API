import click
from flask.cli import with_appcontext
from .extensions import db
from .models import User, Category

@click.command(name='seed')
@with_appcontext
def seed():
    """Initialise la base de données avec des données de test."""
    
    # Vérifie si l'utilisateur admin existe déjà
    if User.query.filter_by(email='admin@digimarket.com').first():
        print('L\'utilisateur admin existe déjà. Aucune action effectuée pour les utilisateurs.')
    else:
        admin_user = User(email='admin@digimarket.com', password='adminpassword', role='admin')
        db.session.add(admin_user)
        print('Utilisateur admin créé.')

    # Vérifie si les catégories existent déjà
    if Category.query.first():
        print('Les catégories existent déjà. Aucune action effectuée pour les catégories.')
    else:
        categories = [
            Category(name='Ordinateurs Portables', description='Des PC portables pour tous les usages.'),
            Category(name='Périphériques', description='Claviers, souris, et autres accessoires.'),
            Category(name='Moniteurs', description='Écrans de toutes tailles et résolutions.'),
            Category(name='Composants', description='Processeurs, cartes graphiques, mémoire, etc.')
        ]
        db.session.bulk_save_objects(categories)
        print(f'{len(categories)} catégories créées.')

    db.session.commit()
    print('Initialisation de la base de données terminée.')