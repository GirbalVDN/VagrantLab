import json
import os
import csv
from io import StringIO
from flask import Flask, request, jsonify, send_file
from flask_restx import Api, Resource, fields

# --- Configuration et Initialisation ---

# Nom du fichier pour le stockage des données
DATA_FILE = 'hardware_readiness_data.json'

def load_data():
    """Charge les données existantes à partir du fichier JSON."""
    if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                # Le fichier stocke un dictionnaire { "Name": { ...data... } }
                return json.load(f)
            except json.JSONDecodeError:
                # Erreur si le fichier est corrompu ou vide mais existe
                return {}
    return {}

def save_data(data):
    """Sauvegarde toutes les données dans le fichier JSON."""
    # S'assure que le répertoire existe (important en K8s)
    os.makedirs(os.path.dirname(DATA_FILE) or '.', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# Initialisation de l'application Flask
app = Flask(__name__)
# Initialisation de l'API Flask-RESTx
api = Api(app, 
          version='1.0', 
          title='Windows 11 Readiness API', 
          description='API pour collecter et consulter les données de compatibilité Windows 11.',
          # L'endpoint Swagger UI sera accessible à /
          doc='/') 

# Création d'un namespace pour notre ressource
ns = api.namespace('record', description='Opérations de collecte et consultation')

# Modèle pour la donnée d'entrée (POST) - Pour la documentation Swagger
post_data_model = api.model('HardwareData', {
    'returnCode': fields.Integer(required=True, description='Code de retour du script (0 = OK).'),
    'returnReason': fields.String(required=False, description="Raison de l'échec ou information supplémentaire."),
    'logging': fields.String(required=True, description='Logs détaillés de la vérification des composants (CPU, TPM, RAM, etc.).'),
    'returnResult': fields.String(required=True, description='Résultat final de la compatibilité (CAPABLE/NOT_CAPABLE).'),
})

# Modèle pour la requête POST complète
post_request_model = api.model('PostRecord', {
    'Name': fields.String(required=True, description='Nom du poste informatique (ex: MI4542).', example='MI4542'),
    'Data': fields.Nested(post_data_model, required=True, description='Données JSON de compatibilité.'),
})

# --- Endpoint /record ---

@ns.route('/')
class RecordList(Resource):
    
    @ns.doc('post_hardware_data')
    @ns.expect(post_request_model, validate=True)
    @ns.response(201, 'Données enregistrées avec succès.')
    @ns.response(400, 'Format de requête invalide.')
    def post(self):
        """
        Enregistre les données de compatibilité d'un poste.
        """
        try:
            # Les données sont validées par Flask-RESTx grâce à @ns.expect
            payload = request.json 
            post_name = payload.get('Name').upper() # Standardiser le nom en majuscule
            post_data = payload.get('Data')

            if not post_name or not post_data:
                 api.abort(400, "Les champs 'Name' et 'Data' sont requis.")

            # Charger les données existantes, ajouter/mettre à jour, et sauvegarder
            all_data = load_data()
            all_data[post_name] = post_data
            save_data(all_data)

            return {'message': f"Données pour le poste {post_name} enregistrées."}, 201

        except Exception as e:
            # Gestion des erreurs génériques (ex: problème de disque)
            api.abort(500, f"Erreur interne lors de l'enregistrement des données: {str(e)}")


    @ns.doc('get_hardware_data')
    @ns.param('Name', 'Nom du poste à rechercher (optionnel). Si absent, renvoie toutes les données au format CSV.', required=False)
    @ns.response(200, 'Données(s) retournée(s) avec succès.')
    @ns.response(404, 'Poste non trouvé.')
    def get(self):
        """
        Renvoie les données d'un poste spécifique (JSON) ou l'ensemble des données (CSV).
        """
        all_data = load_data()
        post_name = request.args.get('Name')

        if post_name:
            # Requête avec "Name": retourner les données du poste en JSON
            post_name = post_name.upper()
            if post_name in all_data:
                return jsonify(all_data[post_name])
            else:
                api.abort(404, f"Poste '{post_name}' non trouvé.")
        
        else:
            # Requête sans "Name": retourner toutes les données en CSV
            if not all_data:
                return {'message': 'Aucune donnée enregistrée à exporter.'}, 200

            # Préparation du fichier CSV en mémoire
            si = StringIO()
            cw = csv.writer(si)
            
            # Déterminer les clés d'entête (basé sur la première entrée)
            first_key = next(iter(all_data))
            data_keys = list(all_data[first_key].keys())
            header = ['Name'] + data_keys
            cw.writerow(header)

            # Écrire les lignes de données
            for name, data in all_data.items():
                row = [name] + [str(data.get(k, 'N/A')) for k in data_keys]
                cw.writerow(row)

            # --- DÉBUT DE LA CORRECTION ---
            
            # 1. Obtenir la chaîne de caractères du CSV
            output = si.getvalue()
            
            # 2. Importer BytesIO pour la gestion binaire
            from io import BytesIO
            
            # 3. Encoder la chaîne CSV en UTF-8 et la placer dans un flux binaire (BytesIO)
            binary_output = BytesIO(output.encode('utf-8'))
            
            # Renvoyer le fichier CSV
            return send_file(
                # Utilisation de BytesIO à la place de StringIO
                binary_output, 
                mimetype='text/csv',
                as_attachment=True,
                download_name='windows_11_readiness_export.csv'
            )
            # --- FIN DE LA CORRECTION ---

# --- Exécution ---

if __name__ == '__main__':
    # Le port standard pour les applications web
    app.run(host='0.0.0.0', port=5000)
