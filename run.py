from app import create_app
from dotenv import load_dotenv

load_dotenv() # Charge les variables d'environnement du fichier .env

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)