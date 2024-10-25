# app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_socketio import SocketIO, join_room, emit
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notepad.db'
app.config['JWT_SECRET_KEY'] = 'supersecretkey'
db = SQLAlchemy(app)
jwt = JWTManager(app)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    locked = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_with = db.Column(db.String, default='')  # CSV of user IDs
    category = db.Column(db.String(50), nullable=True)

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'locked': self.locked,
            'user_id': self.user_id,
            'shared_with': self.shared_with.split(',') if self.shared_with else [],
            'category': self.category
        }

# Create Tables
with app.app_context():
    db.create_all()

# User Authentication Routes

@app.route('/')
def index():
    return "Hello, SocketIO!"

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User registered!"}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return jsonify({"msg": "Bad username or password"}), 401
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token)

# Note CRUD Routes
@app.route('/notes', methods=['POST'])
@jwt_required()
def create_note():
    user_id = get_jwt_identity()
    title = request.json.get('title')
    content = request.json.get('content')
    category = request.json.get('category', '')
    note = Note(title=title, content=content, user_id=user_id, category=category)
    db.session.add(note)
    db.session.commit()
    return jsonify({"msg": "Note created"}), 201

@app.route('/notes', methods=['GET'])
@jwt_required()
def get_notes():
    user_id = get_jwt_identity()
    notes = Note.query.filter((Note.user_id == user_id) | (Note.shared_with.contains(str(user_id)))).all()
    return jsonify([note.serialize() for note in notes])

@app.route('/notes/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_note(note_id):
    user_id = get_jwt_identity()
    note = Note.query.get(note_id)
    if note.user_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403
    note.title = request.json.get('title')
    note.content = request.json.get('content')
    note.category = request.json.get('category', '')
    db.session.commit()
    return jsonify({"msg": "Note updated"}), 200

@app.route('/notes/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note(note_id):
    user_id = get_jwt_identity()
    note = Note.query.get(note_id)
    if note.user_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403
    db.session.delete(note)
    db.session.commit()
    return jsonify({"msg": "Note deleted"}), 200

@app.route('/notes/<int:note_id>/lock', methods=['POST'])
@jwt_required()
def lock_note(note_id):
    user_id = get_jwt_identity()
    note = Note.query.get(note_id)
    if note.user_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403
    note.locked = not note.locked
    db.session.commit()
    return jsonify({"msg": "Note lock toggled"}), 200

@app.route('/notes/<int:note_id>/share', methods=['POST'])
@jwt_required()
def share_note(note_id):
    user_id = get_jwt_identity()
    note = Note.query.get(note_id)
    if note.user_id != user_id:
        return jsonify({"msg": "Unauthorized"}), 403
    shared_with_ids = request.json.get('shared_with')
    note.shared_with = ','.join(map(str, shared_with_ids))
    db.session.commit()
    return jsonify({"msg": "Note shared successfully"})

# Search Notes
@app.route('/notes/search', methods=['GET'])
@jwt_required()
def search_notes():
    user_id = get_jwt_identity()
    query = request.args.get('query', '')
    notes = Note.query.filter(Note.user_id == user_id, Note.content.contains(query)).all()
    return jsonify([note.serialize() for note in notes])

# Real-time Collaborative Editing using WebSocket
@socketio.on('join')
def on_join(data):
    note_id = data['note_id']
    join_room(note_id)

@socketio.on('edit_note')
def on_edit(data):
    note_id = data['note_id']
    content = data['content']
    emit('update_note', content, room=note_id)

if __name__ == '__main__':
    socketio.run(app, debug=True)
