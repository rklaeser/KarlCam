import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context';
import { ErrorBoundary } from './components/ErrorBoundary';
import Home from './pages/Home';
import About from './pages/About';
import AboutCreator from './pages/AboutCreator';
import MeasuringFog from './pages/MeasuringFog';
import WhyKarlCam from './pages/WhyKarlCam';
import TableView from './pages/TableView';
import './App.css';

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AppProvider 
        autoRefresh={true}
        refreshInterval={5 * 60 * 1000} // 5 minutes
      >
        <Router>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<ErrorBoundary><Home /></ErrorBoundary>} />
              <Route path="/about" element={<ErrorBoundary><About /></ErrorBoundary>} />
              <Route path="/about-creator" element={<ErrorBoundary><AboutCreator /></ErrorBoundary>} />
              <Route path="/measuring-fog" element={<ErrorBoundary><MeasuringFog /></ErrorBoundary>} />
              <Route path="/why-karlcam" element={<ErrorBoundary><WhyKarlCam /></ErrorBoundary>} />
              <Route path="/table" element={<ErrorBoundary><TableView /></ErrorBoundary>} />
            </Routes>
          </ErrorBoundary>
        </Router>
      </AppProvider>
    </ErrorBoundary>
  );
};

export default App;