# -------------------------------------------------------
#  Step 1: Build the React app using a Node image
# -------------------------------------------------------
FROM node:22-alpine AS build

WORKDIR /app

# Copy the package files and install dependencies
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy the rest of the frontend code
COPY . ./

# Build the React app for production
RUN npm run build

# -------------------------------------------------------
#  Step 2: Copy build outputs into a minimal Nginx container (non-root)
# -------------------------------------------------------
FROM nginx:stable-alpine

# Define variables for non-root operation
ARG NGINX_USER=nginx
ARG NGINX_GROUP=nginx
ARG NGINX_PID_FILE=/tmp/nginx.pid
ARG NGINX_PORT=8080
ARG NGINX_HTML_DIR=/usr/share/nginx/html

# Configure Nginx for non-root operation
RUN sed -i "s|^pid\s\+.*/nginx.pid;.*|pid ${NGINX_PID_FILE};|g" /etc/nginx/nginx.conf && \
    sed -i "s|listen\s\+80;|listen ${NGINX_PORT};|g" /etc/nginx/conf.d/default.conf && \
    (sed -i "s|listen\s\+\[::\]:80;|listen [::]:${NGINX_PORT};|g" /etc/nginx/conf.d/default.conf || true)

# Remove default nginx static assets
RUN rm -rf ${NGINX_HTML_DIR}/*

# Copy the compiled React build
COPY --from=build /app/build ${NGINX_HTML_DIR}

# Set correct ownership and permissions
RUN chown -R ${NGINX_USER}:${NGINX_GROUP} ${NGINX_HTML_DIR} && \
    chown -R ${NGINX_USER}:${NGINX_GROUP} /var/cache/nginx && \
    chown -R ${NGINX_USER}:${NGINX_GROUP} /var/log/nginx && \
    mkdir -p $(dirname ${NGINX_PID_FILE}) && \
    chown -R ${NGINX_USER}:${NGINX_GROUP} $(dirname ${NGINX_PID_FILE})

# Switch to non-root user
USER ${NGINX_USER}

# Add health check (adjusted for port 8080)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1

# Expose non-privileged port
EXPOSE ${NGINX_PORT}

CMD ["nginx", "-g", "daemon off;"]