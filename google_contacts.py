import json
import db  # Modulo per l'interazione con il database
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Scopes: specifica i permessi richiesti (accesso ai contatti in questo caso)
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']

# Path al file di credenziali scaricato da Google Cloud Console
CREDENTIALS_FILE = 'path/to/credentials.json'  # Assicurati di mettere il path corretto


# Funzione per autenticare l'utente e salvare i token nel database
def authenticate_user(user_id):
    # Recupera i token dell'utente dal database
    user_token_data = db.get_user_google_token(user_id)

    if user_token_data:
        # Crea le credenziali dall'informazione salvata nel DB
        creds = Credentials(
            token=user_token_data['access_token'],
            refresh_token=user_token_data['refresh_token'],
            token_uri=user_token_data['token_uri'],
            client_id=user_token_data['client_id'],
            client_secret=user_token_data['client_secret'],
            scopes=json.loads(user_token_data['scopes'])
        )

        # Se il token è scaduto, aggiornarlo
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Aggiorna il token di accesso e la scadenza nel database
            db.update_user_google_token(user_id, creds.token, creds.expiry)
    else:
        # Avvia il flusso OAuth 2.0 se non ci sono credenziali nel database
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

        # Salva i token nel database
        db.save_user_google_token(
            user_id=user_id,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_uri=creds.token_uri,
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            scopes=json.dumps(creds.scopes),
            expiry=creds.expiry
        )

    return creds


# Funzione per ottenere il servizio Google People API autenticato
def get_google_service(user_id):
    # Autentica l'utente e ottieni le credenziali
    creds = authenticate_user(user_id)
    # Crea il servizio Google People API autenticato
    service = build('people', 'v1', credentials=creds)
    return service


# Funzione per controllare se il numero è presente nei contatti di Google
def get_contact_name(user_id, phone_number):
    # Ottieni il servizio Google People API per l'utente
    service = get_google_service(user_id)

    # Richiedi la lista dei contatti
    results = service.people().connections().list(
        resourceName='people/me',
        personFields='names,phoneNumbers'
    ).execute()

    # Itera attraverso i contatti per trovare il numero di telefono
    connections = results.get('connections', [])
    for person in connections:
        phone_numbers = person.get('phoneNumbers', [])
        for number in phone_numbers:
            if number.get('value') == phone_number:
                # Se il numero corrisponde, restituisci il nome del contatto
                return person['names'][0]['displayName']
    # Se il numero non è trovato, restituisci None
    return None