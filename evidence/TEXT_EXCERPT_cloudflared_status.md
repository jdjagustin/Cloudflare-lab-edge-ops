# Sanitized text excerpt: cloudflared service status and a QUIC reconnect (E-008)

Source: terminal on the lab host (Ubuntu), 2026-11-09. The screenshot itself is NOT published (it shows the OS user name, tunnel connection IDs and the invocation ID). Values below are replaced with placeholders where marked.

Commands run:
```
systemctl status cloudflared
cloudflared --version
journalctl -u cloudflared -n 30 --no-pager
```

Service state (trimmed):
```
cloudflared.service - Cloudflare Tunnel client
     Loaded: loaded (/etc/systemd/system/cloudflared.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-11-02 15:36:05 CST; 6 days ago
   Main PID: <pid> (cloudflared)
     Memory: 48.4M (peak: 59.5M)
     CGroup: /system.slice/cloudflared.service
             /usr/bin/cloudflared --no-autoupdate --config /etc/cloudflared/config.yml tunnel run
```

Journal, 2026-11-09 (times in UTC, CST = UTC-6):
```
15:58:38Z INF Registered tunnel connection connIndex=2 connection=<connection-id> event=0 ip=<edge-ip>
16:04:28Z ERR failed to accept incoming stream requests error="failed to accept QUIC stream: Application error 0x0 (remote)"
16:04:28Z ERR failed to run the datagram handler error="context canceled" connIndex=3
16:04:28Z WRN Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=3
16:04:28Z INF Retrying connection in up to 1s connIndex=3
16:04:36Z INF Registered tunnel connection connIndex=3 connection=<connection-id> event=0 ip=<edge-ip>
```

Version at that time: `cloudflared version 2026.8.3 (built 2026-08-31)`. Upgraded to 2026.10.7 later the same day (see the Replicas view, E-015).

What it shows: the connector reconnected by itself about 8 seconds after the edge closed one QUIC connection (connIndex 3), while connIndex 2 stayed up. The cause of the remote close was not investigated in this lab, so no claim is made about it.
