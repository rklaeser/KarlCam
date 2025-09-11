import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context';
import Home from './pages/Home';
import About from './pages/About';
import AboutCreator from './pages/AboutCreator';
import MeasuringFog from './pages/MeasuringFog';
import WhyKarlCam from './pages/WhyKarlCam';
import TableView from './pages/TableView';
import './App.css';

const App: React.FC = () => {
  return (
    <AppProvider 
      autoRefresh={true}
      refreshInterval={5 * 60 * 1000} // 5 minutes
    >
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/about-creator" element={<AboutCreator />} />
          <Route path="/measuring-fog" element={<MeasuringFog />} />
          <Route path="/why-karlcam" element={<WhyKarlCam />} />
          <Route path="/table" element={<TableView />} />
        </Routes>
      </Router>
    </AppProvider>
  );
};

export default App;