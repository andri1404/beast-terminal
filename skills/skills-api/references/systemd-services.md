# Systemd Service Files for Skills API

Two service files that make the Skills API + Cloudflare Tunnel run persistently, independent of Hermes.

## skills-api.service

```
[Unit]
Description=Skills API Server (19,455+ pentest skills)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/.hermes/skills-api
Environment=PYTHONPATH=/home/ubuntu/.hermes/skills-api/deps
Environment=SKILLS_DIRS_EXTRA=
ExecStart=/home/ubuntu/pentest-venv/bin/python3 /home/ubuntu/.hermes/skills-api/server.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/.hermes/skills-api/server.log
StandardError=append:/home/ubuntu/.hermes/skills-api/server.log

[Install]
WantedBy=multi-user.target
```

## cf-tunnel.service

```
[Unit]
Description=Cloudflare Tunnel for skills-api.anzanesia.uk
After=network.target

[Service]
Type=simple
User=ubuntu
ExecStart=/bin/sh -c '/usr/local/bin/cloudflared tunnel run --token $$(cat /home/ubuntu/.cloudflared/tunnel_token.txt)'
Restart=always
RestartSec=15
StandardOutput=append:/home/ubuntu/.hermes/skills-api/tunnel.log
StandardError=append:/home/ubuntu/.hermes/skills-api/tunnel.log

[Install]
WantedBy=multi-user.target
```

## Key Design Decisions

- **`Type=simple`** — server.py is a long-running process, not a oneshot
- **`Restart=always`** — survives crashes and OOM kills
- **`RestartSec=10/15`** — brief cooldown between restart attempts
- **`User=ubuntu`** — runs as the ubuntu user, not root
- **`$$` escaping** — the `$$` in cf-tunnel.service is intentional; systemd strips one `$` so the shell sees `$(cat ...)`
- **cloudflared full path** — `/usr/local/bin/cloudflared` is required; the binary is not in systemd's default PATH

## Behavior

| Event | Result |
|---|---|
| System boot | Both services auto-start |
| Hermes stop/restart | No effect — services keep running |
| API crash (OOM, segfault) | Auto-restart after 10s |
| Cloudflared disconnect | Auto-restart after 15s |
| `systemctl stop skills-api` | Manual stop, no auto-restart |