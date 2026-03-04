FROM openresty/openresty:1.25.3.1-alpine

# Install cjson (already included in openresty)
# Copy nginx configuration
COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY lua/ /etc/nginx/lua/
COPY ssl/ /etc/nginx/ssl/

# Generate self-signed certs if they don't exist
RUN if [ ! -f /etc/nginx/ssl/cert.pem ]; then \
        apk add --no-cache openssl && \
        openssl req -x509 -nodes -days 365 \
            -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/key.pem \
            -out /etc/nginx/ssl/cert.pem \
            -subj "/C=ES/ST=Madrid/L=Madrid/O=VerifID/OU=Dev/CN=localhost"; \
    fi

EXPOSE 80 443

CMD ["openresty", "-g", "daemon off;"]
