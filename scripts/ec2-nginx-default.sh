#!/bin/bash
# EC2에서 실행: sudo bash ec2-nginx-default.sh
# (이 파일을 EC2로 복사한 뒤 실행하세요)
set -e
BACKUP="/etc/nginx/sites-available/default.bak.$(date +%Y%m%d%H%M%S)"
sudo cp /etc/nginx/sites-available/default "$BACKUP"
echo "Backed up to $BACKUP"
sudo tee /etc/nginx/sites-available/default > /dev/null << 'NGINX_EOF'
##
# Nginx default for api.kanggyeonggu.store → proxy to 127.0.0.1:8000
##
# Default server (80)
server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;
        root /var/www/html;
        index index.html index.htm index.nginx-debian.html;
        location / {
                try_files $uri $uri/ =404;
        }
}

# api.kanggyeonggu.store HTTPS (443) → app :8000
server {
        listen 443 ssl;
        listen [::]:443 ssl ipv6only=on;
        server_name api.kanggyeonggu.store;

        ssl_certificate /etc/letsencrypt/live/api.kanggyeonggu.store/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/api.kanggyeonggu.store/privkey.pem;
        include /etc/letsencrypt/options-ssl-nginx.conf;
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

        location / {
                proxy_pass http://127.0.0.1:8000;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
        }
}

# api.kanggyeonggu.store HTTP (80) → redirect to HTTPS
server {
        listen 80;
        listen [::]:80;
        server_name api.kanggyeonggu.store;
        return 301 https://$host$request_uri;
}
NGINX_EOF
echo "Wrote /etc/nginx/sites-available/default"
sudo nginx -t && sudo systemctl start nginx && echo "nginx started OK" || { echo "nginx -t or start failed"; exit 1; }
