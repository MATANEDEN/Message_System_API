from datetime import datetime
import re
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from flask_httpauth import HTTPBasicAuth
from parser_messages import parser_messages_func

app = Flask(__name__)

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
COL_LEN = int(os.getenv("COLUMN_LENGTH"))
NO_MESSAGES =  os.getenv("NO_MESSAGES")
DELETE_MESSAGES = os.getenv("DELETE_MESSAGES")
UPLOAD_MESSAGES = os.getenv("UPLOAD_MESSAGES")

class MessageDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(COL_LEN))
    receiver = db.Column(db.String(COL_LEN))
    message = db.Column(db.String(COL_LEN))
    subject = db.Column(db.String(COL_LEN))
    status = db.Column(db.String(COL_LEN))
    creation_date = db.Column(db.String(COL_LEN))


@app.route("/")
def home():
    return "Welcome To Message System - Home Page"


@app.route('/get_all_messages', methods=['GET'])
@auth.login_required
def get_all_messages():
    receiver = request.args.get("receiver")

    if receiver:
        messages = MessageDB.query.filter_by(receiver=receiver).all()
        message_dict = parser_messages_func(messages)
        update_messages_status(messages, 'read')
        return jsonify(message_dict)

    return NO_MESSAGES

@app.route('/read_message', methods=['GET'])
@auth.login_required
def get_one_message():
    receiver = request.args.get("receiver", None)

    if receiver:
        messages = MessageDB.query.filter_by(receiver=receiver).order_by(MessageDB.id.desc()).first()
        message_dict = parser_messages_func(messages)
        update_messages_status(messages, 'read')
        return jsonify(message_dict)

    return NO_MESSAGES


@app.route('/get_all_unread', methods=['GET'])
@auth.login_required
def get_unread_message():
    receiver = request.args.get("receiver", None)

    if receiver:
        messages = MessageDB.query.filter_by(receiver=receiver).filter_by(status="unread").all()
        message_dict = parser_messages_func(messages)
        update_messages_status(messages, 'read')
        return jsonify(message_dict)

    return NO_MESSAGES

@app.route('/delete_message', methods=['DELETE'])
@auth.login_required
def delete_message():
    email_sender = request.args.get("sender",None)
    email_receiver = request.args.get("receiver",None)

    if email_receiver:
        MessageDB.query.filter_by(receiver=email_receiver).delete()

    if email_sender:
        MessageDB.query.filter_by(sender=email_sender).delete()

    db.session.commit()
    return DELETE_MESSAGES


@app.route('/write_message', methods=['POST'])
@auth.login_required
def write_message():
    sender = request.args.get('sender')
    receiver = request.args.get('receiver')

    if not is_valid_email(sender):
        raise_email_error(sender, 'sender')
    if not is_valid_email(receiver):
        raise_email_error(sender, 'receiver')

    cur_msg = MessageDB(
          sender=sender,
          receiver=receiver,
          message=request.args.get('message'),
          subject=request.args.get('subject'),
          status="unread",
          creation_date=datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

    db.session.add(cur_msg)
    db.session.commit()
    return UPLOAD_MESSAGES


@auth.verify_password
def authenticate(username, password):
    if username and password:
        if username == os.getenv("USER") and password == os.getenv("PASSWORD"):
            return True
    return False


def is_valid_email(email):
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    is_match = re.match(regex, email)
    return is_match


def update_messages_status(messages, status):
    for msg in messages:
        msg.status = status
    db.session.commit()

def raise_email_error(email, side):
    print(f'Invalid email address for {side} ,please try again')
    raise ValueError(f'Invalid email address: {email}')


if __name__ == '__main__':
    db.create_all()
    app.run() 
