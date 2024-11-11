from flask import Flask, render_template, request, jsonify
import imaplib
import email
from email.header import decode_header
import os

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

    try:
        status, _ = mail.select('inbox')
        if status != 'OK':
            return jsonify({"status": "error", "message": "Erro ao selecionar a caixa de entrada"}), 500

        status, messages = mail.search(None, '(SUBJECT "acesso")')
        if status != 'OK' or not messages[0]:
            return jsonify({"status": "error", "message": "Nenhum e-mail encontrado com o assunto desejado"}), 404

        email_ids = messages[0].split()
        latest_email_id = email_ids[-1]

        status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
        if status != 'OK':
            return jsonify({"status": "error", "message": "Erro ao obter o conteúdo do e-mail"}), 500

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else 'utf-8', errors='replace')
        
        mail.logout()
        return jsonify({"status": "success", "subject": subject}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Ocorreu um erro inesperado: {e}"}), 500
    finally:
        try:
            mail.logout()
        except:
            pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
