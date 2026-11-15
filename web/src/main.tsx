import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './legacy.css';
import './modern-foundations.css';
import './workspace-redesign.css';

ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
