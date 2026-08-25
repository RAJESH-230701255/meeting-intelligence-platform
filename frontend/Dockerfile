# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Build the application
COPY . .
# We use build args to inject env vars during the build step for Vite
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Serve stage
FROM nginx:alpine

# Copy built assets to Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Configure Nginx for SPA routing
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]
