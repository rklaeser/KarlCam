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
              I recently moved to San Francisco just in time for its 
              coldest summer since 1965. SF's fog is extremely localized and I wanted a way 
              to see where in the city it was sunny since the weather stations were getting it wrong. 
              I'm not sure how useful this will be but it was fun to build!
            </p>
            <div className="profile-links">
              <a href="https://www.reedklaeser.com/" target="_blank" rel="noopener noreferrer" className="portfolio-link">
                🌐 reedklaeser.com
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutCreator;