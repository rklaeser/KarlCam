import React from 'react';
import './AboutCreator.css';

const AboutCreator: React.FC = () => {
  return (
    <div className="about-creator">
      <div className="about-creator-content">
        <div className="profile-section">
          <div className="profile-image">
            <img src="/profile.png" alt="Reed" />
          </div>
          <div className="profile-text">
            <h2>Hi I'm Reed!</h2>
            <p>
              I made KarlCam because I recently moved to San Francisco just in time for its 
              coldest summer since 1965. SF's fog is extremely localized and I wanted a way 
              to see where in the city it was sunny. I also wanted to build on Google Cloud 
              and learn about Convolutional Neural Networks.
            </p>
            <div className="profile-links">
              <a href="https://www.reedklaeser.com/" target="_blank" rel="noopener noreferrer" className="portfolio-link">
                🌐 reedklaeser.com
              </a>
              <a href="https://www.linkedin.com/in/reed-klaeser/" target="_blank" rel="noopener noreferrer" className="linkedin-link">
                <img src="/Linkedin.png" alt="LinkedIn" className="linkedin-icon" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutCreator;