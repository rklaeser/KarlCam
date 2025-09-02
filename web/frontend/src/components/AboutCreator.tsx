import React from 'react';

const AboutCreator: React.FC = () => {
  return (
    <div className="p-6 md:p-10">
      <div className="flex flex-col md:flex-row items-center md:items-start gap-6 md:gap-8">
        <div className="flex-shrink-0">
          <img 
            src="/profile.png" 
            alt="Reed" 
            className="w-24 h-24 md:w-30 md:h-30 rounded-full object-cover border-4 border-blue-500 shadow-lg hover:scale-105 transition-transform duration-300"
          />
        </div>
        <div className="flex-1 text-center md:text-left">
          <h2 className="text-2xl md:text-3xl font-semibold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Hi I'm Reed!
          </h2>
          <p className="text-gray-700 text-lg leading-relaxed mb-6">
            I recently moved to San Francisco just in time for its 
            coldest summer since 1965. SF's fog is extremely localized and I wanted a way 
            to see where in the city it was sunny since the weather stations were getting it wrong. 
            I'm not sure how useful this will be but it was fun to build!
          </p>
          <div className="flex justify-center md:justify-start gap-4">
            <a 
              href="https://www.reedklaeser.com/" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300"
            >
              🌐 reedklaeser.com
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutCreator;