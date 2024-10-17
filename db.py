import mysql.connector
import datetime

# Configurazione del database
db_config = {
    'user': 'your_db_user',
    'password': 'your_db_password',
    'host': 'your_db_host',
    'database': 'your_db_name',
}

# Funzione per connettersi al database
def get_connection():
    return mysql.connector.connect(**db_config)

# --------------- Gestione utenti ---------------

# Salva il nome dell'utente
def save_user_name(chat_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (chat_id, name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE name=%s", (chat_id, name, name))
    conn.commit()
    cursor.close()
    conn.close()

# Salva il numero di telefono dell'utente
def save_user_phone(chat_id, phone_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone_number = %s WHERE chat_id = %s", (phone_number, chat_id))
    conn.commit()
    cursor.close()
    conn.close()

# Recupera i dati dell'utente
def get_user_data(chat_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# Trova l'utente in base al numero di telefono
def find_user_by_phone(phone_number):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT chat_id FROM users WHERE phone_number = %s", (phone_number,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user['chat_id'] if user else None

# --------------- Gestione messaggi vocali ---------------

# Salva un messaggio vocale
def save_voicemail(user_id, voicemail_url):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO voicemails (user_id, voicemail_url) VALUES (%s, %s)", (user_id, voicemail_url))
    conn.commit()
    cursor.close()
    conn.close()

# Elimina un messaggio vocale
def delete_voicemail(voice_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM voicemails WHERE voice_id = %s", (voice_id,))
    conn.commit()
    cursor.close()
    conn.close()

# --------------- Gestione token OAuth di Google ---------------

# Salva i token di accesso e aggiornamento di Google OAuth nel database
def save_user_google_token(user_id, access_token, refresh_token, token_uri, client_id, client_secret, scopes, expiry):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO google_tokens (user_id, access_token, refresh_token, token_uri, client_id, client_secret, scopes, expiry)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            access_token = VALUES(access_token),
            refresh_token = VALUES(refresh_token),
            token_uri = VALUES(token_uri),
            client_id = VALUES(client_id),
            client_secret = VALUES(client_secret),
            scopes = VALUES(scopes),
            expiry = VALUES(expiry)
    """, (user_id, access_token, refresh_token, token_uri, client_id, client_secret, scopes, expiry))

    conn.commit()
    cursor.close()
    conn.close()

# Recupera i token OAuth di un utente dal database
def get_user_google_token(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM google_tokens WHERE user_id = %s", (user_id,))
    token_data = cursor.fetchone()

    cursor.close()
    conn.close()

    return token_data

# Aggiorna il token di accesso di Google OAuth
def update_user_google_token(user_id, access_token, expiry):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE google_tokens
        SET access_token = %s, expiry = %s
        WHERE user_id = %s
    """, (access_token, expiry, user_id))

    conn.commit()
    cursor.close()
    conn.close()