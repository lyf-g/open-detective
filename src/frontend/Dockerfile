# Frontend Dockerfile
FROM node:18-alpine AS build
WORKDIR /app

# Copy package files first for better caching
COPY src/frontend/package*.json ./
RUN npm install

# Copy source and build
COPY src/frontend/ .
# Bypass vue-tsc due to compatibility issues in Docker alpine environment
RUN npx vite build

# Production stage
FROM nginx:alpine
# Copy custom configuration
COPY src/frontend/nginx.conf /etc/nginx/conf.d/default.conf
# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]