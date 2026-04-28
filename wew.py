server {
    listen 80;
    server_name scan.ekomplektasiya.uz;

    client_max_body_size 50M;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/backend/doc-scan/doc-scan.sock;
        
        proxy_read_timeout 120;
        proxy_connect_timeout 120;
        proxy_send_timeout 120;
        
        # WebSocket support (agar kerak bo'lsa)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias /var/www/backend/doc-scan/static/;
    }
}