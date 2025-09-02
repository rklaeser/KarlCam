import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import About from './pages/About';
import AboutCreator from './pages/AboutCreator';
import MeasuringFog from './pages/MeasuringFog';
import TableView from './pages/TableView';
import './App.css';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/about-creator" element={<AboutCreator />} />
        <Route path="/measuring-fog" element={<MeasuringFog />} />
        <Route path="/table" element={<TableView />} />
      </Routes>
    </Router>
  );
};

export default App;