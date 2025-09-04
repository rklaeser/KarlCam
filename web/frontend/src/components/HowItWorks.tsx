import React from 'react';

const HowItWorks: React.FC = () => {
  return (
    <div className="p-6 md:p-10">
      <h1 className="text-3xl md:text-4xl font-bold text-gray-800 mb-6">How I Built This</h1>
      
      <div className="space-y-8">
          <div>
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Architecture Overview</h3>
            <p className="text-gray-700 leading-relaxed">
              KarlCam pulls images from public webcams and scores them for fog using Gemini and in time a <strong>Convolutional Neural Network</strong>. It is built on <strong>Google Cloud Platform</strong> for about $10/month.
            </p>
          </div>

          <div>
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Data Flow</h3>
            <ol className="space-y-4 text-gray-700">
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">1</span>
                <div>
                  <strong>Image Collection:</strong> Every half hour a Google Cloud Run job captures images from public webcams around San Francisco and scores them for fog using Gemini.
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">2</span>
                <div>
                  <strong>Cloud Storage and SQL:</strong> Images are stored in Google Cloud Storage buckets and fog scores are stored in a Cloud SQL DB.
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">3</span>
                <div>
                  <strong>Review:</strong> An admin site let's me review the fog scores and correct them if needed.
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">4</span>
                <div>
                  <strong>Model Training:</strong> After enough images are collected from a range of conditions a supervised learning approach will be used to train the Convolutional Neural Network (CNN) and will replace Gemini. This should be cheaper, faster, and more accurate than Gemini but we shall see.
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white rounded-full text-sm flex items-center justify-center font-semibold">5</span>
                <div>
                  <strong>KarlCam Website:</strong> The latest fog scores are displayed here.
                </div>
              </li>
            </ol>
          </div>

          <div>
            <h3 className="text-xl font-semibold text-gray-800 mb-6">Google Cloud Services Used</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-800 mb-2">Cloud Storage</h4>
                <p className="text-sm text-gray-600">Stores webcam images with automatic lifecycle management</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-800 mb-2">Cloud SQL</h4>
                <p className="text-sm text-gray-600">PostgreSQL database for metadata and analysis results</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-800 mb-2">Gemini API</h4>
                <p className="text-sm text-gray-600">AI model for initial training data</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 className="font-semibold text-gray-800 mb-2">Cloud Scheduler</h4>
                <p className="text-sm text-gray-600">Automates image collection every 30 minutes</p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 md:col-span-2 lg:col-span-1">
                <h4 className="font-semibold text-gray-800 mb-2">Cloud Run</h4>
                <p className="text-sm text-gray-600">Containerized deployment with auto-scaling. Cheaper than always on containers in Kubernetes because of low volume.</p>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Coming Soon</h3>
            <ul className="space-y-4 text-gray-700">
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-2 h-2 bg-purple-500 rounded-full mt-2"></span>
                <div>
                  <strong>Train CNN:</strong> Train and deploy the CNN. Will the CNN beat Gemini? Should individual models be trained for each camera location to 
                  account for unique viewing angles, lighting conditions, and dirt on the lens.
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-2 h-2 bg-purple-500 rounded-full mt-2"></span>
                <div>
                  <strong>Can satellite images do better?</strong> Are NOAA satellite images high enough resolution, frequent enough to be useful? Do they do better than KarlCam? 
                  Would they aid training? See <a href="https://fog.today" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 underline">fog.today</a> for an example.
                </div>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-2 h-2 bg-purple-500 rounded-full mt-2"></span>
                <div>
                  <strong>Add cameras:</strong> <a href="https://www.windy.com/-Webcams-San-Francisco-Marina-District/webcams/1693167474?37.796,-122.461,12" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800 underline">Windy</a> has a list of SF cameras, I'll add a few more outside SF and keep looking for others in SF.
                </div>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Learn More</h3>
            <ul>
              <li>
                <a 
                  href="https://github.com/rklaeser/KarlCam" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-blue-600 hover:text-blue-800 underline font-medium"
                >
                  📂 View Source Code on GitHub
                </a>
              </li>
            </ul>
        </div>
      </div>
    </div>
  );
};

export default HowItWorks;