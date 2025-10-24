# Utiliser une image Python officielle légère
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les dépendances et les installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'application
COPY app.py .

# Exposer le port sur lequel Flask tourne
EXPOSE 5000

# Commande pour démarrer l'application (généralement via Gunicorn/Waitress pour la production, mais Flask standard pour le test)
CMD ["python", "app.py"] 
# Pour la production, remplacer par : CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
