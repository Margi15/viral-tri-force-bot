import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes necesarios para subir videos
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

def generate_token():
    """Genera el token de YouTube (ejecutar UNA VEZ localmente)"""

    # Ruta al archivo client_secret que descargaste de Google Cloud Console
    client_secret_file = 'client_secret.json'  # CAMBIA si tu archivo tiene otro nombre

    if not os.path.exists(client_secret_file):
        print(f"ERROR: No se encontro {client_secret_file}")
        print("Descargalo desde: console.cloud.google.com -> APIs -> Credentials -> OAuth 2.0 Client IDs")
        return

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)

    print("Abriendo navegador para autorizar YouTube...")
    credentials = flow.run_local_server(port=0)

    # Guardar las credenciales
    token_data = credentials.to_json()
    with open('youtube_token.json', 'w') as f:
        f.write(token_data)

    print("")
    print("Token generado y guardado en youtube_token.json")
    print("")
    print("SIGUIENTE PASO:")
    print("1. Ve a github.com/Margi15/viral-tri-force-bot/settings/secrets/actions")
    print("2. Crea un secret llamado: YOUTUBE_CLIENT_SECRET")
    print("3. Pega este contenido como valor:")
    print("")
    print("=" * 60)
    print(token_data)
    print("=" * 60)

if __name__ == '__main__':
    generate_token()
