/**
 * Main Entry Point
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';

// Note: StrictMode causes double rendering in development, which can create
// duplicate WebSocket connections. For production builds, this is not an issue.
ReactDOM.createRoot(document.getElementById('root')).render(
  <App />
);
