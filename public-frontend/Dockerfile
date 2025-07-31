# Multi-stage build for React app
FROM node:18-alpine as build

# Set working directory
WORKDIR /app

# Copy package files from the correct context path
COPY public-frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy source code from the correct context path
COPY public-frontend/ .

# Build the React app
RUN npm run build

# Production stage with simple serve
FROM node:18-alpine

# Install serve
RUN npm install -g serve

# Copy built app from build stage
COPY --from=build /app/build /app

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start serve
CMD ["serve", "-s", "/app", "-l", "3000"]