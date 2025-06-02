import './index.css';
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { BrowserRouter } from 'react-router-dom';
import { initGA, usePageViews } from './ga';

// The root element where the React application will be mounted.
// This is the very first step in bringing the application to life in the browser.
const rootElement = document.getElementById('root') as HTMLElement;

// A simple component dedicated to initializing page view tracking.
// Observing user interaction patterns is vital for iterative improvement.
const Tracking = () => {
  usePageViews(); // This hook will handle the page view logic.
  return null; // This component does not render anything itself.
};

// Initialize Google Analytics.
// Early initialization of analytics ensures comprehensive data capture from the outset.
initGA();

const root = ReactDOM.createRoot(rootElement);

// Rendering the application within StrictMode for identifying potential problems.
// The BrowserRouter enables client-side routing, a fundamental aspect of modern single-page applications.
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Tracking /> {/* Component to handle page view tracking */}
      <App /> {/* The main application component */}
    </BrowserRouter>
  </React.StrictMode>,
);

// Reporting web vitals can provide insights into the application's performance.
// Understanding these metrics helps in optimizing the user experience.
// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();