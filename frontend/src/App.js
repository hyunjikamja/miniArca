import logo from './logo.svg';
import './App.css';
import React, { useState, useEffect } from 'react';
import axios from 'axios';


function App() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    axios.get('http://localhost:5000')
      .then(response => setMessage(response.data))
      .catch(error => console.error('Error:', error));
  }, []);

  return (
    <div className="App">
      <h1>My Fullstack App</h1>
      <p>{message}</p>
    </div>
  );
}

export default App;