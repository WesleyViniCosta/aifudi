from flask import Flask, render_template, request, jsonify
import imaplib
import email
from email.header import decode_header

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_latest_email', methods=['POST'])
def get_latest_email():
    email_address = request.json.get('email')
    senha = request.json.get('senha')
    
    if not email_address or not senha:
        return jsonify({"status": "error", "message": "Email e senha são obrigatórios"}), 400

    try:
        mail = imaplib.IMAP4_SSL('outlook.office365.com', timeout=10)
        mail.login(email_address, senha)
    except imaplib.IMAP4.error as e:
        return jsonify({"status": "error", "message": f"Erro de autenticação: {e}"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": f"Erro ao conectar ao servidor IMAP: {e}"}), 500

    def search_email_in_folder(folder_name):
        # Seleciona a pasta especificada
        status, _ = mail.select(folder_name)
        if status != 'OK':
            return None, f"Erro ao selecionar a pasta {folder_name}"

        # Procura o último e-mail com assunto "acesso"
        status, messages = mail.search(None, '(SUBJECT "acesso")')
        if status != 'OK' or not messages[0]:
            return None, None

        email_ids = messages[0].split()
        latest_email_id = email_ids[-1]

        # Busca o conteúdo do e-mail
        status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
        if status != 'OK':
            return None, "Erro ao obter o conteúdo do e-mail"

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        return msg, None

    # Tenta primeiro na caixa de entrada
    msg, error = search_email_in_folder('inbox')
    if error:
        return jsonify({"status": "error", "message": error}), 500
    elif msg:
        # E-mail encontrado na caixa de entrada
        subject, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8', errors='replace')
        mail.logout()
        return jsonify({"status": "success", "subject": subject, "folder": "inbox"}), 200

    # Tenta na lixeira se não encontrou na caixa de entrada
    msg, error = search_email_in_folder('"Deleted Items"')
    if error:
        return jsonify({"status": "error", "message": error}), 500
    elif msg:
        # E-mail encontrado na lixeira
        subject, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8', errors='replace')
        mail.logout()
        return jsonify({"status": "success", "subject": subject, "folder": "Deleted Items"}), 200

    # Se não encontrou em nenhuma das pastas
    mail.logout()
    return jsonify({"status": "error", "message": "Nenhum e-mail encontrado com o assunto desejado"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
