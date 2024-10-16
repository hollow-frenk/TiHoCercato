from flask import Flask, request, session, redirect, url_for
import os
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from twilio.twiml.voice_response import VoiceResponse
import mysql.connector
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)
app.secret_key = 'SOME_SECRET_KEY'

SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']
CREDENTIALS_FILE = 'credentials.json'

TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'YOUR_TELEGRAM_CHAT_ID'
TWILIO_NUMBER = 'YOUR_TWILIO_PHONE_NUMBER'

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def get_db_connection():
    """Crea una connessione a MariaDB."""
    return mysql.connector.connect(
        host="localhost",
        user="your_db_user",
        password="your_db_password",
        database="telegram_bot"
    )

def google_login():
    """Effettua il login a Google per ottenere le credenziali."""
    if 'credentials' in session:
        credentials = Credentials(**session['credentials'])
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        credentials = flow.run_local_server(port=0)

        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
    return credentials


def get_contact_name(phone_number):
    """Verifica se il numero chiamante è presente nei contatti di Google."""
    credentials = google_login()
    service = build('people', 'v1', credentials=credentials)

    results = service.people().connections().list(
        resourceName='people/me',
        pageSize=1000,  # Ottieni fino a 1000 contatti
        personFields='names,phoneNumbers'
    ).execute()

    connections = results.get('connections', [])

    for person in connections:
        phone_numbers = person.get('phoneNumbers', [])
        for number in phone_numbers:
            if phone_number in number.get('value'):
                return person.get('names', [])[0].get('displayName')

    return None


def save_user_name(chat_id, name):
    """Salva il nome dell'utente nel database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO users (chat_id, name) VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE name = VALUES(name)
    ''', (chat_id, name))

    conn.commit()
    cursor.close()
    conn.close()


def save_user_phone(chat_id, phone_number):
    """Salva il numero di telefono dell'utente nel database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE users SET phone_number = %s WHERE chat_id = %s
    ''', (phone_number, chat_id))

    conn.commit()
    cursor.close()
    conn.close()


def get_user(identifier, is_phone=False):
    """Recupera i dettagli dell'utente dal database utilizzando chat_id o numero di telefono."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if is_phone:
        cursor.execute('SELECT chat_id, name FROM users WHERE phone_number = %s', (identifier,))
    else:
        cursor.execute('SELECT name, phone_number FROM users WHERE chat_id = %s', (identifier,))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user, """Restituisce una 'tuple' (name, phone_number) o None"""


def save_voice_message(chat_id, voice_url, message_id):
    """Salva il messaggio vocale nel database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO voice_messages (chat_id, voice_url, message_id) VALUES (%s, %s, %s)
    ''', (chat_id, voice_url, message_id))

    conn.commit()
    cursor.close()
    conn.close()


def send_telegram_message_with_audio(chat_id, message, audio_url):
    """Invia un messaggio e allega un file audio su Telegram."""

    # Invia il messaggio testuale su Telegram
    bot.send_message(chat_id=chat_id, text=message)

    # Invia il file audio su Telegram
    bot.send_audio(chat_id=chat_id, audio=audio_url)



@app.route("/incoming_call", methods=['POST'])
def incoming_call():
    """Gestisce le chiamate in arrivo da Twilio."""
    from_number = request.form['From']
    to_number = request.form['To']

    contact_name = get_contact_name(from_number)
    user = get_user(to_number, is_phone=True),  """Funzione che ottiene l'utente dal numero di telefono"""

    if user:
        chat_id = user[0]
        user_name = user[1]
        if contact_name:
            message = f"Ciao {user_name}, hai una chiamata persa da {contact_name} (numero {from_number})."
        else:
            message = f"Ciao {user_name}, hai una chiamata persa da {from_number}."

            """Avvisa l'utente"""
            bot.send_message(chat_id=chat_id, text=message)

    response = VoiceResponse()
    response.say("Non puoi rispondere al telefono. Puoi lasciare un messaggio dopo il segnale.")
    response.record(
        maxLength=120,  # Durata massima della registrazione in secondi
        action="/handle_recording",  # URL per gestire la registrazione completata
        recordingStatusCallback="/recording_complete"
    )
    return str(response)

    return "OK", 200

@app.route("/handle_recording", methods=['POST'])
def handle_recording():
    """Gestisce il termine della registrazione e invia la notifica su Telegram."""
    from_number = request.form['From']
    recording_url = request.form['RecordingUrl']

    contact_name = get_contact_name(from_number)
    user = get_user(from_number, is_phone=True),  """Funzione che ottiene l'utente dal numero di telefono"""

    if user:
        chat_id = user[0]
        user_name = user[1]
        if contact_name:
            message = f"Ciao {user_name}, hai una chiamata persa da {contact_name} con un messaggio vocale allegato."
        else:
            message = f"Ciao {user_name}, hai una chiamata persa da {from_number} con un messaggio vocale allegato."

        sent_message = bot.send_message(chat_id=chat_id, text=message)
        send_telegram_message_with_audio(chat_id, message, recording_url)

        # Salva il messaggio vocale nel database
        save_voice_message(chat_id, recording_url, sent_message.message_id)

    return "OK", 200

@app.route("/delete_message", methods=['POST'])
def handle_deleted_message(update: Update, context: CallbackContext):
    """Gestisce la cancellazione del messaggio vocale su Telegram e nel database."""
    message_id = update.message.message_id
    chat_id = update.message.chat_id

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    DELETE FROM voice_messages WHERE message_id = %s AND chat_id = %s
    ''', (message_id, chat_id))

    conn.commit()
    cursor.close()
    conn.close()

    return "OK", 200

@app.route('/login')
def login():
    """Inizia il processo di login con Google."""
    google_login()
    return 'Login completato con successo!'


if __name__ == "__main__":
    app.run(debug=True, port=5000)