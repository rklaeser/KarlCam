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
              KarlCam pulls images from public webcams and scores them for fog using a <strong>Convolutional Neural Network</strong>. It is built on <strong>Google Cloud Platform</strong> for about $10/month.
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
                <strong>Model Training:</strong> After collecting a few hundred images from a range of conditions a supervised learning approach was used to train the Convolutional Neural Network (CNN). This is cheaper, faster, and more accurate than Gemini because this simple classification is well suited for a CNN.
              </li>
              <li>
                  <strong>KarlCam Website:</strong> The latest fog scores using the CNN are displayed on the website.
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

          <div className="accuracy-info">
            <h3>Accuracy & Reliability</h3>
            <p>
              The system combines AI analysis with human validation through an admin panel to 
              ensure accurate fog detection. Each prediction includes a confidence score, and 
              administrators can review, validate, and correct Gemini's ratings to maintain 
              high-quality training data. I'm working on the statistics to show the comparative accuracy of Gemini and the CNN.
            </p>
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