# Web Server Security Guide

## Accepting External Connections

The modified `start_web_tmux.sh` script now supports external connections through the `BIND_ADDR` environment variable.

### Usage

**Local access only (default, secure):**
```bash
scripts/start_web_tmux.sh
```

**External access (use with caution):**
```bash
BIND_ADDR=0.0.0.0 PORT=8081 scripts/start_web_tmux.sh
```

## Security Considerations

⚠️ **WARNING**: Exposing terminal access to the network is dangerous! Consider these security measures:

### 1. Authentication

**For ttyd:**
```bash
# Basic auth
ttyd -c username:password -i 0.0.0.0 -p 8081 tmux attach

# Or use the script with credentials
BIND_ADDR=0.0.0.0 ttyd -c admin:secretpass -i "$BIND_ADDR" -p "$PORT" tmux attach
```

**For gotty:**
```bash
# Basic auth
gotty -c username:password -a 0.0.0.0 -p 8081 -w tmux attach

# With title
gotty -t "NanoBragg Dashboard" -c admin:pass -a 0.0.0.0 -p 8081 -w tmux attach
```

### 2. Firewall Rules

**Ubuntu/Debian (ufw):**
```bash
# Allow only from specific IP
sudo ufw allow from 192.168.1.100 to any port 8081

# Allow from subnet
sudo ufw allow from 192.168.1.0/24 to any port 8081
```

**CentOS/RHEL (firewalld):**
```bash
# Allow port
sudo firewall-cmd --add-port=8081/tcp --permanent
sudo firewall-cmd --reload

# Allow from specific source
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.168.1.100" port port="8081" protocol="tcp" accept' --permanent
```

### 3. SSL/TLS (Recommended for Production)

**Using ttyd with SSL:**
```bash
# Generate self-signed cert (for testing)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Run with SSL
ttyd --ssl --ssl-cert cert.pem --ssl-key key.pem -i 0.0.0.0 -p 8081 tmux attach
```

**Using nginx reverse proxy (recommended):**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_read_timeout 86400;
    }

    # Basic auth
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

### 4. SSH Tunnel (Most Secure)

Instead of exposing the web server, use SSH port forwarding:

```bash
# From your local machine
ssh -L 8081:localhost:8081 user@remote-server

# Then access at http://localhost:8081
```

### 5. Container Isolation

Run in Docker for additional isolation:

```dockerfile
FROM ubuntu:latest
RUN apt-get update && apt-get install -y ttyd tmux
COPY scripts/start_web_tmux.sh /start.sh
EXPOSE 8081
CMD ["/start.sh"]
```

```bash
docker run -p 8081:8081 -e BIND_ADDR=0.0.0.0 nanobbragg-web
```

## Best Practices

1. **Never expose without authentication** in production environments
2. **Use HTTPS/SSL** for any external access
3. **Restrict by IP** whenever possible
4. **Monitor access logs** regularly
5. **Use read-only mode** if write access isn't needed:
   - ttyd: Remove write permissions from the tmux session
   - gotty: Don't use the `-w` flag (read-only by default)
6. **Set session timeouts** to auto-disconnect idle sessions
7. **Regular security updates** for ttyd/gotty and dependencies

## Quick Test

After starting the server with external access:
```bash
# Check if it's listening on all interfaces
netstat -tlnp | grep 8081
# or
ss -tlnp | grep 8081

# Test from another machine
curl -I http://your-server-ip:8081
```

## Stopping the Server

```bash
# Find the process
ps aux | grep ttyd
# or
ps aux | grep gotty

# Kill it
kill <PID>
```