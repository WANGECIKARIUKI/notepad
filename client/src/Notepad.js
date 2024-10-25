import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { io } from 'socket.io-client';
import './Notepad.css'; // Import CSS

const socket = io("http://localhost:5000");

const colorThemes = [
  { backgroundColor: '#f7f7f7', textColor: '#333', buttonColor: '#4CAF50', borderColor: '#ccc' },
  { backgroundColor: '#f0f8ff', textColor: '#00008B', buttonColor: '#FF4500', borderColor: '#1E90FF' },
  { backgroundColor: '#FFF5EE', textColor: '#8B4513', buttonColor: '#20B2AA', borderColor: '#B8860B' },
  { backgroundColor: '#F0FFF0', textColor: '#2F4F4F', buttonColor: '#FF6347', borderColor: '#556B2F' },
  { backgroundColor: '#F5F5DC', textColor: '#A52A2A', buttonColor: '#FF69B4', borderColor: '#8A2BE2' },
  { backgroundColor: '#F0E68C', textColor: '#2E8B57', buttonColor: '#6A5ACD', borderColor: '#4682B4' },
  { backgroundColor: '#E6E6FA', textColor: '#191970', buttonColor: '#DA70D6', borderColor: '#9370DB' },
];

function Notepad() {
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState({ title: '', content: '' });
  const [selectedNote, setSelectedNote] = useState(null);
  const [currentTheme, setCurrentTheme] = useState(colorThemes[0]); // Default theme
  const [errorMessage, setErrorMessage] = useState(null); // Track errors

  const fetchNotes = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:5000/notes', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotes(response.data);
    } catch (error) {
      console.error('Error fetching notes:', error);
    }
  };

  const createNote = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post('http://localhost:5000/notes', newNote, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchNotes();
      setNewNote({ title: '', content: '' }); // Reset the form after creating the note
    } catch (error) {
      setErrorMessage('Failed to create note. Please check the input and try again.');
      console.error('Error creating note:', error);
    }
  };

  const updateNote = (note) => {
    socket.emit('edit_note', { note_id: note.id, content: note.content });
  };

  useEffect(() => {
    fetchNotes();
    socket.on('update_note', (newContent) => {
      setSelectedNote((prev) => ({ ...prev, content: newContent }));
    });
  }, []);

  return (
    <div className="notepad-container" style={{ backgroundColor: currentTheme.backgroundColor, color: currentTheme.textColor }}>
      <h1>Notepad</h1>

      {/* Theme Selector */}
      <div className="theme-selector">
        {colorThemes.map((theme, index) => (
          <button
            key={index}
            className="theme-button"
            style={{ backgroundColor: theme.buttonColor, borderColor: theme.borderColor }}
            onClick={() => setCurrentTheme(theme)}
          />
        ))}
      </div>

      {/* Note creation section */}
      <div className="note-creation">
        <input
          className="notepad-input"
          type="text"
          placeholder="Title"
          value={newNote.title}
          onChange={e => setNewNote({ ...newNote, title: e.target.value })}
          style={{ borderColor: currentTheme.borderColor }}
        />
        <ReactQuill
          className="notepad-editor"
          value={newNote.content}
          onChange={content => setNewNote({ ...newNote, content })}
        />
        <div className="button-container">
          <button className="notepad-button" style={{ backgroundColor: currentTheme.buttonColor }} onClick={createNote}>
            Create Note
          </button>
        </div>
        {errorMessage && <p className="error-message">{errorMessage}</p>}
      </div>

      {/* Notes list displayed as folders */}
      <div className="notes-folder-container">
        {notes.map(note => (
          <div
            key={note.id}
            className="note-folder"
            onClick={() => setSelectedNote(note)}
            style={{ borderColor: currentTheme.borderColor }}
          >
            <h3 className="note-folder-title">{note.title}</h3>
          </div>
        ))}
      </div>

      {/* Selected note details */}
      {selectedNote && (
        <div className="notepad-editor-wrapper">
          <h2>{selectedNote.title}</h2>
          <ReactQuill
            className="notepad-editor"
            value={selectedNote.content}
            onChange={content => updateNote({ ...selectedNote, content })}
          />
        </div>
      )}
    </div>
  );
}

export default Notepad;
