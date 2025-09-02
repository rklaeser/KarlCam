import React, { useState } from 'react';
import './HowItWorks.css';

const HowItWorks: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div id="learn-more" className="how-it-works">
      <div className="how-it-works-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h2>How This Works</h2>
        <button className="expand-toggle">
          {isExpanded ? '−' : '+'}
        </button>
      </div>

      {isExpanded && (
        <div className="how-it-works-content">
          <div className="architecture-overview">
            <h3>Architecture Overview</h3>
            <p>
              KarlCam pulls images from public webcams and scores them for fog using Gemini and in time a <strong>Convolutional Neural Network</strong>. It is built on <strong>Google Cloud Platform</strong> for about $10/month.
            </p>
          </div>

          <div className="data-flow">
            <h3>Data Flow</h3>
            <ol className="flow-steps">
              <li>
                <strong>Image Collection:</strong> Every half hour a Google Cloud Run job captures images from public webcams around San Francisco and scores them for fog using Gemini.
              </li>
              <li>
                <strong>Cloud Storage and SQL:</strong> Images are stored in Google Cloud Storage buckets and fog scores are stored in a Cloud SQL DB.
              </li>
              <li>
                <strong>Review:</strong> An admin site let's me review the fog scores and correct them if needed.
              </li>
              <li>
                <strong>Model Training:</strong> After enough images are collected from a range of conditions a supervised learning approach will be used to train the Convolutional Neural Network (CNN) and will replace Gemini. This should be cheaper, faster, and more accurate than Gemini but we shall see.
              </li>
              <li>
                  <strong>KarlCam Website:</strong> The latest fog scores are displayed here.
              </li>
            </ol>
          </div>

          <div className="gcp-services">
            <h3>Google Cloud Services Used</h3>
            <div className="services-grid">
              <div className="service-card">
                <h4>Cloud Storage</h4>
                <p>Stores webcam images with automatic lifecycle management</p>
              </div>
              <div className="service-card">
                <h4>Cloud SQL</h4>
                <p>PostgreSQL database for metadata and analysis results</p>
              </div>
              <div className="service-card">
                <h4>Gemini API</h4>
                <p> AI model for initial training data</p>
              </div>
              <div className="service-card">
                <h4>Cloud Scheduler</h4>
                <p>Automates image collection every 30 minutes</p>
              </div>
              <div className="service-card">
                <h4>Cloud Run</h4>
                <p>Containerized deployment with auto-scaling. Cheaper than always on containers in Kubernetes because of low volume.</p>
              </div>
            </div>
          </div>

          <div className="data-flow">
            <h3>Coming Soon</h3>
            <ul className="flow-steps">
              <li>
                <strong>Train CNN:</strong> Train and deploy the CNN. Will the CNN beat Gemini? Should individual models be trained for each camera location to 
                account for unique viewing angles, lighting conditions, and dirt on the lens. 
              </li>
              <li>
                <strong>Can satellite images do better?</strong> Are NOAA satellite images high enough resolution, frequent enough to be useful? Do they do better than KarlCam? 
                Would they aid training? See <a href="https://fog.today" target="_blank" rel="noopener noreferrer">fog.today</a> for an example.
              </li>
              <li>
                <strong>Add cameras:</strong> <a href="https://www.windy.com/-Webcams-San-Francisco-Marina-District/webcams/1693167474?37.796,-122.461,12" target="_blank" rel="noopener noreferrer">Windy</a> has a list of SF cameras, I'll add a few more outside SF and keep looking for others in SF.
              </li>
            </ul>
          </div>

          <div className="learn-more-links">
            <h3>Learn More</h3> 
            <ul>
              <li>
                <a href="https://github.com/rklaeser/KarlCam" target="_blank" rel="noopener noreferrer">
                  View Source Code on GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default HowItWorks;