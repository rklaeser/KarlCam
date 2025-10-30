/**
 * Enhanced error display components that work with existing string-based error states
 */

import React from 'react';

interface ErrorDisplayProps {
  error: string | null;
  onRetry?: () => void;
  onDismiss?: () => void;
  variant?: 'inline' | 'card' | 'overlay';
  className?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  onDismiss,
  variant = 'card',
  className = ''
}) => {
  if (!error) return null;

  const getErrorIcon = () => (
    <svg className="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
    </svg>
  );

  const getUserFriendlyMessage = (error: string): string => {
    // Convert technical errors to user-friendly messages
    if (error.includes('Failed to fetch') || error.includes('NetworkError')) {
      return 'Unable to connect to the server. Please check your internet connection and try again.';
    }
    if (error.includes('timeout') || error.includes('Timeout')) {
      return 'The request took too long to complete. Please try again.';
    }
    if (error.includes('404') || error.includes('not found')) {
      return 'The requested information could not be found.';
    }
    if (error.includes('500') || error.includes('server error')) {
      return 'Server is experiencing issues. Please try again in a moment.';
    }
    if (error.includes('starting up')) {
      return 'The service is starting up. Please wait a moment and try again.';
    }
    // Return the original error if it's already user-friendly
    return error;
  };

  const variantStyles = {
    inline: 'rounded border-l-4 border-red-400 bg-red-50 p-3',
    card: 'rounded-lg border border-red-200 bg-red-50 shadow-sm p-4',
    overlay: 'rounded-xl border border-red-200 bg-red-50 shadow-lg p-6'
  };

  return (
    <div className={`${variantStyles[variant]} ${className}`}>
      <div className="flex items-start">
        {getErrorIcon()}
        <div className="ml-3 flex-1">
          <div className="font-medium text-red-800">
            {getUserFriendlyMessage(error)}
          </div>
          {(onRetry || onDismiss) && (
            <div className="mt-3 flex space-x-3">
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm font-medium transition-colors"
                >
                  Try Again
                </button>
              )}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className="text-red-600 hover:text-red-800 text-sm font-medium transition-colors"
                >
                  Dismiss
                </button>
              )}
            </div>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="flex-shrink-0 ml-2 text-red-500 hover:text-red-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

interface ErrorPageProps {
  error: string;
  onRetry?: () => void;
  onGoHome?: () => void;
  title?: string;
  className?: string;
}

export const ErrorPage: React.FC<ErrorPageProps> = ({
  error,
  onRetry,
  onGoHome,
  title = 'Something went wrong',
  className = ''
}) => {
  const getUserFriendlyMessage = (error: string): string => {
    if (error.includes('Failed to fetch') || error.includes('NetworkError')) {
      return 'Unable to connect to the server. Please check your internet connection.';
    }
    if (error.includes('timeout') || error.includes('Timeout')) {
      return 'The request took too long to complete.';
    }
    if (error.includes('404') || error.includes('not found')) {
      return 'The page or information you\'re looking for could not be found.';
    }
    if (error.includes('500') || error.includes('server error')) {
      return 'Server is experiencing issues. Please try again later.';
    }
    return error;
  };

  return (
    <div className={`min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 ${className}`}>
      <div className="max-w-md w-full space-y-8 text-center">
        <div>
          <div className="mx-auto h-12 w-12 text-red-500">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            {title}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {getUserFriendlyMessage(error)}
          </p>
        </div>
        <div className="space-y-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              Try Again
            </button>
          )}
          {onGoHome && (
            <button
              onClick={onGoHome}
              className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              Go Home
            </button>
          )}
        </div>
      </div>
    </div>
  );
};