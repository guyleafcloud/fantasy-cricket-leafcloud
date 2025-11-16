FROM node:20-alpine AS base

# Accept API URL as build argument
ARG NEXT_PUBLIC_API_URL=https://api.fantcric.fun
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install ALL dependencies (needed for build)
RUN npm install

# Copy application files
COPY . .

# Build the Next.js application with environment variable
RUN npm run build

# Expose port 3001
EXPOSE 3001

# Start the application
CMD ["npm", "start"]
