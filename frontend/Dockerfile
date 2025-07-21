# -------------------------------------------------------
#  Step 1: Build the React app using a Node image
# -------------------------------------------------------
FROM node:18-alpine AS build

WORKDIR /app

# Copy the package files and install dependencies
COPY package*.json ./
# Consider addressing peer dependency issues rather than relying on --legacy-peer-deps if possible for long-term maintenance.
RUN npm install --legacy-peer-deps

# Copy the rest of the frontend code
COPY . ./

# Build the React app for production
RUN npm run build

# -------------------------------------------------------
#  Step 2: Copy build outputs into a minimal Nginx container (non-root)
# -------------------------------------------------------
FROM nginx:stable-alpine

# The nginx:alpine images include an 'nginx' user (typically UID/GID 101)
# which is unprivileged. We will configure Nginx to run entirely as this user.

# Define variables for paths and user for clarity and easier modification
ARG NGINX_USER=nginx
ARG NGINX_GROUP=nginx
ARG NGINX_PID_FILE=/tmp/nginx.pid
ARG NGINX_PORT=8080
ARG NGINX_CONF_DIR=/etc/nginx
ARG NGINX_LOG_DIR=/var/log/nginx
ARG NGINX_CACHE_DIR=/var/cache/nginx
ARG NGINX_HTML_DIR=/usr/share/nginx/html

# 1. Modify Nginx configuration for non-root operation:
#    - Change PID file location: The default /var/run/nginx.pid is not writable by non-root.
#      We'll use /tmp/nginx.pid, which is generally writable.
#    - Change listening port: Port 80 is privileged. We'll use 8080.
#    Using \s+ in sed to match one or more whitespace characters for robustness.
RUN sed -i "s|^pid\s\+.*/nginx.pid;.*|pid ${NGINX_PID_FILE};|g" "${NGINX_CONF_DIR}/nginx.conf" && \
    # Modify the default server configuration to listen on port 8080 for IPv4
    sed -i "s|listen\s\+80;|listen ${NGINX_PORT};|g" "${NGINX_CONF_DIR}/conf.d/default.conf" && \
    # Modify the default server configuration to listen on port 8080 for IPv6, if present
    # The '|| true' ensures the command doesn't fail if the IPv6 listen directive isn't found.
    (grep -q "listen\s\+\[::\]:80;" "${NGINX_CONF_DIR}/conf.d/default.conf" && \
     sed -i "s|listen\s\+\[::\]:80;|listen [::]:${NGINX_PORT};|g" "${NGINX_CONF_DIR}/conf.d/default.conf") || true

# 2. Remove default nginx static assets from the image
RUN rm -rf ${NGINX_HTML_DIR}/*

# 3. Copy custom Nginx configuration for SPA routing
COPY nginx.conf ${NGINX_CONF_DIR}/conf.d/default.conf

# 4. Copy the compiled React application from the builder stage to Nginx's web root
COPY --from=build /app/build ${NGINX_HTML_DIR}

# 5. Set correct ownership for directories Nginx needs to write to or read from:
#    - NGINX_HTML_DIR: For serving application files.
#    - NGINX_CACHE_DIR: For Nginx caching mechanisms.
#    - NGINX_LOG_DIR: For Nginx logs (base image often sets this, but explicit is safer).
#    - Directory for PID file: Nginx needs to write the PID file.
#      /tmp should be writable, but ensuring the nginx user owns the specific path if it's deeper.
#      Since NGINX_PID_FILE is /tmp/nginx.pid, /tmp is its parent.
RUN mkdir -p "$(dirname ${NGINX_PID_FILE})" && \
    chown -R "${NGINX_USER}:${NGINX_GROUP}" "$(dirname ${NGINX_PID_FILE})" && \
    chown -R "${NGINX_USER}:${NGINX_GROUP}" "${NGINX_HTML_DIR}" && \
    chown -R "${NGINX_USER}:${NGINX_GROUP}" "${NGINX_CACHE_DIR}" && \
    chown -R "${NGINX_USER}:${NGINX_GROUP}" "${NGINX_LOG_DIR}"

# 6. Switch to the non-root 'nginx' user.
# This instruction ensures that Nginx and any subsequent commands run as this user.
USER ${NGINX_USER}

# Expose the new non-privileged port
EXPOSE ${NGINX_PORT}

# Standard command to run Nginx in the foreground.
# This will be executed by the 'nginx' user.
CMD ["nginx", "-g", "daemon off;"]
