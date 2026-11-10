# Cloudflare edge lab - evidence log

Chronological evidence for a hands-on Cloudflare lab (DNS, proxy, TLS, cache, WAF, rate limiting, Access, Tunnel, API, Terraform, Observability). Rule: record only what actually ran or was actually seen. Times are CST (UTC-6), 2026-11-09 and 2026-11-10. Personal values are replaced with placeholders such as <email>, <user>, <lan-ip>.

---

## E-001 — Cloudflare advisory email about cloudflared (11:43)
Source: PDF print of the email + screenshot of the header (images are NOT stored on disk; content transcribed below).
- Subject: "[Action Required] Upgrade your Cloudflare Tunnel to version 2026.10.2 or later"
- Date of email: Mon 2026-10-26 11:20 CST. Read by the user on 2026-11-09 (about 2 weeks later).
- Sender as displayed: Cloudflare <em@em1.cloudflare.com>. Authenticity NOT cryptographically verified (SPF/DKIM/DMARC headers not checked yet).
- Content (paraphrased):
  - Cause: eight eMudhra (emSign) intermediate certificates have weak private keys; cloudflared versions before 2026.10.2 still trust them.
  - Action: upgrade every cloudflared to >= 2026.10.2; macOS not installed via Homebrew >= 2026.10.3. Docker/Kubernetes: pull and redeploy image cloudflare/cloudflared:2026.10.3 (restarting an old image does not apply the fix).
  - Zero-downtime: with a single instance, add a temporary replica first (dashboard: Add a replica). Upgrade restarts cloudflared; 30 s grace period; WebSocket/SSH/TCP/UDP sessions drop.
  - Warning: if cloudflared connects to an HTTPS origin whose cert chains to an affected eMudhra cert, the upgraded cloudflared rejects it. Do not use noTLSVerify as a fix.
  - Verify version: dashboard Networking > Tunnels (connectors list) or `cloudflared --version` on each host.

## E-002 — Public confirmation of the incident (web search, 11:44)
- Cloudflare blog: "8 eMudhra certificates are compromised. Here's what you need to know" — https://blog.cloudflare.com/emudhra-certificate-compromise/ . States: Cloudflare learned on 2026-10-19 ~17:00 UTC; cloudflared fix is 2026.10.2; cloudflared security update published Oct 20 09:15 UTC.
- Cloudflare follow-up: https://blog.cloudflare.com/emudhra-patching
- Independent coverage: iTnews (https://www.itnews.com.au/news/cloudflare-warns-fixing-botched-emudhra-certs-goes-beyond-browsers-629804), YourStory (https://yourstory.com/2026/10/emudhra-faces-scrutiny-after-weak-certificate-keys-raise-web-security-concerns).
- Limit: confirms the incident and the fix version are real; does not by itself authenticate the specific email.

## E-003 — Screenshot of email header (11:45)
- Transcription: From "Cloudflare <em@em1.cloudflare.com>", To: user's Gmail, date lunes 26 de octubre de 2026 11:20 a.m.

## E-004 — Terminal on CloudSpartan: looking for cloudflared as a host service (11:47)
Prompt: <user>@CloudSpartan:~$
Commands run by the user:
```
systemctl status cloudflared
cloudflared --version
journalctl -u cloudflared -n 30 --no-pager
```
Verbatim output:
```
Unit cloudflared.service could not be found.
cloudflared: command not found
-- No entries --
```
Interpretation (limited to what the output proves): no systemd unit named cloudflared and no cloudflared binary in PATH on CloudSpartan. It does NOT prove the tunnel is gone; it may run as a container/pod or on another host. Plan assumption "cloudflared is a systemd service on CloudSpartan" was wrong (see the initial plan, Deviation 2).

## E-005 — Terminal on CloudSpartan: looking for cloudflared as K8s pod, container or process (11:50)
Commands run by the user:
```
kubectl get pods -A | grep -i cloudflared
docker ps | grep -i cloudflared
pgrep -a cloudflared
```
Verbatim output (timestamps/PID as printed; the same error line repeated 5 times):
```
E1109 11:50:00.341652 4024371 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp 127.0.0.1:8080: connect: connection refused"
(... same line x5, timestamps .342133 .343626 .344720 .345220)
The connection to the server localhost:8080 was refused - did you specify the right host or port?
```
Nothing else printed (docker ps | grep and pgrep printed no lines).
Interpretation (limited to what the output proves):
- kubectl: connection to localhost:8080 refused. That is kubectl's default when it has no kubeconfig for this user (or no API server there). It does NOT prove there is no k3s on this machine: k3s keeps its kubeconfig at /etc/rancher/k3s/k3s.yaml and usually needs sudo. Kubernetes check is INCONCLUSIVE.
- docker: no cloudflared line shown. If docker were missing or denied, an error would have appeared on screen (stderr is not filtered by grep); none did, so docker most likely ran and has no cloudflared container. Not shown: full `docker ps` output.
- pgrep: no cloudflared process running on this host.
- Net: no cloudflared as host service, host process or (very likely) Docker container on CloudSpartan. Kubernetes unverified.

## E-006 — Cloudflare dashboard: Networking > Tunnels (screenshot, 12:00)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Page: Tunnels. Usage card: Tunnels 1 / 1,000. "Showing 1-1 of 1". Filter: All statuses.
Table (one row):
| Name | Status | Replicas | Version | Routes |
|---|---|---|---|---|
| lab-tunnel | Healthy | 1 | 2026.8.3 (badge shown in orange) | 1 app |
Interpretation (limited to what is visible):
- The tunnel exists and reports Healthy with 1 replica: some cloudflared connector is connected to Cloudflare right now.
- Connector version is 2026.8.3, which is OLDER than the 2026.10.2 required by the advisory (E-001). So the advisory applies to this tunnel.
- The orange badge on the version is probably an "outdated" indicator; not confirmed by any text in the screenshot.
- The screenshot does NOT show where the connector runs (host name, OS, origin IP) nor the route's hostname/service. Those need the tunnel detail page.
- Combined with E-004/E-005: the live connector is not a host service, host process or (very likely) Docker container on CloudSpartan. K8s and other hosts are still possible.

## E-007 — Cloudflare dashboard: tunnel detail, Overview tab (screenshot, 12:03)
Source: screenshot pasted in chat (not on disk yet; transcribed here, sensitive values masked).
Breadcrumb: Tunnels > lab-tunnel. Tabs: Overview, Routes, Live logs (New).
Metrics: Active replicas 1 | Routes 1 | Status Healthy | Uptime 2 days.
Replicas table (one row):
| Field | Value |
|---|---|
| Replica ID | ...d83235 (full UUID masked) |
| Hostname | Cloudlab-1 |
| Origin IP | <public-ip> (public IP, masked) |
| Edge locations | dfw15, dfw08, dfw08, dfw01 |
| Version | 2026.8.3 (orange badge) |
| Architecture | linux_amd64 |
The Routes panel at the bottom of the page was not visible in the screenshot.
Interpretation (limited to what is visible):
- The only connector of lab-tunnel runs on host "Cloudlab-1" (linux_amd64), cloudflared 2026.8.3. This confirms the author's recollection and refutes the initial plan assumption (CloudSpartan). Resolves N-001 / Deviation 3 on location.
- 2026.8.3 < 2026.10.2: the advisory applies to this connector.
- "Uptime 2 days" is shown at tunnel level; it only says the tunnel has been connected for about 2 days. Not interpreted further.
- Edge locations are Dallas-area (dfw) data centers; shown as listed, no conclusion drawn.
- Still unknown: how cloudflared is installed on Cloudlab-1 (systemd service vs other) and the route's service URL (http vs https).

## E-008 — Terminal: SSH from CloudSpartan to Cloudlab-1, then cloudflared checks (12:06)
Source: two screenshots pasted in chat (not on disk yet; transcribed here).

### E-008a — SSH session
```
<user>@CloudSpartan:~$ ssh <lan-ip>
The authenticity of host '<lan-ip> (<lan-ip>)' can't be established.
ED25519 key fingerprint is: SHA256:<shown on screen, omitted here>
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '<lan-ip>' (ED25519) to the list of known hosts.
<user>@<lan-ip>'s password:
Welcome to Ubuntu 26.04.1 LTS (GNU/Linux 7.0.0-42-generic x86_64)
...
Expanded Security Maintenance for Applications is not enabled.
33 updates can be applied immediately.
5 of these updates are standard security updates.
20 additional security updates can be applied with ESM Apps.
*** System restart required ***
<user>@Cloudlab-1:~$
```
Facts: first SSH from CloudSpartan to <lan-ip> (Cloudlab-1), host key newly accepted, password authentication used. Cloudlab-1: Ubuntu 26.04.1 LTS, kernel 7.0.0-42-generic. Pending: 33 updates (5 standard security), 20 more ESM security updates (ESM not enabled), restart required.

### E-008b — cloudflared on Cloudlab-1
Commands (pasted as one block): `systemctl status cloudflared`, `cloudflared --version`, `journalctl -u cloudflared -n 30 --no-pager`.
`systemctl status` output (legible parts):
```
cloudflared.service - Cloudflare Tunnel client
  Loaded: loaded (/etc/systemd/system/cloudflared.service; enabled; preset: enabled)
  Active: active (running) since Mon 2026-11-02 15:36:05 CST; 6 days ago
  Main PID: 1889 (cloudflared)
  Tasks: 9 (limit: 14975)   Memory: 48.4M (peak: 59.5M)   CPU: 25min 13.179s
  CGroup: /system.slice/cloudflared.service
          1889 /usr/bin/cloudflared --no-autoupdate --config /etc/cloudflared/config.yml tunnel run
```
`journalctl` output (lines are cut at the right edge of the screenshot; only 9 lines visible, not 30; times are local CST, the ISO part is UTC):
```
Nov 09 09:58:37 INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 ...
Nov 09 09:58:38 INF Registered tunnel connection connIndex=2 connection=<uuid> event=0 ip=198.41.2..
Nov 09 10:04:28 ERR failed to accept incoming stream requests error="failed to accept QUIC stream: Application error 0x0 (remote)"
Nov 09 10:04:28 ERR failed to run the datagram handler error="context canceled" connIndex=3 event=0 ip=198.41.192.7
Nov 09 10:04:28 WRN failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex..
Nov 09 10:04:28 WRN Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=3 ...
Nov 09 10:04:28 INF Retrying connection in up to 1s connIndex=3 event=0 ip=198.41.192.7
Nov 09 10:04:29 WRN Connection terminated error="accept stream listener encountered a failure while serving" connIndex=3
Nov 09 10:04:36 INF Tunnel connection curve preferences: [...] connIndex=3 ...
Nov 09 10:04:36 INF Registered tunnel connection connIndex=3 connection=<uuid> event=0 ip=198.41.192..
```
`cloudflared --version` output: `cloudflared version 2026.8.3 (built 2026-08-31-10:04 UTC)`.
The screenshot ends with `^C` (Ctrl+C pressed) before the prompt returned.

Interpretation (limited to what is visible):
- cloudflared runs on Cloudlab-1 as a systemd service (enabled, running), binary at /usr/bin/cloudflared, version 2026.8.3 — matches the dashboard (E-006/E-007). The advisory applies.
- The service is started with `--no-autoupdate`: it will NOT update itself. Upgrading is manual.
- Config file: /etc/cloudflared/config.yml (contents not seen yet).
- At 2026-11-09 10:04:28 CST one of the tunnel connections (connIndex=3) dropped with a QUIC "Application error 0x0 (remote)" and re-registered about 8 seconds later; the log lines seen do not show the cause. No link to the eMudhra issue is shown or claimed. Other connections are not visible in the cut.
- Not explained: the dashboard says "Uptime 2 days" but the service says active since 2026-11-02 (6 days). Unknown what each measures; not interpreted.
- Not yet known: whether the binary was installed via apt (a .deb) or manually, and the origin service URL in config.yml (http vs https).
- Resolves N-001: the connector is confirmed on Cloudlab-1 (SSH prompt <user>@Cloudlab-1).

## E-009 — Terminal on Cloudlab-1: config.yml and apt-cache policy (12:09)
Commands run by the user:
```
cat /etc/cloudflared/config.yml
apt-cache policy cloudflared
```
Verbatim output (tunnel ID and credentials file name masked to the last 4 characters):
```
tunnel: ...5493
credentials-file: /home/<user>/.cloudflared/...5493.json

ingress:
  - hostname: grafana.jdjagustin-lab.dev
    service: http://localhost:32000
  - service: http_status:404
cloudflared:
  Installed: 2026.8.3
  Candidate: 2026.8.3
  Version table:
 *** 2026.8.3 100
        100 /var/lib/dpkg/status
```
Interpretation (limited to what the output shows):
- Locally-managed tunnel: config lives in /etc/cloudflared/config.yml with an ingress rule. One public hostname: grafana.jdjagustin-lab.dev -> http://localhost:32000 (Grafana NodePort, consistent with earlier project notes); catch-all returns 404.
- The origin is plain HTTP on localhost, NOT HTTPS. The advisory's warning about HTTPS origins with eMudhra-chained certificates therefore does not apply to this origin (no TLS certificate is validated between cloudflared and Grafana).
- apt-cache policy: Installed = Candidate = 2026.8.3, and the only source listed is /var/lib/dpkg/status (no apt repository line). Inference: cloudflared was installed from a local .deb (dpkg), and no Cloudflare apt repository is configured on this host. Consequence: `apt-get install --only-upgrade cloudflared` (the command written in the initial plan) would find nothing newer. Not yet confirmed by looking at /etc/apt/sources.list.d.
- The public hostname is on jdjagustin-lab.dev (older lab domain), NOT on <other-zone> as the plan assumed for the lab pieces.

## E-010 — Official docs check: how to upgrade cloudflared installed via dpkg (web search, 12:15)
Source: Cloudflare docs "Update cloudflared" — https://developers.cloudflare.com/tunnel/downloads/update-cloudflared/ (several indexed versions of the page; read through search snippets, not the full page).
- The docs have separate procedures per install method: apt repository, `dpkg -i`, yum, Homebrew, Docker, GitHub binary (`cloudflared update`). For package-manager installs the docs say to update with the same package manager.
- For "installed via dpkg -i" the procedure is: download the latest .deb from the cloudflared GitHub releases (`cloudflared-linux-<arch>.deb`, arch from `dpkg --print-architecture`) and install it with `sudo dpkg -i`, then `sudo systemctl restart cloudflared.service`.
- The docs warn that updating restarts cloudflared and affects traffic being served; zero-downtime options are a second cloudflared instance or Cloudflare Load Balancer.
- Conclusion for this host: matches E-009 (installed from a local .deb). The `apt-get install --only-upgrade` command in the initial plan does not apply. Use the dpkg procedure.
- Limit: snippets only; I did not see the full page. The new version number must be verified after the upgrade with `cloudflared --version` (must be >= 2026.10.2 per the advisory in E-001). No checksum/signature step was found in the snippets I saw.
Decision pending from the author: direct upgrade (brief Grafana drop, up to 30 s grace + reconnect) vs temporary replica first. Lab has no real users; recommendation given was direct upgrade.

## E-011 — Cloudlab-1: cloudflared upgrade executed (terminal, 12:13)
Source: terminal output pasted as text by the author. Commands run (as one block, from /tmp):
```
cd /tmp
curl --location --output cloudflared.deb "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$(dpkg --print-architecture).deb"
sudo dpkg -i cloudflared.deb
sudo systemctl restart cloudflared.service
cloudflared --version
systemctl status cloudflared --no-pager
rm /tmp/cloudflared.deb
```
Output (relevant parts, verbatim; connection UUIDs masked to last 4 chars):
```
100 19.00M 100 19.00M   0      0  6.12M      0   00:03   00:03          4.97M
[sudo: authenticate] Password:
(Reading database... 252049 files and directories currently installed.)
Preparing to unpack cloudflared.deb...
Unpacking cloudflared (2026.10.7) over (2026.8.3)...
Setting up cloudflared (2026.10.7)...
Processing triggers for man-db (2.13.1-1build1)...
Failed to allocate directory watch: Too many open files
cloudflared version 2026.10.7 (built 2026-10-30-17:05 UTC)
cloudflared.service - Cloudflare Tunnel client
     Loaded: loaded (/etc/systemd/system/cloudflared.service; enabled; preset: enabled)
     Active: active (running) since Mon 2026-11-09 12:13:06 CST; 662ms ago
   Main PID: 3717513 (cloudflared)   Tasks: 9   Memory: 18.4M (peak: 18.7M)   CPU: 675ms
     CGroup: /system.slice/cloudflared.service
             3717513 /usr/bin/cloudflared --no-autoupdate --config /etc/cloudflared/config.yml tunnel run
Nov 09 12:13:06 INF Starting metrics server on 127.0.0.1:20241/metrics
Nov 09 12:13:06 INF Registered tunnel connection connIndex=0 connection=...3558b7 ... protocol=quic
Nov 09 12:13:07 INF Registered tunnel connection connIndex=1 connection=...47d5   ... protocol=quic
Nov 09 12:13:08 INF Registered tunnel connection connIndex=2 connection=...6b62f6 ... protocol=quic
Hint: Some lines were ellipsized, use -l to show in full.
```
Facts (what the output shows):
- The .deb downloaded fully (19.00 MB, about 3 s). dpkg upgraded cloudflared from 2026.8.3 to 2026.10.7 (built 2026-10-30). 2026.10.7 is >= the 2026.10.2 required by the advisory (E-001). "latest" resolved to 2026.10.7, newer than the 2026.10.3 named in the email.
- The service restarted and was active (running) since 12:13:06 CST; the service file and the `--no-autoupdate --config /etc/cloudflared/config.yml tunnel run` command line are unchanged.
- Three tunnel connections (connIndex 0, 1, 2) registered over QUIC within about 2 seconds. connIndex=3 is NOT visible in this capture (status was taken 662 ms after start; the status view shows only the last lines).
- "Failed to allocate directory watch: Too many open files" appeared during the dpkg step. The same inotify-limit warning is already documented in earlier project notes as non-blocking for this host. Not investigated further now.
- The final `rm /tmp/cloudflared.deb` printed nothing; deletion is not yet verified.
Not shown / not measured: the exact downtime (when the old process stopped and when Grafana became unreachable); the dashboard view of the new version; whether Grafana answers through the public hostname.

## E-012 — Post-upgrade verification on Cloudlab-1 (terminal, 12:15) — PARTIAL
Commands run by the author:
```
journalctl -u cloudflared --since "12:13" --no-pager | grep -o "Registered tunnel connection connIndex=[0-9]"
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:32000/login
ls /tmp/cloudflared.deb
```
Verbatim output:
```
Registered tunnel connection connIndex=0
Registered tunnel connection connIndex=1
Registered tunnel connection connIndex=2
Registered tunnel connection connIndex=3
200
ls: cannot access '/tmp/cloudflared.deb': No such file or directory
```
Facts (what the output shows):
- All four tunnel connections (connIndex 0-3) have registered since 12:13 CST. This closes the gap noted in E-011 (4th connection).
- Grafana's origin answers HTTP 200 on http://localhost:32000/login: the origin is up, so the upgrade did not break Grafana itself.
- The temporary installer /tmp/cloudflared.deb no longer exists (cleanup verified).
Still pending for E-012: (a) dashboard shows version 2026.10.7 and Healthy for the replica; (b) public hostname https://grafana.jdjagustin-lab.dev responds (expected: Cloudflare Access login first, per earlier project notes; not verified yet). Downtime was not measured.

## E-013 — Browser: https://grafana.jdjagustin-lab.dev after the upgrade (screenshot, 12:17)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Page shown (dark theme): "Cloudflare Access" logo; Access team domain shown as <team-name>.cloudflareaccess.com (team name is part of the Access login page, mask before publishing if desired); heading "Log in to grafana"; "Sign in with:" with a single button "Cloudflare".
Facts (what it shows):
- Requests to the public hostname are intercepted by Cloudflare Access and show a login screen with one identity provider ("Cloudflare"), as described in earlier project notes.
- This page is served by Cloudflare's edge BEFORE any request reaches the origin. It proves the hostname resolves, Cloudflare answers and Access is enforcing authentication. It does NOT prove the tunnel reaches Grafana after the upgrade.
- To prove end-to-end: log in (the author, own account) and confirm Grafana loads through the tunnel. Not done yet.
- Known limit from the earlier notes: the login method tested in the lab is the Cloudflare account, not an external IdP (that is lab piece 3).

## E-014 — Why four connections: official docs (web search, 12:30)
Sources: Cloudflare docs, Tunnel overview (https://developers.cloudflare.com/tunnel), Tunnel configuration > Replicas and high availability (https://developers.cloudflare.com/tunnel/configuration/), Tunnel availability and failover (https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/configure-tunnels/tunnel-availability). Read through search snippets.
- A running cloudflared opens four outbound-only connections to at least two distinct Cloudflare data centers. If one connection, server or data center goes offline, the tunnel stays available.
- The four connections go to four different servers. A replica (extra cloudflared instance on the same tunnel) opens four more; up to 25 replicas (100 connections) per tunnel.
- Cloudflare does not guarantee which connection carries a given request.
Link to our own evidence:
- Our logs show connIndex 0, 1, 2, 3 registered after the upgrade (E-012) with `protocol=quic`. Edge IPs seen in E-008/E-011: 198.41.192.x and 198.41.200.x. The dashboard before the upgrade listed edge locations dfw15, dfw08, dfw08, dfw01 (E-007): four entries, consistent with four connections in the Dallas area. The exact mapping connIndex -> data center was NOT established.
- Inference (not proven): at 10:04 CST on 2026-11-09, connIndex=3 dropped and re-registered in ~8 s (E-008b) while the tunnel kept reporting Healthy; this is consistent with the redundancy described in the docs, but no request-level test was made.

## E-015 — Cloudflare dashboard after the upgrade (two screenshots, 12:19)
Source: screenshots pasted in chat (not on disk yet; transcribed here, sensitive values masked).
Tunnels list (one row): lab-tunnel | Status Healthy | Replicas 1 | Version 2026.10.7 (green badge; it was orange at 2026.8.3 in E-006) | Routes 1 app. Usage: 1 / 1,000 tunnels.
Replica table (tunnel detail):
| Field | Value |
|---|---|
| Replica ID | ...979bdb (full UUID masked; different from the pre-upgrade ID ...d83235 in E-007) |
| Hostname | Cloudlab-1 |
| Origin IP | <public-ip> (public IP, masked) |
| Edge locations | dfw05, dfw06, dfw06, dfw14 (before: dfw15, dfw08, dfw08, dfw01) |
| Version | 2026.10.7 (green badge) |
| Architecture | linux_amd64 |
Facts (what it shows):
- The dashboard confirms the upgrade from Cloudflare's side: one replica on Cloudlab-1 reports 2026.10.7 and the tunnel is Healthy. This matches the terminal evidence (E-011, E-012).
- The replica ID changed and the edge locations are different from before the restart. Both are consistent with a new cloudflared process opening new connections; not investigated further. Still four edge entries (see E-014).
- The orange badge on 2026.8.3 (E-006) is now green on 2026.10.7, consistent with the orange badge meaning "outdated" (still an inference; the UI text does not say so).
Not yet verified: that Grafana actually loads through the tunnel after logging in through Access (E-013 only shows the Access login screen). Downtime during the restart was not measured.

## E-016 — Cloudflare account sign-in page reached from the Access login (screenshot, 12:24)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Page: "Sign in to Cloudflare" with buttons Google, Apple, GitHub, "Continue with SSO", then Email/Password fields, checkbox "Save email and login method on this device" (checked), "Sign in", "Sign up", "Forgot your email or password?".
Facts: after clicking "Cloudflare" on the Access screen (E-013) the flow lands on the normal Cloudflare account login. This browser had no saved login method. earlier project notes only records that the tested login method was the Cloudflare account ("Sign in with: Cloudflare"), not which of these sign-in options the author used; the account email shown in the dashboard header starts with "<email>" (E-006).
Pending: the author signs in on his own (credentials are never shared in chat) and reports whether Grafana loads (closes Piece 0).

## E-017 — End-to-end check through Access, as reported by the author (12:29) — NO SCREENSHOT
Source: the author's verbal report in chat. No screenshot or log of this step; I did not see the page myself.
What the author reported, in order:
1. On the Cloudflare account sign-in page he tried email + password twice; both attempts showed an error message to the effect of "retry" (exact text not captured; cause not investigated).
2. The page had another button (he does not remember which); clicking it took him to the Cloudflare dashboard (so a Cloudflare session existed in that browser).
3. With the dashboard left open, he opened a new tab and went to https://grafana.jdjagustin-lab.dev. It let him through and he reached "the Grafana page" (whether the Grafana login screen or a Grafana dashboard was not specified).
Interpretation (limited to the report):
- The request went browser -> Cloudflare edge -> Access (accepted the existing Cloudflare session) -> tunnel (cloudflared 2026.10.7) -> Grafana. A Grafana page can only be served by the origin, so the tunnel is carrying traffic to Grafana after the upgrade.
- Limits: the email/password form was NOT what authenticated him (it errored twice, unexplained); the Access step passed thanks to the existing dashboard session. This is not a test of a fresh login, and it is not the three-test validation of earlier project notes. Downtime during the restart was not measured. A screenshot of the Grafana page would strengthen this entry; not required.

## E-018 — Screenshot: Grafana login page served at the public hostname (12:31)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the browser bookmarks bar visible in the image is personal and not transcribed).
Browser address bar: grafana.jdjagustin-lab.dev. Page: "Welcome to Grafana", fields "Email or username" and "Password", "Log in" button, "Forgot your password?". Footer: Documentation | Support | Community | Open Source | Grafana (version shown) | "New version available!".
Facts (what it shows):
- This is Grafana's own login page, which only the origin can serve. Together with E-017 it supports that traffic reaches Grafana through Access and the upgraded tunnel (cloudflared 2026.10.7). It replaces the "no screenshot" limit of E-017 in part: it is the Grafana LOGIN screen, not a logged-in dashboard.
- Observation: the instance runs Grafana (version) and shows "New version available!". It sits behind Cloudflare Access (E-013), which limits exposure, but it is not the latest release. Not acted on; added to the pending list as a later hardening item, outside the lab plan.

## E-019 — Screenshot: Cloudflare account home (12:31)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Account home ("What are we building today?"). Domains panel lists two zones: <other-zone> and jdjagustin-lab.dev. Workers panel: empty ("Ship something new"). Recents: Networking / Tunnels, AI / Models, Domains / Overview, Analytics / Web analytics, Analytics / Dashboards.
Facts: both domains live in the SAME Cloudflare account, so the existing tunnel could route hostnames from either zone. No Workers deployed.

## E-020 — Cloudlab-1: Kubernetes Secrets in namespace `observability` (names only, 12:50)
Command run by the author: `sudo k3s kubectl get secrets -n observability` (lists names/types/key counts/ages; no secret values were printed or shared).
Verbatim output:
```
NAME                                                       TYPE     DATA   AGE
grafana-admin-credentials                                  Opaque   2      94d
kube-prometheus-stack-admission                            Opaque   3      339d
kube-prometheus-stack-grafana                              Opaque   3      339d
loki-stack                                                 Opaque   1      339d
loki-stack-promtail                                        Opaque   1      339d
prometheus-kube-prometheus-stack-prometheus                Opaque   1      339d
prometheus-kube-prometheus-stack-prometheus-tls-assets-0   Opaque   1      339d
prometheus-kube-prometheus-stack-prometheus-web-config     Opaque   1      339d
```
Facts: k3s is running on Cloudlab-1 and `sudo k3s kubectl` reaches the cluster (the plain `kubectl` failure on CloudSpartan, E-005, was a missing kubeconfig). The namespace holds a kube-prometheus-stack + loki-stack deployment (names suggest Helm installs about 339 days old; naming-based inference). Two secrets could hold Grafana's admin login: `kube-prometheus-stack-grafana` (3 keys, 339d, looks like the chart's own secret) and `grafana-admin-credentials` (2 keys, 94d, created later, custom name). Which one Grafana actually reads is NOT established yet.
Pending: identify, without printing values, which secret the Grafana deployment references and its key names.

## E-021 — Cloudlab-1: which secret the Grafana deployment reads (12:53)
Commands run by the author:
```
sudo k3s kubectl get deploy -n observability -o yaml | grep -B2 -A6 -i "GF_SECURITY_ADMIN"
sudo k3s kubectl describe secret grafana-admin-credentials -n observability
```
Output (no secret values shown by these commands):
```
- name: GF_SECURITY_ADMIN_USER
  valueFrom: secretKeyRef: key: admin-user      name: kube-prometheus-stack-grafana
- name: GF_SECURITY_ADMIN_PASSWORD
  valueFrom: secretKeyRef: key: admin-password  name: kube-prometheus-stack-grafana
- name: GF_PATHS_DATA  value: /var/lib/grafana/

Name: grafana-admin-credentials   Namespace: observability   Type: Opaque
Data: admin-password: 15 bytes   admin-user: 5 bytes
```
Facts: the Grafana deployment takes its admin user and password from secret `kube-prometheus-stack-grafana` (keys admin-user, admin-password). The secret `grafana-admin-credentials` (same two key names; password is 15 bytes) is NOT referenced by the lines captured; the grep only showed these admin variables, so I cannot say what else uses it.
Caveat (general Grafana behavior, from my knowledge, not verified in this session): Grafana applies the admin password from the environment only when it first creates its database; if the password was changed later in the Grafana UI, the Kubernetes secret may no longer match the current password. Grafana data lives under /var/lib/grafana/.
Pending: the author reads the user/password locally in his own terminal (never pasted in chat) and tries the login.

## E-022 — Grafana login succeeded, as reported by the author (12:55) — NO SCREENSHOT
Source: the author's verbal report ("ya entre a Grafana"). He did not say which credentials he used (presumably those read from secret kube-prometheus-stack-grafana, E-021) and no screenshot was shared; I did not see the logged-in page.
Interpretation (limited to the report): a full login to Grafana through the public hostname (Access + upgraded tunnel + Grafana's own login) worked. Strengthens E-017/E-018: this is now a logged-in session, per the author's report. The optional extra Grafana user (his Gmail, admin rights) was only discussed; NOT created. No Grafana setting was changed in this lab.

## E-023 — Screenshot: Grafana "New user" form, before submitting (12:55)
Source: screenshot pasted in chat (not on disk yet; transcribed here). Grafana path: Home > Administration > Users and access > Users > New user.
Form: Name "<name>"; Email and Username both set to the author's Gmail address (masked here: <email>); Password field filled and masked (password-manager key icon shown; value not visible, not recorded); button "Create user" not yet pressed in the screenshot.
Facts: this is an optional side task outside the lab plan (own Grafana user instead of sharing `admin`). At the time of the screenshot the user was NOT created yet. Admin rights are set after creation (Grafana Admin switch and organization role). Nothing about this changes who passes Cloudflare Access.

## E-024 — Screenshot: Grafana user page of the new user (12:58)
Source: screenshot pasted in chat (not on disk yet; transcribed here; email masked).
Path: Home > Administration > Users and access > Users > <the author's Gmail>. Section "User information": Name "<name>"; Email and Username = the author's Gmail (masked: <email>); Password shown as "********" (fixed mask, not the real value or length). Buttons: Delete user, Disable user. Section "Permissions": Grafana Admin = Yes (with a "Change" link). Section "Organizations": Main Org. = Admin (links "Change role", "Remove from organization"); button "Add user to organization".
Facts (what it shows): the user exists in Grafana with the Grafana Admin switch on and the Admin role in Main Org. The screenshot does not show which account is currently logged in, and it does not prove that the new user can sign in.
Not verified yet: a test login with the new user in a private window. The original `admin` account is untouched (kept as recovery). Side task, outside the lab plan.

## E-025 — Screenshot: logged in to Grafana as the new user (13:00)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the browser bookmarks bar in the image is personal and not transcribed).
Address bar: grafana.jdjagustin-lab.dev. Page: Grafana "Home" with the "Welcome to Grafana" panel and the "Basic" setup cards (Grafana fundamentals tutorial; "Add your first data source" marked COMPLETE; "Create your first dashboard" marked COMPLETE). The user menu (top right) is open and shows the name "<name>" and the author's Gmail (masked: <email>), with Profile, Notification history, Change password, Sign out.
Facts (what it shows): a Grafana session logged in as the newly created user, reached through the public hostname (Access + upgraded tunnel). This upgrades E-022 (login "as reported") to a logged-in screenshot. The screenshot does not show whether the window was private; it does not matter for the result, since Access passes with an existing Cloudflare session. The original `admin` account was not changed.
Side task (own Grafana admin user) is closed. Not part of the lab plan.

## E-026 — Cloudlab-1: Python, port 8081, load and memory (terminal, 13:02)
Commands run by the author: `python3 --version`, `ss -ltn | grep -E ':8081\b' || echo "puerto 8081 libre"`, `uptime`, `free -h`.
Verbatim output:
```
Python 3.14.4
puerto 8081 libre
 13:02:44 up 6 days, 21:28,  2 users,  load average: 7.42, 6.72, 6.16
               total        used        free      shared  buff/cache   available
Mem:            15Gi       6.2Gi       543Mi       219Mi       8.8Gi       8.8Gi
Swap:          4.0Gi       104Mi       3.9Gi
```
Facts (what the output shows):
- Python 3.14.4 is installed; nothing listens on port 8081 (free for the temporary static site).
- Memory: 15 GiB total, 6.2 GiB used, 8.8 GiB available (buff/cache 8.8 GiB), swap 104 MiB used of 4 GiB. RAM is not tight.
- Load average 7.42 / 6.72 / 6.16 (1/5/15 min) with the machine up 6 days 21 h and 2 users logged in. The load has been high and roughly steady for at least 15 minutes. Number of CPU cores NOT known yet, so the load cannot be judged: the earlier notes says Cloudlab-1 has a Celeron G530 (a 2011 dual-core), which would make a load of ~7 heavy; to be confirmed with `nproc`.
- Not established: which processes use the CPU. No link is claimed between this load and the 10:04 connection drop (E-008b).

## E-027 — Cloudlab-1: CPU cores and top CPU processes (terminal, 13:05)
Commands run by the author: `nproc` and `ps -eo pid,pcpu,pmem,comm --sort=-pcpu | head -n 8`.
Verbatim output:
```
2
    PID %CPU %MEM COMMAND
3736889  150  0.0 ps
  19337 29.0  0.0 open5gs-mmed
   1921 25.9  9.4 k3s-server
  19010 18.9  0.3 open5gs-smfd
  52451 18.9  0.0 open5gs-hssd
  53298 18.9  0.0 open5gs-pcrfd
  17803 15.1  4.4 prometheus
```
Facts and limits:
- Cloudlab-1 has 2 CPU cores. A load average of ~7 (E-026) is therefore about 3.5 runnable tasks per core: the CPU is saturated, steadily.
- Largest consumers: Open5GS daemons (mmed, smfd, hssd, pcrfd), k3s-server and prometheus. These belong to the lab's 5G/EPC core and the k3s cluster, not to this Cloudflare lab.
- Caveat: `ps` %CPU is the average over each process's whole lifetime, not the current usage; the `ps` row itself (150%) is an artifact of that measure. So the ranking is indicative, not an instantaneous reading.
- Design consequences for the Cloudflare lab (reasoning, not measured): cache hits and requests blocked by WAF/rate limiting are answered at Cloudflare's edge and never reach Cloudlab-1; only cache misses and allowed requests cost origin CPU. Plan: keep test volumes modest and run the static server with the lowest priority (`nice -n 19`).
- Not read: the LAB_DRILLDOWN*_CLOUDLAB1_* files of 2026-11-02 in ~/projects, which suggest this host's load was already investigated.

## E-028 — Static site files created locally in this folder (13:14)
Files written in `site/` (this folder, on the author's Mac): `index.html` (title "Lab site", links /style.css, one paragraph) and `style.css` (one rule). Content has no company or role names (portfolio rule). They are NOT yet on Cloudlab-1 and nothing serves them yet.

## E-029 — Static site files created on Cloudlab-1 (terminal, 13:07)
Commands run by the author: `mkdir -p ~/lab-site`, two `cat > ... <<'EOF'` blocks (same content as ./site, see E-028), `ls -la ~/lab-site`.
Verbatim `ls` output:
```
total 16
drwxrwxr-x  2 <user> <user> 4096 Nov  9 13:07 .
drwxr-x--- 31 <user> <user> 4096 Nov  9 13:07 ..
-rw-rw-r--  1 <user> <user>  276 Nov  9 13:07 index.html
-rw-rw-r--  1 <user> <user>   48 Nov  9 13:07 style.css
```
Facts: ~/lab-site on Cloudlab-1 holds index.html (276 bytes) and style.css (48 bytes); both sizes match the copies in ./site on the Mac (276 and 48 bytes), a consistency hint, not a byte-for-byte comparison. Nothing is running yet.
Cleanup (planned): stop the server, `rm -r ~/lab-site`, remove /tmp/lab-site.log, remove the tunnel ingress rule and the DNS record.

## E-030 — Cloudlab-1: static server started and tested locally (terminal, 13:09)
Commands run by the author (one block): `nohup nice -n 19 python3 -m http.server 8081 --bind 127.0.0.1 --directory ~/lab-site > /tmp/lab-site.log 2>&1 &`, `sleep 1`, `ss -ltn | grep 8081`, `curl -sI http://127.0.0.1:8081/ | head -n 5`, `curl -s http://127.0.0.1:8081/style.css`, `pgrep -af "http.server 8081"`.
Verbatim output:
```
[1] 3738629
LISTEN 0      5          127.0.0.1:8081       0.0.0.0:*
HTTP/1.0 200 OK
Server: SimpleHTTP/0.6 Python/3.14.4
Date: Mon, 09 Nov 2026 19:09:17 GMT
Content-type: text/html
Content-Length: 276
body { font-family: sans-serif; margin: 2rem; }
3738629 python3 -m http.server 8081 --bind 127.0.0.1 --directory /home/<user>/lab-site
```
Facts: the temporary static server runs as PID 3738629, listening ONLY on 127.0.0.1:8081 (not reachable from the LAN), answers `200 OK` for / with Content-Length 276 (matches index.html) and serves the 1-line stylesheet. Started with `nice -n 19` (the priority is not visible in this output; not verified with `ps -o ni`). Log file: /tmp/lab-site.log. Only the first 5 header lines were shown (head -n 5), so headers such as Last-Modified were not seen.
Stop it at cleanup: `kill 3738629` (PID valid only until the process or machine restarts).

## E-031 — Cloudlab-1: config.yml backed up, edited and validated (terminal, 13:13)
Commands run by the author (one block): `sudo cp -a /etc/cloudflared/config.yml /etc/cloudflared/config.yml.bak-2026-11-09`, a `sudo python3 - <<'PY'` script that inserts the new ingress rule before the catch-all, `sudo cat /etc/cloudflared/config.yml`, `cloudflared tunnel --config /etc/cloudflared/config.yml ingress validate`, `cloudflared tunnel --config /etc/cloudflared/config.yml ingress rule https://lab.jdjagustin-lab.dev`.
Verbatim output (tunnel ID and credentials file name masked to the last 4 characters):
```
tunnel: ...5493
credentials-file: /home/<user>/.cloudflared/...5493.json

ingress:
  - hostname: grafana.jdjagustin-lab.dev
    service: http://localhost:32000
  - hostname: lab.jdjagustin-lab.dev
    service: http://localhost:8081
  - service: http_status:404
Validating rules from  /etc/cloudflared/config.yml
OK
Using rules from /etc/cloudflared/config.yml
Matched rule #1
	hostname: lab.jdjagustin-lab.dev
	service: http://localhost:8081
```
Facts: a backup of the previous config exists at /etc/cloudflared/config.yml.bak-2026-11-09. The new rule sits between the Grafana rule and the 404 catch-all. cloudflared's own validator says OK, and the rule matcher maps https://lab.jdjagustin-lab.dev to rule #1 (counting from 0) -> http://localhost:8081, as intended.
Not done yet: the running cloudflared has NOT reloaded this config (it needs a restart), and no DNS record exists for lab.jdjagustin-lab.dev, so the hostname does not resolve to the tunnel yet.
Rollback: `sudo cp -a /etc/cloudflared/config.yml.bak-2026-11-09 /etc/cloudflared/config.yml` (then restart). Cleanup at the end: restore or delete the backup, remove the rule.

## E-032 — Cloudlab-1: cloudflared restarted with the new ingress rule (terminal, 13:15)
Commands run by the author (one block): `sudo systemctl restart cloudflared.service`, `sleep 5`, `systemctl is-active cloudflared`, `journalctl -u cloudflared --since "2 minutes ago" --no-pager | grep -o -E "Registered tunnel connection connIndex=[0-9]"`.
Verbatim output:
```
Failed to allocate directory watch: Too many open files
active
Registered tunnel connection connIndex=0
Registered tunnel connection connIndex=1
Registered tunnel connection connIndex=2
Registered tunnel connection connIndex=3
```
Facts: the service restarted and is `active`; all four tunnel connections (0-3) registered again within the 5 s wait plus the log window. The "Failed to allocate directory watch: Too many open files" warning appeared again (same inotify-limit warning as in E-011 and earlier project notes; not investigated).
Not verified: that cloudflared actually loaded the new rule (the log lines for the configuration were not shown; the real proof comes when lab.jdjagustin-lab.dev is reached through the tunnel); that Grafana kept answering through the public hostname after this restart (the author had not reported it yet); the duration of the drop (not measured).

## E-033 — Grafana session dropped by the cloudflared restart, as reported by the author (13:17) — NO SCREENSHOT
Source: the author's verbal report: the Grafana connection he had open (logged in) "se cayo" after the restart in E-032; he will log in again with his own user.
Interpretation (limited to the report): consistent with what the Cloudflare advisory says (E-001): restarting cloudflared drops long-lived connections (for example WebSockets) and clients must reconnect. The exact failure he saw (error page, blank, login screen) was not described, and how long the drop lasted was not measured. Whether Grafana is reachable again is pending his report.

## E-034 — Screenshot: Grafana login page served again after the restart (13:18)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the browser bookmarks bar is personal and not transcribed).
Address bar: grafana.jdjagustin-lab.dev. Page: "Welcome to Grafana" login form (Grafana (version), "New version available!"), "Email or username" filled with the author's Gmail (masked: <email>), the password field filled and masked by the password manager (value not visible, not recorded), "Log in" not yet pressed.
Facts: after the cloudflared restart (E-032) the public hostname answers again and Grafana's own login page is served, which only the origin can do. This closes the "Grafana reachable after the restart" gap listed in E-032. It matches E-033: his previous session was dropped and he is asked to log in again. The screenshot does not show Access intervening this time (an existing Cloudflare session was probably still valid; not verified), and it does not show the login result or how long the drop lasted.

## E-035 — Grafana login after the restart succeeded, as reported by the author (13:19) — NO SCREENSHOT
Source: the author's verbal report ("entre"). He logged into Grafana again with his own user through the public hostname after the cloudflared restart. No screenshot of the logged-in page; drop duration not measured. Together with E-034 this supports that the tunnel, the Access layer and Grafana work end to end after the second restart.

## E-036 — Screenshot: DNS records of jdjagustin-lab.dev BEFORE adding the lab record (13:21)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Page: "DNS records for jdjagustin-lab.dev" (zone plan badge: free; "DNS Setup: Full"). Left menu under DNS: Records, Analytics, Settings; other zone sections visible include SSL/TLS, Security, Access, Speed, Email. Buttons: Import, Export, Add record, Filters, Display options. "You have used 1 of 200 available DNS records in this domain."
Recommendations panel (3): "Visitors cannot reach www.jdjagustin-lab.dev" (suggests an A/AAAA/CNAME for www) and "Visitors cannot reach jdjagustin-lab.dev"; the third is not visible. Not acted on: the zone has no apex or www records and the lab does not need them.
Records table (one row): Name grafana.jdjagustin-lab.dev | Type Tunnel | Content lab-tunnel (link) | Proxy status Proxied | TTL Auto | Tags -.
Facts and limits:
- The zone has exactly one record, the Grafana one. The `lab` record does NOT exist yet (this is the "before" state).
- The dashboard labels the Grafana record as type "Tunnel" with content "lab-tunnel", proxied. My reading (from how Cloudflare displays tunnel CNAME records, not verified here): it is a proxied CNAME to <tunnel-id>.cfargotunnel.com shown with the tunnel's name. The new `lab` record should end up looking the same.
- The zone has an Export button: a DNS backup in one click exists in this UI (earlier I had only recalled it).

## E-037 — Where the DNS target comes from: official docs check (web search, 13:25)
Source: Cloudflare docs, Tunnel routing and "DNS records" pages — https://developers.cloudflare.com/tunnel/routing/ and https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/dns/ . Read through search snippets, not the full pages.
- Every tunnel gets a subdomain `<UUID>.cfargotunnel.com`. To route a hostname to the tunnel, create a CNAME in DNS: Type CNAME, Name = the subdomain, Target = `<UUID>.cfargotunnel.com`. For locally-managed tunnels the same record can be created with `cloudflared tunnel route dns <UUID or NAME> <hostname>`.
- The tunnel UUID is not secret, and `cfargotunnel.com` only proxies traffic for DNS records in the same Cloudflare account.
- The DNS record and the tunnel are independent: a record can point to a tunnel that is not running. A docs snippet said visitors then see error 1016 (later NOT confirmed: see E-122; a tunnel id that does not exist gave 1033, E-127).
- A published hostname inherits that hostname's Cloudflare settings (cache rules, WAF rules and other Rules), which is what makes per-hostname lab tests possible.
Where the author's value comes from: the UUID is the `tunnel:` line of /etc/cloudflared/config.yml on Cloudlab-1 (E-009, E-031); the suffix `.cfargotunnel.com` is the documented format. Cross-check available: the dashboard shows the Tunnel ID under Networking > Tunnels (per the docs).
Note for lab piece 4: the plan expected "530/1033" when the origin is down behind a tunnel; this page mentions 1016 for a record pointing to a stopped tunnel. These may be different situations (tunnel stopped vs. origin service down). Neither code is claimed until it is reproduced and captured in this lab.

## E-038 — DNS zone export of jdjagustin-lab.dev BEFORE adding the lab record (13:24)
Source: file `jdjagustin-lab.dev.txt` attached by the author (Cloudflare DNS > Export). Exported 2026-11-09 19:22:54 UTC (13:22 CST). Saved as a transcription in `evidence/jdjagustin-lab.dev_zone_export_BEFORE-lab-record_2026-11-09_1922UTC.txt` (header comments trimmed; contains the tunnel UUID and the zone's name servers: private working evidence, check before publishing).
Contents (what the export shows):
- SOA: donald.ns.cloudflare.com., serial 2054591877. NS: donald.ns.cloudflare.com. and georgia.ns.cloudflare.com. (the zone's authoritative name servers are Cloudflare's).
- Exactly one other record: `grafana.jdjagustin-lab.dev.` TTL 1 (= "Auto" in the dashboard), type CNAME, target `<tunnel-uuid>.cfargotunnel.com.` with the tag `cf-proxied:true`.
Facts:
- This confirms my reading in E-036: the "Tunnel" type shown in the dashboard is a proxied CNAME to `<UUID>.cfargotunnel.com`.
- The UUID in that CNAME equals the `tunnel:` value of /etc/cloudflared/config.yml on Cloudlab-1 (E-009, E-031): same string, so the target I proposed for `lab` is the right one (compared by reading both values).
- It is the "before" backup of the zone: if the new record causes trouble, the zone can be restored to this state by deleting the `lab` record (import is possible but not needed for one record).

## E-039 — Screenshot: "Add record" dialog with the Type list open (13:27)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Dialog "Add record". Helper text for the selected type: "[name] is an alias of [target] and has its traffic proxied through Cloudflare." Fields: Type = CNAME (selected, checkmark in the list), Name (placeholder "Use @ for root"), Target (placeholder ends in "...le.com"), Proxy status = Proxied (toggle on, orange cloud), TTL = Auto. Buttons: Cancel (and a Save button partly hidden behind the open list).
Type list as visible: A, AAAA, CAA, CERT, CNAME, DNSKEY, DS, HTTPS, LOC, MX, NAPTR, NS, OPENPGPKEY, PTR, SMIMEA (the list continues below the visible part; remaining types not seen). Behind the dialog the existing row `...jdjagustin-lab.dev | Tunnel | lab-tunnel | Proxied | Auto` is visible.
Facts: the form is at the right place with CNAME and Proxied already preselected. The record had NOT been saved at this point.
the author's request: a DNS deep-dive document is wanted at the END of the lab (see the initial plan pending deliverables); use this list of record types as a starting point.

## E-040 — Screenshot: "Add record" form filled in for `lab`, before saving (13:29)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Preview sentence shown by the dashboard: "lab.jdjagustin-lab.dev is an alias of <tunnel-uuid>.cfargotunnel.com and has its traffic proxied through Cloudflare."
Fields: Type CNAME | Name `lab` | Target `<tunnel-uuid>.cfargotunnel.com` | Proxy status Proxied (toggle on) | TTL Auto. Section "Record Attributes" (UI text: the information there does not impact DNS resolution and is only for reference) with an optional Comment field (up to 100 characters), empty at this point. Buttons: Save, Cancel.
Facts: the target string equals the `tunnel:` value of config.yml (E-009, E-031) and the CNAME target in the zone export (E-038), compared by reading. The record was NOT saved yet when the screenshot was taken.
Suggested comment (the author's decision): marks the record as temporary to ease cleanup; it is only a label.

## E-041 — Screenshot: DNS records of jdjagustin-lab.dev AFTER saving the lab record (13:30)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Page "DNS records for jdjagustin-lab.dev" (plan badge free, DNS Setup: Full). "You have used 2 of 200 available DNS records in this domain." "Showing 1-2 of 2".
Records table:
| Name | Type | Content | Proxy status | TTL |
|---|---|---|---|---|
| grafana.jdjagustin-lab.dev | Tunnel | lab-tunnel | Proxied | Auto |
| lab.jdjagustin-lab.dev | Tunnel | lab-tunnel | Proxied | Auto |
The Comment/Tags columns are cut off at the right edge of the screenshot; whether the optional comment was saved is not visible.
Facts: the `lab` record exists (created about 13:30 CST) and looks identical to the Grafana one: a proxied CNAME to the tunnel, shown by the dashboard as type "Tunnel" with content "lab-tunnel". The zone went from 1 record (E-036/E-038) to 2.
Not verified yet: that the name resolves publicly (dig), the zone's SSL/TLS mode, and that https://lab.jdjagustin-lab.dev reaches the static site through the tunnel (which also proves cloudflared loaded the new ingress rule).

## E-042 — dig from the author's Mac: lab and grafana resolve to Cloudflare IPs (terminal, 13:31)
Commands run by the author (Mac terminal, cwd ~/Downloads): `dig +short lab.jdjagustin-lab.dev` and `dig +short grafana.jdjagustin-lab.dev`.
Verbatim output (in order, first command then second):
```
104.21.51.133
172.67.180.160
172.67.180.160
104.21.51.133
```
Facts:
- `lab.jdjagustin-lab.dev` resolves to 104.21.51.133 and 172.67.180.160; `grafana.jdjagustin-lab.dev` resolves to the same two addresses in the opposite order (the order of answers rotates between queries, normal DNS round-robin behavior). Neither answer shows the `cfargotunnel.com` name or any address of the author's network: a proxied record hides the real destination.
- The addresses are in the 104.21.x.x and 172.67.x.x ranges that Cloudflare uses for proxied sites (from my knowledge; can be checked against Cloudflare's published IP list, not done here).
- The new `lab` record is therefore live in public DNS about a minute after creation. Whether the page behind it works is NOT verified yet.

## E-043 — Screenshot: https://lab.jdjagustin-lab.dev serves the static "Lab site" page (13:34)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the browser bookmarks bar is personal and not transcribed).
Address bar: lab.jdjagustin-lab.dev; tab title "Lab site". Page content: heading "Lab site" and the paragraph "Temporary static page used for Cloudflare lab tests (cache, WAF, rate limiting)." The text is in a sans-serif font with a margin around it.
Facts (what it shows):
- The page from ~/lab-site on Cloudlab-1 (index.html, E-029) is reachable on the public hostname through Cloudflare and the tunnel. This also proves that cloudflared loaded the new ingress rule (E-031/E-032): without it the request would have hit the 404 catch-all.
- The page looks sans-serif with a margin, which matches style.css (`font-family: sans-serif; margin: 2rem`), so the stylesheet seems to have loaded too (visual inference; not checked in the network tab).
- No Cloudflare Access login screen appeared. This is NOT proof that Access does not cover this hostname: the author has an open Cloudflare session in this browser. To check without cookies: `curl -sI` from the terminal (a redirect to cloudflareaccess.com would mean Access applies).
- Lab Piece 1 status: DNS record created and live (E-041, E-042), proxied (E-042), page reachable (this entry). Still to read: the zone's SSL/TLS mode.

## E-044 — Access check without a Cloudflare session, as reported by the author (13:36) — NO SCREENSHOT
Source: the author's verbal report. After being asked to open https://lab.jdjagustin-lab.dev from a context without a Cloudflare session (private window, another browser or his phone), he says he also sees the "Lab site" page directly. Which of those options he used was not stated, and there is no screenshot.
Interpretation (limited to the report): if the test really had no Cloudflare session, the Access application does NOT cover `lab.jdjagustin-lab.dev`, so the hostname is public by design (it only serves a static page). The `curl -sI` check (no cookies at all) would confirm it with headers and is still planned as the first Piece 2 step.

## E-045 — Detail for E-044: the test was done in Google Chrome (13:38) — NO SCREENSHOT
Source: the author's verbal report: he opened https://lab.jdjagustin-lab.dev in Google Chrome, which does not have the Cloudflare dashboard open, and saw "Lab site" directly.
Interpretation: this is a different browser from the one used before, so it is a stronger test than the first one. Limit: "the dashboard is not open" is not the same as "no Cloudflare/Access session cookies": if Chrome had logged in to Cloudflare Access earlier, a stale session could still let it through. It is not a private window and there is no screenshot. The cookie-free `curl -sI` check remains the definitive one.

## E-046 — curl -sI from the author's Mac: headers of / and /style.css (terminal, 13:37 CST = 19:37 GMT)
Commands run by the author (Mac terminal, no cookies): `curl -sI https://lab.jdjagustin-lab.dev/` and `curl -sI https://lab.jdjagustin-lab.dev/style.css` (twice).
Output (verbatim; the long `report-to` and `nel` lines, which are Cloudflare's network-error-logging headers with a per-response signature, are trimmed here):
```
--- request 1: /
HTTP/2 200
date: Mon, 09 Nov 2026 19:37:28 GMT
content-type: text/html
last-modified: Mon, 09 Nov 2026 19:07:18 GMT
server: cloudflare
cf-cache-status: DYNAMIC
cf-ray: a57f45ae1bdd2526-DFW
alt-svc: h3=":443"; ma=86400
--- request 2: /style.css
HTTP/2 200
date: Mon, 09 Nov 2026 19:37:28 GMT
content-type: text/css
content-length: 48
last-modified: Mon, 09 Nov 2026 19:07:18 GMT
server: cloudflare
age: 262
accept-ranges: bytes
cache-control: max-age=14400
cf-cache-status: HIT
cf-ray: a57f45afea2c6c0e-DFW
alt-svc: h3=":443"; ma=86400
--- request 3: /style.css (identical to request 2: age 262, HIT, cf-ray a57f45b15850f676-DFW)
```
Facts (what the headers show):
1. Access does NOT cover `lab`: a cookie-free request got `HTTP/2 200` and the page headers, not a 302 to cloudflareaccess.com. This settles the open point from E-043/E-044/E-045 (the hostname is public by design).
2. The HTML is `cf-cache-status: DYNAMIC` (Cloudflare did not treat it as cacheable by default). The stylesheet is `HIT`.
3. The stylesheet was ALREADY cached on the first curl: `age: 262` seconds, which puts the moment it was cached at about 19:33:06 GMT = 13:33 CST, i.e. when the author first opened the page in his browser (E-043). So my earlier expectation of "MISS the first time, HIT the second" was wrong for this test, because the browser visits had already warmed the cache. A real MISS->HIT demo needs a URL not yet requested (for example adding a query string).
4. `cache-control: max-age=14400` (4 hours) appears on the cached response. The origin (Python http.server) sends no Cache-Control header (E-030 showed its headers: Server, Date, Content-type, Content-Length), so this value was added by Cloudflare; my understanding is that it is Cloudflare's default Browser Cache TTL (4 hours on the Free plan), not verified in this session.
5. `cf-ray` ends in `-DFW`: the three requests were served by a Cloudflare data center identified as DFW (Dallas area). `alt-svc: h3` shows HTTP/3 is offered. `last-modified` (19:07:18 GMT = 13:07 CST) matches when the files were created on Cloudlab-1 (E-029).
Not shown yet: the origin side (how many requests actually reached the Python server; /tmp/lab-site.log on Cloudlab-1), and a clean MISS->HIT sequence.

## E-047 — Clean cache MISS -> HIT demonstration (terminal, 13:43 CST)
Commands run by the author (Mac terminal): the same command twice, `curl -sI "https://lab.jdjagustin-lab.dev/style.css?test=1" | grep -i -E "^(HTTP|cf-cache-status|age)"`.
Verbatim output:
```
HTTP/2 200
cf-cache-status: MISS
HTTP/2 200
age: 0
cf-cache-status: HIT
```
Facts: the first request for a URL nobody had asked for (`?test=1`, the query string makes it a different cache key) was a `MISS`: Cloudflare had to fetch it from the origin and stored it. The second, immediately after, was a `HIT` with `age: 0` (the object had been in cache for less than a second). The MISS response carries no `age` header, the HIT does. This is the clean MISS->HIT sequence that E-046 could not show.
Not shown yet: the origin side. Prediction to test (not measured): the Python server on Cloudlab-1 received ONE request for `style.css?test=1` (the MISS), not two. Check: /tmp/lab-site.log on Cloudlab-1.

## E-048 — Origin log on Cloudlab-1: which requests actually reached the Python server (terminal, 13:50 CST)
Commands run by the author on Cloudlab-1: `cat /tmp/lab-site.log` and `wc -l /tmp/lab-site.log`.
Verbatim output (times are local CST; the client address is always 127.0.0.1 because cloudflared connects to the server locally):
```
127.0.0.1 - - [09/Nov/2026 13:09:17] "HEAD / HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 13:09:17] "GET /style.css HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 13:33:05] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 13:33:05] "GET /style.css HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 13:33:05] code 404, message File not found
127.0.0.1 - - [09/Nov/2026 13:33:05] "GET /favicon.ico HTTP/1.1" 404 -
127.0.0.1 - - [09/Nov/2026 13:33:31] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 13:36:27] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 13:36:28] code 404, message File not found
127.0.0.1 - - [09/Nov/2026 13:36:28] "GET /favicon.ico HTTP/1.1" 404 -
127.0.0.1 - - [09/Nov/2026 13:37:28] "HEAD / HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 13:43:14] "GET /style.css?test=1 HTTP/1.1" 200 -
12 /tmp/lab-site.log
```
Matching the log against what we did (this is the measurement that was only a prediction in E-027 and E-047):
- 13:09:17 HEAD / and GET /style.css: the two local curl tests on Cloudlab-1 (E-030), not through Cloudflare.
- 13:33:05 GET /, GET /style.css, GET /favicon.ico (404): the author's first browser visit (E-043). The /style.css request here is the MISS that populated Cloudflare's cache; it matches `age: 262` at 13:37:28 in E-046 (cached about 13:33:06).
- 13:33:31 and 13:36:27 GET /: further visits (13:36:27 is followed by a favicon 404, typical of a browser opening the site for the first time, probably the Chrome test, E-045; inference).
- 13:37:28 HEAD /: the first of the three curl requests in E-046 (HTML, `DYNAMIC`, always goes to the origin).
- ABSENT at 13:37:28: the two `curl -sI /style.css` requests, both `HIT` in E-046. They never reached the origin.
- 13:43:14 GET /style.css?test=1: exactly ONE line for the two requests of E-047 (MISS then HIT). The prediction held: only the MISS reached the origin, and Cloudflare turned the client's HEAD request into a GET to the origin (the origin saw GET, not HEAD).
Counts: 12 lines = 10 requests + 2 "code 404" detail lines. Of the 5 requests for style.css that we know went through Cloudflare (browser first visit, 2 curls, 2 curls with ?test=1), only the 2 MISSes (13:33:05 and 13:43:14) reached the origin. Every request for the HTML page we know of reached it (DYNAMIC).
Limits: browser visits at 13:33:31 and 13:36:27 may also have requested the stylesheet from Cloudflare (HIT, invisible here) or from the browser's own cache; not known. The log shows only 127.0.0.1, so the origin cannot see real visitor IPs (Cloudflare passes them in a header, not logged by this server).
Conclusion supported by evidence: cache HITs do not consume origin CPU on Cloudlab-1; HTML pages (DYNAMIC) do reach it.

## E-049 — Screenshot: SSL/TLS Overview of jdjagustin-lab.dev (13:58)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Page "SSL/TLS" (zone jdjagustin-lab.dev, plan badge free). Intro text: "Choose how Cloudflare encrypts traffic between your visitors and Cloudflare, and between Cloudflare and your origin server, to prevent data theft and other tampering." Button "Configure".
Panel "SSL/TLS encryption": "Current encryption mode: Full". Diagram: Browser -> (lock) -> Cloudflare -> (lock) -> Origin Server. Under it: "Automatic mode enabled · 66 days ago" and "Next automatic scan: Nov 17".
Panel "Traffic Served Over TLS (Last 24 hours)": TLS v1.3 = 136 (a full-width blue bar; no other TLS version is listed in the visible part).
Left menu under SSL/TLS: Overview, Edge Certificates, Client Certificates, Origin Server, Custom Hostnames. Other zone sections visible: Security, Access, Speed, Caching, Workers Routes.
Facts and interpretation:
- The zone's encryption mode is Full (Cloudflare connects to the origin over HTTPS without requiring a publicly valid certificate; "Full (strict)" would require one). The mode is managed by Automatic SSL/TLS, enabled about 66 days ago (around early September 2026, when the lab domain was set up; date arithmetic, not stated on screen), with the next automatic scan on Nov 17.
- In this lab the origin hop is not a classic HTTPS origin: Cloudflare reaches Cloudlab-1 through the tunnel and cloudflared talks plain HTTP to localhost (E-009, E-031). My understanding is that the SSL/TLS mode therefore does not change how the tunnel traffic is carried; this is NOT verified here and is not claimed.
- 136 requests served over TLS 1.3 in the last 24 hours: all visible traffic used TLS 1.3. The count includes today's tests (Grafana, lab site, curl). Visitors always use HTTPS on this domain; `.dev` domains are on the browsers' HTTPS-only (HSTS preload) list (my knowledge).
Lab Piece 1 is now complete: DNS record created (E-041), proxied and resolving to Cloudflare IPs (E-042), page reachable (E-043), zone SSL/TLS mode read: Full, Automatic mode (this entry).

## E-050 — Free plan limits for WAF custom rules and rate limiting (web search, 14:10)
Sources: Cloudflare docs, WAF overview (https://developers.cloudflare.com/waf/) and the legacy rate-limiting upgrade page (https://developers.cloudflare.com/waf/reference/legacy/old-rate-limiting/upgrade); Cloudflare blog "unmetered rate limiting" (https://blog.cloudflare.com/unmetered-ratelimiting/); third-party pricing comparisons (eastondev.com, cloud-pricing-tracker.pages.dev). Read through search snippets only.
- Rate limiting rules: Free = 1 rule (Cloudflare docs and blog; Pro 2, Business 5). Action Block returns HTTP 429 (Cloudflare legacy docs). Third-party comparison: on Free the period is limited to 10 seconds (not confirmed by Cloudflare's own pages I saw).
- WAF custom rules: available on all plans per the Cloudflare docs table; the NUMBER for Free is 5 according to two third-party comparisons (the snippet of Cloudflare's own page did not show the number). To verify in the dashboard: Security > WAF > Custom rules shows how many are used.
- Evaluation order (third-party article, consistent with Cloudflare's phases): custom rules run before rate limiting, which runs before managed rules; a request blocked by a custom rule never reaches the rate limiter.
- Managed rules on Free: the "Free Managed Ruleset" only.
Plan consequence for the lab: one custom rule scoped to the `lab` hostname, and the single rate limiting rule scoped to the `lab` hostname. No rule may apply to grafana.jdjagustin-lab.dev.
Caveat: pricing/limits pages change; the dashboard is the source of truth for this account.

## E-051 — "New custom rule" form filled in, before deploying (screenshot PDF, 14:10)
Source: PDF with two screenshots attached by the author (not on disk yet; transcribed here).
Page "New custom rule" in zone jdjagustin-lab.dev (plan badge free). Left menu now shows under Security: Overview, Analytics, Account Abuse Protection (Beta), Web assets, Security rules, Settings (the WAF rules live under "Security rules"; the menu differs from the "Security > WAF" path I gave from memory).
Fields:
- Rule name: `lab-block-blocked-path`.
- Expression: `(http.host eq "lab.jdjagustin-lab.dev" and http.request.uri.path eq "/blocked")` — counter "79 / 4000 characters" (the string is 79 characters, consistent).
- Preview: "Total requests matched 0 — 0.0% of all traffic - Last 30 days". The preview says no request in the last 30 days would have matched this rule, so it cannot affect Grafana or the lab page.
- Action: Block ("Blocks matching requests and stops evaluating other rules").
- Status: Disabled / Active radio buttons, both appear UNSELECTED in the screenshot.
- "Rule validation passed" with the Deploy button shown pale/greyed (probably until a Status is chosen; not confirmed).
- A "Deploy with API call" section shows the equivalent request: `curl -X PUT "https://api.cloudflare.com/client/v4/zones/<zone id, cut off>/..." -H "Authorization: Bearer $CF_AUTH_TOKEN" -d '{"rules":[{"description":"lab-block-blocked-path","expression":"(http.host eq \"lab.jdjag...","action":"block","enabled":true}]}'`; the page says an API Token with `Zone > Zone WAF` or broader permissions is required. Useful for lab Piece 5 (API/Terraform); NOT run.
Facts: the rule was NOT deployed at the time of the screenshot. Expected after deploying (to be tested): `/blocked` on the lab hostname answers 403 from Cloudflare's edge without reaching the origin; `/` still answers 200; grafana.* untouched.

## E-052 — Screenshot: Security rules page after deploying the custom rule (14:13)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Page "Security rules" (tabs: Security rules, DDoS protection) of zone jdjagustin-lab.dev (plan badge free). A blue info banner reads: "Cloudflare is helping protect jdjagustin-lab.dev against php2shell ... Cloudflare has deployed rules that help block known php2shell attacks. This reduces your risk but doesn't fix the vulnerabilities in PHP. We recommend updating PHP to a patched version." (generic notice; not something done in this lab; the lab serves no PHP).
Custom rules "1/5 rules": row Order 1 | Name `lab-block-blocked-path` | Description "Hostname equals lab.jdjagustin-lab.dev and URI Path equals /blocked" | Action Block | CSR "-" | Events (empty at the time).
Rate limiting rules "0/1 rules": "No Rate limiting rules created".
Facts:
- The custom rule exists in the list with the intended description and action Block. The list does not show whether its status is Active; the curl test will show it.
- Plan limits are now confirmed by the account itself: custom rules 5 per zone (1 used) and rate limiting rules 1 per zone (0 used). This resolves the uncertainty in E-050 (the "5" came from third-party sources; the dashboard shows 1/5).
- The Events column is empty because no request has matched yet (or none has been counted yet).
Not yet verified: that the rule blocks `/blocked` on the lab hostname (expected 403 from the edge), that `/` still returns 200, and that the origin log has no `/blocked` line.

## E-053 — curl test of the custom rule: /blocked answers 403 from Cloudflare, / still 200 (terminal, 14:14 CST = 20:14 GMT)
Commands run by the author (Mac terminal): `curl -sI https://lab.jdjagustin-lab.dev/blocked` and `curl -sI https://lab.jdjagustin-lab.dev/`.
Output (verbatim, long `report-to`/`nel` lines trimmed as in E-046):
```
--- /blocked
HTTP/2 403
date: Mon, 09 Nov 2026 20:14:15 GMT
content-type: text/html; charset=UTF-8
cache-control: private, max-age=0, no-store, no-cache, must-revalidate, post-check=0, pre-check=0
expires: Thu, 01 Jan 1970 00:00:01 GMT
referrer-policy: same-origin
x-frame-options: SAMEORIGIN
server: cloudflare
cf-ray: a57f7b92af30552a-DFW
alt-svc: h3=":443"; ma=86400
--- /
HTTP/2 200
date: Mon, 09 Nov 2026 20:14:15 GMT
content-type: text/html
last-modified: Mon, 09 Nov 2026 19:07:18 GMT
server: cloudflare
cf-cache-status: DYNAMIC
cf-ray: a57f7b93fe3f806d-DFW
alt-svc: h3=":443"; ma=86400
```
Facts:
- The custom rule is ACTIVE and works: a request to /blocked on the lab hostname got `HTTP/2 403`. The headers (no `last-modified`, `cache-control: no-store ...`, `referrer-policy`, `x-frame-options`, `expires` in 1970) are those of a page generated by Cloudflare, not by the Python server (whose responses carry `last-modified`, see the second request and E-030). This is a header-based inference; the page body was not read.
- The normal page is unaffected: `/` still returns `200` with `cf-cache-status: DYNAMIC`, as in E-046.
- Both requests were handled by a data center whose `cf-ray` ends in DFW. Times: `date` 20:14:15 GMT = 14:14:15 CST.
Not verified yet: that the origin never saw the /blocked request (check /tmp/lab-site.log on Cloudlab-1; prediction: no /blocked line, only a HEAD / at 14:14:15), and the event in the dashboard's security events view.

## E-054 — Origin log after the WAF test: the blocked request never reached Cloudlab-1 (terminal, 14:17 CST)
Commands run by the author on Cloudlab-1: `grep -c "blocked" /tmp/lab-site.log` and `tail -n 3 /tmp/lab-site.log`.
Verbatim output:
```
0
127.0.0.1 - - [09/Nov/2026 13:37:28] "HEAD / HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 13:43:14] "GET /style.css?test=1 HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 14:14:15] "HEAD / HTTP/1.1" 200 -
```
Facts: zero lines in the origin log contain "blocked", and the last request in the log is the `HEAD /` of 14:14:15, the second curl of E-053 (the normal page). The `/blocked` request of the same second (E-053) is NOT in the log: Cloudflare answered the 403 at its edge and never forwarded it to the Python server. The prediction made in E-053 held, and it is the same mechanism measured for cache HITs in E-048: requests answered at the edge cost Cloudlab-1 nothing.
Limit: the log proves the request did not reach the origin; the 403 page body was not read.
Pending: see the same request as an event in the dashboard's security analytics (rule name, action, host, path).

## E-055 — Security Events: the blocked request seen in the dashboard (PDF with screenshots, 14:23)
Source: PDF attached by the author (not on disk yet; transcribed here; his public IP is masked).
Page: zone jdjagustin-lab.dev > Security > Analytics > tab "Events" (tabs: Traffic, Events). Section "Security Events" with Filter, a time window set to "Last 2 hours" and a "Create security rule" button; below, "Sampled logs" with one event expanded.
Event details (as shown):
- Action: Block. Matched service: Custom rules. Action taken: Block.
- Request details: Ray ID `a57f7b92af30552a`; IP address <public IP, masked>; ASN AS<n> [as typed in the PDF text; the JSON export in E-056 says <n>] <ISP>; User agent `curl/8.7.1`; HTTP Version HTTP/2. The date/time column shows GMT but its value is cut off in the capture.
Facts:
- The Ray ID `a57f7b92af30552a` is exactly the `cf-ray` of the 403 response to `/blocked` in E-053. A response header in the terminal can therefore be tied to its event in the dashboard: this is the troubleshooting workflow (customer gives the Ray ID, support finds the event, the rule that fired and the action).
- The event names the service that acted (Custom rules) and the action (Block), and shows who asked (country, network, client). The rule name, host and path are not in the visible part of the capture (only the expanded fields listed above are).
- The IP written in the PDF text looks truncated or mistyped (<ip>, while the ASN is a Mexican residential provider); the tunnel's origin IP in E-007 was in the <public-ip> block. It is plausible that both are the author's home public address (the Mac and Cloudlab-1 share the same home connection), but the PDF text does not confirm it, so it is NOT claimed here.
- "Sampled logs": this view shows a sample of events, not necessarily every request.
Piece 2 status: custom rule proven at the client (E-053), at the origin (E-054) and in the dashboard (this entry). Still to do: the single rate limiting rule on the `lab` hostname.

## E-056 — Firewall events exported as JSON: the raw record of the blocked request (file attached by the author, 14:25 CST)
Source: file `firewall-events-2026-11-08T20_21_05Z-2026-11-09T20_21_05Z.json` (Security > Analytics > Events export, window 2026-11-08 20:21 to 2026-11-09 20:21 UTC). A copy with the public IP masked is saved in `evidence/firewall-events_2026-11-08T2021Z_to_2026-11-09T2021Z_masked.json`.
Content: ONE event in the 24-hour window. Key fields: action `block`; source `firewallCustom` (a custom rule); description `lab-block-blocked-path` (the rule name); clientRequestHTTPHost `lab.jdjagustin-lab.dev`; clientRequestPath `/blocked`; method `HEAD` (curl -I); protocol HTTP/2; datetime `2026-11-09T20:14:15Z`; rayName `a57f7b92af30552a`; userAgent `curl/8.7.1`; clientCountryName MX; clientASNDescription "<ISP>n `<n>`; ruleId and rulesetId (identifiers of the rule and its ruleset); matchIndex 0; sampleInterval 1.
Facts:
- Everything in the dashboard event (E-055) is confirmed by the raw record, and the missing details are now visible: the rule that fired (`lab-block-blocked-path`), the host, the path, the method and the exact time. The rayName equals the `cf-ray` of the 403 in E-053, and datetime equals the `date` header (20:14:15 GMT).
- Correction to E-055: the ASN is <n> (the PDF text said AS<n>, a transcription slip) and the client IP is `<public-ip> (masked)` in the JSON (the PDF text showed <ip>). That IP is the same as the tunnel's "Origin IP" in E-007 (<public-ip> (masked)), compared by reading both values: the author's Mac and Cloudlab-1 reach the internet through the same home public address. Cloudflare sees the real client address; the Python server never does (it only logs 127.0.0.1, E-048).
- `sampleInterval: 1` means this record stands for exactly one request (nothing was sampled out). It is the only blocked request in the last 24 hours.
- Useful as a deliverable: the JSON can go (masked) into the future repo as an example of a security event export.

## E-057 — Screenshot: the block page a visitor sees in the browser (14:25)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the browser bookmarks bar is personal and not transcribed).
Browser address bar shows `lab.jdjagustin-lab.dev` (the path is not displayed by the browser; it is presumably /blocked, since the author opened the blocked URL; inference). Tab title: "Attention Required! | ..." (cut off). Page: heading "Sorry, you have been blocked", subtitle "You are unable to access jdjagustin-lab.dev", an illustration with a red X over a browser window, and two headings at the bottom, "Why have I been blocked?" and "What can I do to resolve this?". The rest of the page (where Cloudflare normally prints the Ray ID and client IP) is below the visible part of the screenshot.
Facts: the body of the 403 is Cloudflare's standard block page, which settles the limit noted in E-053/E-054 ("page body not read"). It is served by Cloudflare, not by the lab server. In support practice a visitor reports the Ray ID printed on this page, which can then be looked up in Security Events (E-055/E-056 showed that link for the curl request). Not verified: the Ray ID/IP at the bottom of the page and the exact path (not visible); this browser request would also appear as a second event in Security Events.

## E-058 — Screenshot: bottom of the block page with Ray ID (14:28) and the author's confirmation that the URL was /blocked
Source: screenshot pasted in chat (not on disk yet; transcribed here; the visitor IP printed on the page is masked) plus the author's reply "si, asi fue" confirming he opened the blocked path. This confirms the inference in E-057.
Page text (paraphrased): "Why have I been blocked?" explains in generic terms that the site uses a security service, that the action performed triggered it, and that many things can trigger the block, including submitting a certain word or phrase, a SQL command or malformed data. "What can I do to resolve this?" tells the visitor to email the site owner, saying what they were doing and including the Cloudflare Ray ID shown at the bottom of the page.
Footer (verbatim except the IP): "Cloudflare Ray ID: a57f8f0e8d9ff2f0 • Your IP: <public-ip> (masked) • Performance & security by Cloudflare".
Facts and limits:
- The Ray ID of this browser request, `a57f8f0e8d9ff2f0`, is different from the one of the earlier curl request (`a57f7b92af30552a`, E-053/E-055/E-056): it is a new request, so it should be a second event in Security Events. Not looked up yet.
- The page does NOT say which rule fired or why; the visitor only gets the Ray ID and their IP. The reason (rule name, host, path) is visible only to the site owner in Security Events (E-056 showed it for the curl request). This is the support workflow of the role: the visitor reports the Ray ID, the engineer finds the event and the rule.
- The printed IP is the same address as in E-056 (compared by reading both).
Optional check offered: search this Ray ID in Security Events (Filter) to reproduce the full support workflow.

## E-059 — Support workflow reproduced: the Ray ID from the block page found in Security Events (screenshot + JSON, 14:49 CST)
Source: screenshot of Security > Analytics > Events and the file `firewall-events-2026-11-08T20_32_27Z-2026-11-09T20_32_27Z.json` attached by the author; masked copy of the event in `evidence/firewall-event_ray-a57f8f0e8d9ff2f0_browser-GET-blocked_masked.json` (public IP masked).
What the author did: in Security Events he filtered by "Ray ID = a57f8f0e8d9ff2f0" (the Ray ID printed on the block page, E-058), window "Last 24 hours".
Event found (screenshot): Date 2026-11-09 14:27:33 GMT-6 | Action taken Block | Country Mexico | IP <masked> | Service Custom rules. Expanded: Matched service: Service "Custom rules", Action taken Block, Ruleset "default" (id <id>), Rule "lab-block-blocked-path" (link, id <id>). Request details: Ray ID a57f8f0e8d9ff2f0; ASN AS<n> <ISP>; User agent Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 ... Version/26.6.2 Safari/605.1.15; HTTP Version HTTP/2; Referer None (direct); Method GET; Host lab.jdjagustin-lab.dev; Path /blocked; Query string empty. There is an "Export event JSON" link and an "Export" button.
JSON: same values (datetime 2026-11-09T20:27:33Z = 14:27:33 CST, method GET, rayName a57f8f0e8d9ff2f0, source firewallCustom, description lab-block-blocked-path, same ruleId/rulesetId as E-056).
Facts:
- The full support workflow is now reproduced end to end with a browser: the visitor sees the block page and its Ray ID (E-057/E-058) -> the engineer filters Security Events by that Ray ID -> finds the event, the rule that fired (name and id), the action, host, path, method, client and network.
- Comparison with the first event (E-056): same rule, same path; different method (HEAD vs GET), different client (curl/8.7.1 vs Safari) and different Ray ID. Two blocked requests in total so far.
- The dashboard displays the time converted to the author's time zone (GMT-6) while the JSON uses UTC (Z).

## E-060 — "New rate limiting rule" form filled in, before deploying (screenshot, 14:56)
Source: screenshot pasted in chat (not on disk yet; transcribed here; zone id masked).
Page: Security rules > New rate limiting rule (zone jdjagustin-lab.dev, plan free).
- Rule name: `lab-ratelimit-test`.
- Expression: `(http.host eq "lab.jdjagustin-lab.dev" and http.request.uri.path eq "/ratelimit-test")`, "86 / 4000 characters" (consistent with the 79 characters of the WAF rule plus 7 more for the longer path).
- "With the same characteristics...": IP (the field looks greyed out/not editable on this plan).
- "When rate exceeds...": Requests 5, Period 10 seconds.
- "Then take action...": Block ("Blocks matching requests and stops evaluating other rules").
- "For duration...": Duration 10 seconds.
- Status: Active selected (Disabled not selected).
- "Rule validation passed"; the Deploy button is enabled (blue).
- "Deploy with API call" shows the equivalent PUT request to `https://api.cloudflare.com/client/v4/zones/<zone id ...0b54f>/rulesets/phases/ht...` (URL cut off) with the rule in JSON: `"ratelimit": {"characteristics": ["ip.src", "cf.colo.id"], "period": 10, "requests_per_period": 5, "requests_to_origin": false, "mitigation_timeout": 10}`, `"description": "lab-ratelimit-test"`, the expression, `"action": "block"`, `"enabled": true`. Needs a token with `Zone > Zone WAF` or broader permissions. NOT run (lead for lab Piece 5).
Facts and nuances:
- The dashboard shows the characteristic as "IP", but the API sample shows the counting key is TWO fields: `ip.src` AND `cf.colo.id`: the count is kept per client IP per Cloudflare data center, not globally. For the test from one location it behaves as per-IP because all requests go to the same data center (DFW so far). My reading of the JSON; the UI does not say it in words.
- `requests_to_origin: false`: the rule counts every request that matches the expression (also those that end in 404 at the origin), not only requests forwarded to the origin.
- Period 10 s and duration 10 s are the values selected; whether other values are selectable on Free was not shown (the earlier third-party claim of a 10-second cap is consistent with this form but not proven by it).
- Not deployed at the time of the screenshot. Expected after deploying: the first requests to /ratelimit-test return 404 from the origin (the file does not exist); once the rate exceeds 5 per 10 s from the same IP, Cloudflare answers 429 at the edge for 10 seconds; the origin log shows only the requests that were let through.

## E-061 — Screenshot: the rate-limit test loop stuck at the `for>` prompt (15:00)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Terminal (Mac, a zsh-style prompt) shows: `for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null -w "%{http_code} " https://lab.jdjagustin-lab.dev/ratelimit-test\; done; echo` followed by a continuation prompt `for>`.
Facts: the shell inserted a backslash before the `;` that follows the unquoted URL (`...ratelimit-test\;`), so the `;` no longer ended the curl command and `done` was never reached; the shell is waiting for the rest of the loop. No request was sent.
Likely cause (my reading, not verified): a zsh feature that escapes special characters in unquoted URLs when text is pasted (url-quote-magic style). Fix: wrap the URL in double quotes (as in the earlier `?test=1` commands, which worked) and press Ctrl+C to cancel the pending input. Lesson for the runbook: always quote URLs in shell commands.
Not known yet: whether the rate limiting rule was already deployed (the author has not said).

## E-062 — Second attempt: the shell still inserts the backslash, even with the URL in quotes (screenshot, 15:03)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Terminal shows the command with the URL in double quotes: `... "https://lab.jdjagustin-lab.dev/ratelimit-test"\; done; echo` and again the continuation prompt `for>`. The `;` after the closing quote received a backslash. The earlier prompts in the screenshot are red (the previous input was cancelled or failed).
Facts: quoting the URL did NOT prevent the escaping (this corrects the fix suggested in E-061, which was wrong). The terminal adds a `\` before a `;` that comes right after a URL in the pasted line. No request was sent.
Next fix: keep the URL out of the line that contains the `;`: put it in a shell variable on its own line (`url="..."`) and use `"$url"` in the loop; cancel the pending input with Ctrl+C first.
Runbook lesson (revised): in this terminal, avoid `;` right after a URL; use a variable or separate lines.

## E-063 — Rate limit test: 404 x5 then 429 x5 (terminal screenshot) + Security rules page (screenshot, 15:05 CST)
Source: two screenshots pasted in chat (not on disk yet; transcribed here).
Terminal (Mac): commands `url="https://lab.jdjagustin-lab.dev/ratelimit-test"` and `for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null -w "%{http_code} " "$url"; done; echo`. Output:
```
404 404 404 404 404 429 429 429 429 429
```
(The variable trick worked: no backslash was inserted this time, which confirms the diagnosis in E-062.)
Security rules page: Custom rules "1/5 rules": `lab-block-blocked-path` (order 1, Block, description "Hostname equals lab.jdjagustin-lab.dev and URI Path equals /blocked"). Rate limiting rules "1/1 rules" with an amber warning triangle next to the count and an "Upgrade plan" button: `lab-ratelimit-test` (order 1, Block, description "Hostname equals lab.jdjagustin-lab.dev and URI Path equals /ratelimit-test"). Managed rules: "No Managed rules created" (Upgrade plan button). Response rules: "Cloudflare default protection applied — Responses from your origin are protected by Cloudflare's default rules ... php2shell protection" with an "Edit configuration" button. The Events column of both rules is empty in the capture.
Facts (what the output shows):
- The rate limiting rule is deployed and ACTIVE and behaves as designed: the first five requests got 404 (the file /ratelimit-test does not exist, so this is the Python server answering) and the next five got 429 ("Too many requests", the status Cloudflare uses for rate limit Block). The change happened exactly at the threshold of 5 requests in 10 seconds from the same IP.
- Free plan capacity is used up for rate limiting (1/1) and one custom rule of five is used (1/5). The amber triangle next to 1/1 most likely just flags that the quota is full; the screenshot does not say so.
Not verified yet: that the five 429 never reached the origin (prediction: the origin log has only the 5 requests that returned 404); the events of the 429 in Security Events.

## E-064 — Origin log after the rate limit test: only 5 of the 10 requests reached Cloudlab-1 (terminal, 15:11 CST)
Commands run by the author on Cloudlab-1: `grep "ratelimit-test" /tmp/lab-site.log` and `grep -c "ratelimit-test" /tmp/lab-site.log`.
Verbatim output:
```
127.0.0.1 - - [09/Nov/2026 15:04:55] "GET /ratelimit-test HTTP/1.1" 404 -
127.0.0.1 - - [09/Nov/2026 15:04:55] "GET /ratelimit-test HTTP/1.1" 404 -
127.0.0.1 - - [09/Nov/2026 15:04:56] "GET /ratelimit-test HTTP/1.1" 404 -
127.0.0.1 - - [09/Nov/2026 15:04:56] "GET /ratelimit-test HTTP/1.1" 404 -
127.0.0.1 - - [09/Nov/2026 15:04:56] "GET /ratelimit-test HTTP/1.1" 404 -
5
```
Facts: exactly 5 requests for /ratelimit-test reached the Python server, all answered 404, within about two seconds (15:04:55-15:04:56); there is no 429 line in the origin log. The client sent 10 (E-063): the other 5 received 429 from Cloudflare's edge and were never forwarded. The prediction of E-063 held (5, not 10). Origin load avoided by the rate limit in this test: half of the requests, and it would grow with the size of a flood (reasoning; only this 10-request test was measured).
Limit: Cloudflare's counting is approximate, so the exact threshold crossing can vary between runs; this is one run.

## PIECE 2 SUMMARY (written 15:12 CST)
Cache: HTML DYNAMIC, CSS MISS -> HIT, HITs absent from the origin log (E-046, E-047, E-048). Custom WAF rule: 403 at the edge, absent from the origin log, visible in Security Events by Ray ID and in a JSON export (E-053..E-059). Rate limiting: 404 x5 then 429 x5, only 5 requests at the origin (E-063, E-064). All of it scoped to the `lab` hostname; Grafana untouched. Free plan quotas now used: custom rules 1/5, rate limiting 1/1.

## E-065 — Docs check for Piece 3: Google as identity provider and path-scoped Access applications (web search, 15:20 CST)
Sources: Cloudflare docs "Google" identity provider (https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/google/ and the older path /cloudflare-one/identity/idp-integration/google), "Application paths" (https://developers.cloudflare.com/cloudflare-one/policies/access/app-paths/), "Publish a self-hosted application to the Internet" (https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/). Read through search snippets only.
Google IdP (per the docs):
- No Google Workspace account is needed; a Google Cloud project is used only to create an OAuth client.
- In Google Cloud: create an OAuth client of type "Web application"; Authorized JavaScript origins = `https://<team-name>.cloudflareaccess.com`; Authorized redirect URI = `https://<team-name>.cloudflareaccess.com/cdn-cgi/access/callback`. Google then shows a Client ID and a Client secret (the secret works like a password and must not be shared).
- In Cloudflare: Zero Trust > Integrations > Identity providers > Add new identity provider > Google; paste Client ID (called "App ID" in the dashboard) and Client secret; then use "Test" next to the provider (it should return the user identity). The team name is under Settings > Team name and domain.
- Troubleshooting noted: "Error 401: deleted_client" appears if the OAuth client was deleted in Google.
- the author's team domain, seen on the Access login page in E-013: `<team-name>.cloudflareaccess.com` (so the redirect URI would be that host plus /cdn-cgi/access/callback).
Path-scoped applications (per the docs): an Access self-hosted application can be defined by hostname AND path; path rules are inherited by sub-paths unless a more specific rule exists; a wildcard in the Path field (e.g. `example.com/alpha/*`) does not cover the parent path (`example.com/alpha`); query strings are not supported in application paths. Dashboard route: Zero Trust > Access controls > Applications > Create new application > Self-hosted and private > Add public hostname.
Standard: Google login is OpenID Connect (OIDC) based (my knowledge; the docs snippets above say "OIDC identity provider" for Google Workspace).
DEVIATION 6 (decided to keep the change small): instead of a second hostname (which would need another ingress rule, another cloudflared restart and another DNS record), protect the path `/private` of the existing `lab.jdjagustin-lab.dev` hostname with an Access application. Static file `private/index.html` created locally in ./site/private (E-065 file, not yet on Cloudlab-1). Cloudflared and DNS stay untouched; only a new page is added to ~/lab-site.

## E-066 — Piece 3 step A: the private page exists on Cloudlab-1 and is served locally (terminal, 15:19 CST)
Commands run by the author on Cloudlab-1: `mkdir -p ~/lab-site/private`, `cat > ~/lab-site/private/index.html <<'EOF' ... EOF` (same content as ./site/private/index.html, E-065) and `curl -s http://127.0.0.1:8081/private/`.
Output: the curl printed the HTML just written (doctype, head with title "Private area" and link to /style.css, body with the heading "Private area" and the paragraph "Temporary page behind Cloudflare Access, used for the lab identity provider test."). No error.
Facts: the static server serves /private/ from the new folder without restart. The page is still public at this point: no Access application exists yet, so https://lab.jdjagustin-lab.dev/private/ currently answers like any other path (not tested from outside; expected).
Cleanup: ~/lab-site (including private/) is already in the private cleanup checklist item 2.

## E-067 — Screenshot: Google Auth Platform after the OAuth configuration was created (15:31 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the profile picture and account details are not transcribed).
Google Cloud console, project `lab-cloudflare-access` (the project name chosen for this lab), breadcrumb "Google Auth Platform / Overview", page "OAuth Overview". A toast says "OAuth configuration created!". Left menu: Overview, Branding, Audience, Clients, Data Access, Verification Center, Settings. Metrics panel: "You haven't configured any OAuth clients for this project yet." with a "Create OAuth client" button. Project Checkup: "No project health recommendations found for your project." A banner at the top offers a free trial with $300 in credit (Dismiss / Start free).
Facts: the project and the OAuth consent configuration (branding/audience) exist; no OAuth client exists yet. In this newer console there is no "Credentials" menu item in this view: the OAuth client is created from "Create OAuth client" (also reachable through "Clients"), which matches the Cloudflare docs snippet ("On the OAuth overview screen, select Create OAuth client", E-065). The free-trial banner is not needed for this lab (no billing should be enabled).
Still to check by the author: Audience shows the app as an External app in Testing with his Gmail listed as a test user (needed for the login to work while the app is in testing).

## E-068 — Screenshot: Zero Trust Settings > Team domain, confirming the team name (15:39 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here). the author reached it with the dashboard quick search ("settings"), because he could not find the menu.
Page "Settings" ("Manage your Cloudflare One account, plan, and preferences."), section "Team domain": text explaining that the team domain is where users enroll devices with the Cloudflare One Client and access protected applications, and that changing the subdomain requires updating the identity providers and the client on all devices. Team name `<team-name>` (with an Edit link); Full domain `<team-name>.cloudflareaccess.com` (with a copy button). Right-hand "On this page": Team domain, Downloads, Admin controls, Plan, Permissions. Left menu under Zero Trust: Overview, Insights & Logs, Team & Resources, Access controls (more items below, not visible).
Facts: the team domain is confirmed by the dashboard itself: `<team-name>.cloudflareaccess.com`, identical to the one read from the Access login page in E-013. The redirect URI to register in Google is therefore `https://<team-name>.cloudflareaccess.com/cdn-cgi/access/callback` (format from the Cloudflare docs, E-065) and the JavaScript origin is `https://<team-name>.cloudflareaccess.com`.
Navigation note: the Settings page lives inside the Zero Trust section (not the zone menu); the dashboard quick search finds it. The Zero Trust menu has more entries below "Access controls" (Integrations is expected there; not seen yet).

## E-069 — Screenshot: "Create OAuth client ID" form in Google, filled in, before pressing Create (15:45 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Google Cloud, project `lab-cloudflare-access`, breadcrumb "Google Auth Platform / Clients / Create client", page "Create OAuth client ID". Visible fields:
- Authorized JavaScript origins, URIs 1: `https://<team-name>.cloudflareaccess.com`.
- Authorized redirect URIs, URIs 1: `https://<team-name>.cloudflareaccess.com/cdn-cgi/access/callback`.
- A checkbox "Use this client for an AI-powered agent" (unchecked in the screenshot; the author said he intended to tick it, advice given: leave it unticked, see below).
- Note on the page: "It may take 5 minutes to a few hours for settings to take effect". Buttons: Create, Cancel.
The Application type field is above the visible part of the screenshot (not seen; the presence of JavaScript origins and redirect URI fields is consistent with "Web application").
Facts: both URIs equal the values required by the Cloudflare docs (E-065) and the team domain confirmed in E-068, compared character by character. The "AI-powered agent" option is not part of the Cloudflare Access setup in the docs I read; its effect was not verified, and nothing in this lab needs it.
Practical consequence: after creating the client, the first Test in Cloudflare may fail with a redirect or "client not found" error for a few minutes because of the delay noted by Google.

## E-070 — Detail for E-069: Application type confirmed as Web application (15:46 CST) — NO SCREENSHOT
Source: the author's report ("si dice web application"). The part of the form that was cut off in E-069 shows Application type = Web application. Whether he left the "AI-powered agent" box unticked was not stated.

## E-071 — Google IdP created; first Test failed: "User email was not returned" (screenshot, 15:57 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the numeric Google user id is masked).
the author created the OAuth client in Google and the Google identity provider in Cloudflare, then ran Test. Result page (dark theme): "Cloudflare Access" logo; red exclamation icon; heading "Failed to get your identity"; subtitle "Looks like something went wrong. Here are the details."; a code box with the text: `User email was not returned. API permissions are likely incorrect.` followed by a JSON object with two fields: `"id": "<21-digit Google user id, masked ...4376>"` and `"name": "<name>"`.
Facts (what it shows):
- The Google side of the login worked: Google authenticated the author and returned his account id and display name to Cloudflare. What is missing is the email claim, which Cloudflare needs for policies that match on email.
- Cloudflare's own message points to permissions: in the Google OAuth flow this usually means the scopes that return the email address were not granted or not configured (my reasoning; checked against docs in the next step).
- The first part of the chain (redirect URI, client id and secret) is therefore correct: otherwise the error would have been a redirect or client error before any identity came back.

## E-072 — Docs search for the "User email was not returned" error (web search, 16:03 CST)
Sources searched: Cloudflare docs "Troubleshooting Access" (https://developers.cloudflare.com/cloudflare-one/troubleshooting/access and /access-controls/troubleshooting) and a general web search.
Result: the Cloudflare troubleshooting pages list a similar but different message ("Failed to fetch user/group information from the identity provider", caused by missing API permissions with the IdP) and others (SAML, OTP, Google Workspace redirect loop, Google Super Admin). I did NOT find this exact message ("User email was not returned. API permissions are likely incorrect.") documented.
Consequence: the fix proposed next is a hypothesis based on how Google OAuth/OIDC works, not on a Cloudflare document: Google returns the email address only when the `email` scope was requested and granted; Cloudflare's own text says "API permissions". Hypotheses, in order: (1) the consent configuration lacks the standard sign-in scopes (openid, email, profile) in the Data Access page; (2) the author's earlier consent (given before scopes were set) is cached by Google, so a new consent is needed; (3) the email permission was left unticked on Google's consent screen. Verification: change one thing, run Test again, record the result.

## E-073 — Screenshot: Google "Update selected scopes" panel with no scope selected (16:01 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Panel with an info banner: "Only scopes for enabled APIs are listed below. To add a missing scope to this screen, find and enable the API in the Google API Library or use the Pasted Scopes text box below. Refresh the page to see any new APIs you enable from the Library." A filterable table (31 scopes, 10 per page) with columns API, Scope, User-facing description, and a checkbox per row. The first three rows, all UNCHECKED: `.../auth/userinfo.email` ("See your primary Google Account email address"), `.../auth/userinfo.profile` ("See your personal info, including any personal info you've made publicly available"), `openid` ("Associate you with your personal info on Google"). Further rows (all unchecked) are Google Cloud / BigQuery / App Topology scopes such as `.../auth/bigquery` and `.../auth/cloud-platform`.
Facts: the project had no scopes declared (consistent with hypothesis 1 of E-072). The three basic sign-in scopes are the first rows and the only ones this lab needs; the other scopes in the list are unrelated cloud-data permissions and must NOT be selected (they are broader, and some Google scopes of that kind trigger app verification requirements).
Next: tick those three rows, press the update button of the panel (not visible in the capture) and save on the Data Access page, then revoke the earlier grant (E-072 step 2) and run the Test again.

## E-074 — Screenshot: Google Account "Sign in with Google" connections list (16:04 CST)
Source: screenshot pasted in chat (not on disk yet). Only the entries relevant to this lab are transcribed; the other entries are unrelated personal accounts and are intentionally not recorded.
Google Account > third-party connections, filter chip "Sign in with Google (23)" (other tabs: "Access to (10)", "Linked account (0)"). Relevant entries visible: "Cloudflare Dashboard" (Cloudflare logo) and "cloudflareaccess.com" (generic icon).
Interpretation (limited): the entry `cloudflareaccess.com` is the connection created by the Cloudflare Access test login with the new Google OAuth client (E-071), which Google granted without the email scope. Removing it forces a new consent screen on the next Test. The entry "Cloudflare Dashboard" is a separate connection, most likely how the author signs in to the Cloudflare dashboard with Google (inference from the name; not verified): it must NOT be removed.
Pending: confirm that the three scopes (openid, userinfo.email, userinfo.profile) were saved in Google Auth Platform > Data Access BEFORE removing the connection, otherwise the new consent would again lack the email.

## E-075 — Screenshot: the existing Google grant for cloudflareaccess.com shares only "profile info" (16:06 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Google Account page "cloudflareaccess.com" with an illustration, then a card "How Google helps you sign in to cloudflareaccess.com": "Sign in with Google — When you use Sign in with Google to sign in to your cloudflareaccess.com account, you're sharing some sensitive info with cloudflareaccess.com", listing ONE item: "See your profile info" (button "See details"). Below, a second card "Delete all — Remove all links and stop sharing your Google Account data with cloudflareaccess.com".
Facts: the grant that Google recorded for this connection lists only "See your profile info"; the email address is not listed. This agrees with the Cloudflare error in E-071 (name and id returned, email missing) and supports the scopes hypothesis of E-072/E-073: the first consent was given without the email scope. "Delete all" removes only the connection with cloudflareaccess.com (the Access login); it does not delete any data of the Google account and does not affect the "Cloudflare Dashboard" connection.
Next: delete this connection, make sure the three scopes are saved in Data Access, run the Test again and check that the consent screen now mentions the email address.

## E-076 — Screenshot: "How Google helps you sign in to cloudflareaccess.com" detail page, and a CORRECTION to E-075 (16:07 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Page text: "Sign in with Google — You use Sign in with Google to sign in to your cloudflareaccess.com account. Google uses your name, email address, and profile picture to securely sign you in. Learn more". "Access given on: 11 minutes ago". "Access given to: cloudflareaccess.com". "If you stop using Sign in with Google — If cloudflareaccess.com uses automatic sign-in, Google will no longer automatically sign you in to cloudflareaccess.com" with a button "Stop using Sign in with Google". A second card says cloudflareaccess.com uses Google Account sign-in prompts (settings link) and a footer "See something suspicious? Report this app".
Facts and correction:
- "Access given 11 minutes ago" (about 15:56 CST) matches the time of the first Test (E-071).
- CORRECTION: in E-075 I read "See your profile info" as meaning the email was not included in the grant. That reading was too strong: this page says, in generic wording that Google shows for every "Sign in with Google" connection, that Google uses name, email address and profile picture. So Google's screens do NOT prove that the email scope was missing. The scopes hypothesis (E-072/E-073: nothing declared in Data Access) is still a plausible cause and still the cheapest thing to fix, but it is NOT confirmed.
- The button on this page, "Stop using Sign in with Google", is described only in terms of automatic sign-in; it is not the same action as "Delete all" on the previous page ("Remove all links and stop sharing your Google Account data"). To force a brand-new consent, "Delete all" is the right action.
Plan unchanged but time-boxed: (1) make sure the 3 scopes are saved in Data Access, (2) Delete all for cloudflareaccess.com, (3) re-run Test. If the email is still missing, stop looking in Google's screens and decide between checking the Cloudflare side of the Google IdP and falling back to GitHub (OAuth 2.0).

## E-077 — Second Test after scopes + connection removal: same error, but Google's own email says the email WAS shared (screenshot + PDF, 16:15 CST)
Source: screenshot and a 2-page PDF of an email from Google attached by the author (not on disk yet; transcribed here; the author's Google user id and Gmail are masked).
the author reports that steps 1, 2 and 3 of the plan were done (scopes saved in Data Access, connection removed with "Delete all", Test repeated) and the Test still fails.
Cloudflare result (screenshot): the same page as E-071, "Failed to get your identity" with `User email was not returned. API permissions are likely incorrect.` and the JSON with only `"id"` (masked ...4376, the same id as before) and `"name": "<name>"`.
Google email (PDF): subject "You shared some Google Account data with cloudflareaccess.com", sent Monday 2026-11-09 4:11 PM CST, from Google to the author's Gmail. Text: you used Sign in with Google to sign in to cloudflareaccess.com on November 9 at 4:10 PM; "cloudflareaccess.com received this profile info": "<name> — Name and profile picture" and "<the author's Gmail> — Email address"; "This email includes the info you shared on November 9 at 4:10 PM"; links to the author's Google Account and a note that data can be deleted by contacting cloudflareaccess.com.
Facts (this is the key finding):
- The consent given at 4:10 PM CST (new, after "Delete all", E-075/E-076) included the email address: Google itself reports that cloudflareaccess.com received the author's email address. So the Google side is delivering the email.
- Yet Cloudflare's Test still reports the email as not returned, with the same id and name as in the first Test. So the failure is NOT explained by missing Google consent/scopes; the hypothesis of E-072/E-073 is REFUTED as the cause of this error (saving scopes may still have been harmless, but it did not fix it).
- What is not known: why Cloudflare does not get or parse the email. Possibilities that remain (none verified): how Cloudflare's Google integration retrieves the email (for example a different Google API call that the project may need enabled), a problem with how this particular IdP entry was created, or a Cloudflare-side issue. A docs search follows.
- Timeline note: the email is time-stamped 4:11 PM and the sign-in 4:10 PM, one minute before the author's message (4:15 PM).

## E-078 — Web search for the exact error: a Cloudflare Community thread with the same message and a lead (16:25 CST)
Sources: Cloudflare Community, "Unable to Authenticate with Google" (https://community.cloudflare.com/t/unable-to-authenticate-with-google/643784, about 936 days old per the search result, so roughly 2024); Cloudflare docs "Troubleshooting Access" (https://developers.cloudflare.com/cloudflare-one/troubleshooting/access); a GitHub discussion for another IdP (Authelia) with the same Cloudflare message. Read through search snippets only.
Findings:
- The Community thread reports exactly our message ("Failed to get your identity ... User email was not returned. API permissions are likely incorrect." with only id and name) for Google. One reply says a similar issue "seemed to be caused by something in the email claim field" and went away when that field was cleared; it gives the path: Zero Trust > Settings > Authentication > edit the login method that gives the error (in today's dashboard this is Integrations > Identity providers > edit; field under "Optional configurations" > "Email claim").
- Cloudflare's own docs describe the "Email claim" optional setting for other IdPs (for example Entra: the claim that represents the user's email; if it is renamed the dashboard value must match), which shows the field exists to tell Cloudflare WHICH claim to read the email from. If that field holds something that is not a real claim name, Cloudflare would look for a claim that does not exist and report the email as missing.
- Cloudflare's docs troubleshooting pages do not mention this exact message.
Status of the evidence: the Community reply is an unofficial, user-written, old message; it is a lead, not a documented fix. Our case fits it (Google delivered the email, E-077; Cloudflare says it is missing).
Hypothesis to test next (my reasoning, not verified): the "Email claim" field of the `google-lab` IdP contains a value (for example text inserted automatically by the browser or password manager when the Client ID/secret were pasted, since a password manager also filled the Grafana form earlier). Test: open the IdP, look at Optional configurations > Email claim, clear it if it has anything, save, run Test.

## E-079 — Screenshot: the "Email claim" field of the google-lab identity provider contains the author's email address (16:30 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the address is masked).
Section "Optional configurations" of the Google identity provider edit page. Field "Email claim (optional)" with the value `<the author's Gmail address, masked>` and the helper text "The claim name for email in the id_token response."
Facts:
- The field is meant to hold the NAME of the claim that carries the email inside the id_token (for example `email`), not an email address. It holds the author's address instead. Cloudflare therefore looks for a claim literally named after that address, finds none, and reports "User email was not returned" even though Google delivered the email (E-077). This matches the lead in E-078.
- The value was most likely inserted automatically (browser or password-manager autofill of an "email-like" field); the author does not remember typing it (inference; not asked explicitly).
- Status: strongly consistent explanation, but it is only CONFIRMED when the Test succeeds after the field is cleared.
Next: clear the field (empty means Cloudflare uses its default), save, run Test, record the result.

## E-080 — Test passes after clearing the Email claim field: "Your connection works!" (screenshot, 16:19 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the address is masked). the author's message: "listo" (he cleared the field and saved; the screenshot is the new Test).
Result page: "Cloudflare Access" logo, green check, heading "Your connection works!", subtitle "Below is the user identity we will use to check against your rules.", and the identity JSON with two fields: `"name": "<name>"` and `"email": "<the author's Gmail, masked>"`.
Facts:
- The Google identity provider `google-lab` now works end to end: Cloudflare receives the user's name AND email from Google, which is what Access policies match on.
- ROOT CAUSE CONFIRMED by the fix: the "Email claim" field held the author's email address instead of a claim name; once it was emptied the same Test (same Google client, same scopes, same account) succeeded (E-079 -> this entry).
- What was NOT the cause (ruled out with evidence): the Google redirect URI, client id and secret (the identity came back from the first Test, E-071); the Google consent/scopes (Google's own email showed the address was delivered before the fix, E-077). Saving scopes in Data Access and deleting the connection were harmless but unnecessary.
- Troubleshooting timeline (for the runbook ): 15:57 first Test fails (id and name only) -> hypothesis 1 (scopes) tested and refuted at 16:15 using Google's own notification email -> docs/community search found the Email claim lead (16:25) -> field inspected (16:30) -> cleared -> 16:19 CST screenshot of the passing Test (the screenshot's clock is earlier than the previous messages because the author's message timestamps and my log timestamps are not the same clock; not investigated).
Lesson: when an IdP says an attribute is missing, check (a) what the IdP actually sent (here Google's notification), then (b) the mapping fields on the Cloudflare side (claim names), before changing the IdP; and beware autofill in "optional" fields.
Piece 3 status: step B DONE. Next: step C = Access application for lab.jdjagustin-lab.dev/private with an Allow policy for the author's email and only the google-lab login method; step D tests.

## E-081 — Screenshot: the empty "Create new self-hosted application" form (16:29 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Zero Trust > Access controls > Applications > "Create new self-hosted application". Left menu under Access controls: Overview, Applications, Policies, MCP Portals, Targets, Service credentials, Access settings; other Zero Trust sections: Traffic controls, Data loss prevention, Cloud Workload (Beta), Cloud & SaaS findings, Email security, Browser isolation. Tabs: Application details, Additional settings.
Sections of the empty form:
- Destinations ("Define the public hostnames, specific paths, private IPs, private hostnames, or Workers protected by this application ... up to fifty destinations per app"): a Private IPs template row (empty) and four buttons: Add public hostname, Add private hostname, Add private IP, Add Workers.
- Browser-based RDP/SSH/VNC sessions: Off.
- Access policies ("Policies are default-deny. Access evaluates Bypass and Service Auth policies first. Then, policies are evaluated in order from top-to-bottom."): "No policy associated", buttons "Create new policy" and "Add current policies".
- Policy tester (needs a policy).
- Authentication (tabs Identity / MFA): "Accept all available identity providers" toggle ON; a selector "Choose available identity providers for this application"; "Apply instant authentication" off; "Authenticate with Cloudflare One Client" off.
- Preview: Sources / Policies / Destinations all empty.
- Details: Name (empty, "Use an auto-generated name or add your own."), Session Duration 24 hours. Buttons Cancel / Create.
Facts: nothing has been created yet. Plan for this form (path-based Access, Deviation 6): public hostname `lab.jdjagustin-lab.dev` with path `private`; one Allow policy with the author's email; accept-all-IdPs OFF with only `google-lab` selected; name `lab-private`. The default-deny note means that any request not matching an Allow rule is refused.

## E-082 — Screenshot: the Access application form filled in, before pressing Create (16:38 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the policy id is shortened).
- Destinations > Public hostnames: Subdomain `lab`, Domain `jdjagustin-lab.dev`, Path `private` (the "Switch to custom input" link is shown). An empty "Private IPs" template row is still present below it (empty fields; not used).
- Access policies: one policy attached: order 1, name `allow-owner-email`, action Allow, 1 rule, policy id `264e30f1-...` (shortened). The "Policy tester" "Test policies" button is now enabled.
- Authentication (Identity tab): "Accept all available identity providers" is OFF; the selector shows one chosen provider, "Google-lab - google"; "Apply instant authentication" OFF; "Authenticate with Cloudflare One Client" OFF.
- Preview: SOURCES "All authenticated users" -> POLICIES `allow-owner-email` -> DESTINATIONS `lab.jdjagustin-lab.dev/private`.
- Details: Name `lab-private`; Session Duration 24 hours. Buttons Cancel / Create.
Facts: the form matches the plan: path-scoped destination, a single Allow policy (the email rule itself is inside the policy; its content was not visible in this screenshot, only that it has 1 rule), and Google as the only login method. "All authenticated users" under Sources only describes who can reach the login via the chosen provider; the Allow policy is what restricts access to one email (to be proven by the tests: the author's account passes; another account would be refused, not tested unless a second Google account is available).
Not created yet at the time of the screenshot.

## E-083 — Screenshot: error when pressing Create on the Access application (16:40 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here).
Page "Create new self-hosted application" (tabs Application details / Additional settings) with a red banner: "Error configuring your application: access.api.error.invalid_request: use_clientless_isolation_app_launcher_url can only be enabled for apps with private destinations". The form is still shown below the banner.
Facts: the application was NOT created. The API rejected the request because an option named `use_clientless_isolation_app_launcher_url` (by its name, related to Browser Isolation / clientless web isolation and the App Launcher) is enabled in the request, and the API only allows it for applications that have private destinations. This application has a public hostname destination only (plus an empty "Private IPs" template row in the form). Cause of the option being on is not known: it may be a default of the form, or something triggered by the empty private row (both unverified). Lead: look in the "Additional settings" tab for a Browser isolation / clientless isolation option and turn it off; delete the empty Private IPs row.

## E-084 — Docs check for the Create error: what use_clientless_isolation_app_launcher_url is (web search, 16:58 CST)
Sources: Cloudflare API reference for Access applications (https://developers.cloudflare.com/api/resources/zero_trust/subresources/access/subresources/applications/), Cloudflare changelog "Streamlined clientless browser isolation for private applications" (https://developers.cloudflare.com/changelog/2026-02-17-clientless-access-for-private-apps), and third-party API wrappers listing the same field. Read through snippets only.
Findings:
- `use_clientless_isolation_app_launcher_url` is an optional boolean of an Access application: "Determines if users can access this application via a clientless browser isolation URL. This allows users to access private domains without connecting to Gateway. The option requires Clientless Browser Isolation to be set up with policies that allow users of this application."
- The February 2026 changelog says a new dashboard setting, "Allow clientless access", lets private self-hosted applications be reached without a device client; when it is on, users who pass the policies get a tile in the App Launcher pointing to a Clientless Web Isolation URL (remote browser permissions required).
Interpretation (mine, unverified): the dashboard is sending that flag as true for this application. The flag only makes sense for PRIVATE destinations, and our application is public (a hostname and path). The empty "Private IPs" template row that stayed in the form (E-081/E-082) may be what made the dashboard include a private-destination option such as "Allow clientless access". Two things to try, one at a time: (1) delete the empty Private IPs row; (2) if the error persists, find the "Allow clientless access" or browser-isolation toggle (Additional settings tab or near the destinations) and turn it OFF. Neither feature is needed for this lab.

## E-085 — Screenshot: the Access application `lab-private` now exists (16:45 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the policy id is shortened).
Page: Applications > `lab-private` (a saved application: buttons Delete, Cancel, Save; "View audit logs"; tabs All, Destinations, Browser rendering, Policies, Policy tester, Login methods, Preview, Details).
Contents as saved:
- Destinations > Public hostnames: Subdomain `lab`, Domain `jdjagustin-lab.dev`, Path `private`. The empty "Private IPs" row is no longer in the form.
- Browser-based RDP/SSH/VNC sessions: off.
- Access policies: `allow-owner-email` (order 1, Allow, 1 rule, id `264e30f1-...`).
- Authentication: "Accept all available identity providers" OFF; chosen provider "Google-lab - google"; instant authentication OFF; Cloudflare One Client authentication OFF.
- Preview: All authenticated users -> `allow-owner-email` -> `lab.jdjagustin-lab.dev/private`.
- Details: Name `lab-private`, Session Duration 24 hours.
Facts: the application was created (E-083's error is gone). The screenshot shows the empty Private IPs row removed, which is consistent with hypothesis (1) of E-084 (the empty private row made the dashboard send the private-only option); the "Allow clientless access" toggle was not needed. That explanation is plausible but not proven: I did not see which of the author's actions made the difference beyond his report of the new state.
Not verified yet: that the path is actually protected from outside (curl without cookies), that the login via Google works for this app, and that `/` is still public.

## E-086 — curl without cookies: /private/ and /private/index.html are redirected to Access login, / stays public (terminal, 16:46:44 CST)
Commands run by the author (Mac terminal): three `curl -sI "<URL>" | grep -i -E "^(HTTP|location)"` for `https://lab.jdjagustin-lab.dev/private/`, `/private/index.html` and `/`.
Result (the long `location` URLs are shortened here; each carries a `kid` and a signed `meta` token):
```
/private/            -> HTTP/2 302
  location: https://<team-name>.cloudflareaccess.com/cdn-cgi/access/login/lab.jdjagustin-lab.dev?kid=<...>&meta=<signed token>&redirect_url=%2Fprivate%2F
/private/index.html  -> HTTP/2 302
  location: https://<team-name>.cloudflareaccess.com/cdn-cgi/access/login/lab.jdjagustin-lab.dev?kid=<...>&meta=<signed token>&redirect_url=%2Fprivate%2Findex.html
/                    -> HTTP/2 200
```
Facts:
- Access protects the path: a request without any session to /private/ and to a file under it (/private/index.html) is redirected (302) to the login page on the team domain, with `redirect_url` set to the original path, so the user would return there after logging in. The sub-path inheritance described in the docs (E-065) is confirmed by the second request.
- The rest of the hostname stays public: `/` still answers 200 (no Access redirect), as intended.
- The `meta` value in the redirect is a JWT (three base64url parts). The payload of the first one decodes to the following claims (decoded locally from the text the author pasted; identifiers masked):
```
{
  "type": "meta",
  "aud": "e333ceeb...(masked)",
  "hostname": "lab.jdjagustin-lab.dev",
  "redirect_url": "/private/",
  "service_token_status": false,
  "is_warp": false,
  "is_gateway": false,
  "exp": 1794264704,
  "nbf": 1794264404,
  "iat": 1794264404,
  "auth_status": "NONE",
  "mtls_auth": {
    "cert_issuer_dn": "",
    "cert_serial": "",
    "cert_issuer_ski": "",
    "cert_presented": false,
    "common_name": "",
    "auth_status": "NONE"
  },
  "real_country": "MX",
  "app_session_hash": "6dd3480b...(masked)",
  "_exp_utc": "2026-11-09T22:51:44Z",
  "_iat_utc": "2026-11-09T22:46:44Z"
}
```
 Reading: `hostname` and `redirect_url` echo the request; `auth_status` is NONE (not authenticated); `real_country` MX; `is_warp`/`is_gateway` false (no device client); the token lives 300 seconds (`exp` minus `iat`); `aud` is the application's audience tag (the same value is sent as `kid`). The signature was not verified (not needed).
- The timestamp `iat` (22:46:44 UTC) equals the prompt time in the terminal (04:46:44 PM CST).
Not verified yet: the browser login flow with Google and the "Private area" page, the Access authentication log entry, and that a different Google account is refused.

## E-087 — Full browser login through Access with Google: positive test PASSED (4 screenshots + the author's account, 16:55 CST)
Source: four screenshots and the author's description (not on disk yet; transcribed here; the Gmail address is masked). The test was done in a Private Browsing window ("Navegación privada") so no earlier session or cookie was involved.
Sequence (the author's account plus screenshots):
1. Opening https://lab.jdjagustin-lab.dev/private/ showed the Cloudflare Access login page on the team domain: "Log in to lab-private", "Sign in with:" with one button "Google · Google-lab" (screenshot 1).
2. Choosing it opened Google's "Acceder con Google" page on accounts.google.com ("Accede a tu cuenta — Ir a cloudflareaccess.com") with an empty email field (screenshot 2): no Google session existed in that window.
3. the author typed his Gmail address; Google asked him to authenticate with his fingerprint (Touch ID/passkey on the Mac; as he described it, the exact Google prompt was not captured).
4. After that he reached the page "Private area — Temporary page behind Cloudflare Access, used for the lab identity provider test." at the lab hostname (screenshot 3; the browser shows only the host, not the path). This is the content of ~/lab-site/private/index.html (E-066).
5. At the same time Google sent a "Security alert: A new sign-in on Mac OS" email to the same address, received 4:52 p.m. (screenshot 4): "We noticed a new sign-in to your Google Account on a Mac OS device. If this was you, you don't need to do anything." with a "Check activity" button and a link to myaccount.google.com/notifications.
Facts:
- The positive test works end to end: browser -> Access login -> Google (OIDC identity provider `google-lab`) -> back to the protected path -> origin page served through the tunnel. The Allow policy `allow-owner-email` accepted the author's identity (the email delivered by Google, which the earlier Email-claim fix made possible, E-080).
- The "new sign-in" alert is the expected side effect of logging in from a private window (a fresh browser without cookies looks like a new device to Google) and matches the time of the test (about 4:52 p.m.). It was not investigated beyond that; the links in the email were NOT opened.
- About MFA: the second factor in this test (fingerprint/passkey) was requested by GOOGLE for the author's Google account. Cloudflare Access itself was not configured to require MFA (the application's "MFA" tab was not used). So what can be said is "Access trusted a Google login that used a passkey", not "MFA enforced by Cloudflare".
Not verified yet: the Access authentication log entry for this login, and the negative test (an account whose email is not in the policy must be refused; needs a second Google account).

## E-088 — Which log shows the Access login: "Access authentication logs" (docs check, 17:03 CST)
Sources: Cloudflare docs "Access authentication logs" (https://developers.cloudflare.com/cloudflare-one/insights/logs/dashboard-logs/access-authentication-logs/ and the older "Access audit logs" page). Read through search snippets.
- Where: Zero Trust (Cloudflare One) > Insights > Logs > "Access authentication logs" (older wording: Logs > Access). The new viewer is marked beta and has a "Return to old logs" option. The application page `lab-private` also has a "View audit logs" button (seen in E-085).
- What it records: an authentication event every time a user or service tries to log in to an application, whether it succeeds or not (identity-based events only; non-identity events such as IP or service-token policies need the GraphQL API).
- Fields documented: user email, IP address, app domain, app type, action (for example login), connection (identity provider used, e.g. google), allowed (true/false), Ray ID, country, request time. For a blocked attempt, a "View" link explains why Access denied it.
- Retention (as stated in the docs page I read; may have changed): authentication logs are kept six months, block decisions about a week.
- Not captured: user actions during the session (the log covers authentication, not what the user did afterwards); per-request audit logs are a different thing.
Expected entry for the author's test (E-087, about 4:52 p.m. CST): action login, connection google, allowed true, app lab.jdjagustin-lab.dev/private, his email, country Mexico. Screenshot pending (mask email and IP in the file).

## E-089 — Access authentication logs exported as CSV: the author's Google login to lab-private is recorded (file attached, 17:06 CST)
Source: file `Access_Request_Logs_2026-11-09T23_02_57Z.csv` attached by the author (Access authentication logs export, generated 2026-11-09 23:02:57 UTC = 17:02:57 CST). 2 data rows, 17 columns. A masked copy (email, IP, user id, app ids masked; the last four optional columns are empty and omitted) is in `evidence/Access_Request_Logs_2026-11-09T23_02_57Z_masked.csv`.
Rows (times in UTC; CST = UTC minus 6 hours):
1. App `lab-private`, domain `lab.jdjagustin-lab.dev`, type self_hosted, action `login`, connection `google`, Allowed `true`, created `2026-11-09T22:52:03` (= 16:52:03 CST), RayID `a58062bd3de9f8b8`, country mx.
2. App `grafana`, domain `grafana.jdjagustin-lab.dev`, type self_hosted, action `login`, connection `cloudflare`, Allowed `true`, created `2026-11-09T18:27:46` (= 12:27:46 CST), RayID `a57edf973d288de5`, country mx.
Both rows carry the same user (the author's Gmail, same Access user id) and the same client IP (the author's home address).
Facts:
- The Access log recorded the lab-private login exactly as designed: identity provider `google` (the `google-lab` IdP), allowed true, at 16:52:03 CST, which matches the "new sign-in" alert Google sent at 4:52 p.m. (E-087). Positive test proven in three places: the browser (E-087), the origin page, and the Access authentication log.
- Row 2 explains the morning check (E-017): at 12:27:46 CST Access allowed the author into Grafana through the `cloudflare` connection (the "Cloudflare" login button of Access, which is a login with his Cloudflare account), matching the time he reached Grafana after the cloudflared upgrade (about 12:29 CST). So that earlier pass was a genuine Access login, not a stale session of the Grafana app.
- The export holds only two events for the whole window: no denied or failed attempts exist yet, so the "blocked" path of the log (with its "View" explanation) has not been exercised. Failed logins at the Cloudflare account form (E-017) or the identity-provider Test pages (E-071, E-077) are not Access application logins and do not appear here.
- Fields confirmed by the real export: App Name, User Email, User ID, IP Address, App UID, App Domain, App Type, Action, Connection, Allowed, Created At, RayID, Country, plus Purpose Justification and Temporary Access columns (empty here).
Pending: negative test (needs a second Google account) to produce an `allowed false` row.

## E-090 — Screenshot: Application Access Report dashboard (17:08 CST)
Source: screenshot pasted in chat (not on disk yet; transcribed here; the Gmail and the IP are masked).
Zero Trust > Insights & Logs > Dashboards > "Application Access Report" ("Summary of application Access usage across your organization"), time window "Last 24 hours".
- Summary: Total access events 2; "All login attempts were successful. The highest number of Access events occurred on Nov 9, 2026 at 12:00 PM at 1 events."
- Access events chart: two bars of "Granted" (one around 12:00 PM, another around 4-5 PM, local time).
- Access decisions by event count: Granted 2. Access events by type: Login 2. Access applications by event count: Self-hosted 2.
- Top counts: Application name: grafana 1, lab-private 1. Identity provider: google 1, cloudflare 1. Users: <the author's Gmail> 2. Countries: MX 2. IP addresses: <the author's home IP> 2.
- Access admin metrics: Applications configured 2, Self-hosted applications 2, Policies configured 2, Allow policies 2.
Facts: it is a second view of the same data as the CSV (E-089): two events, both granted, one per application and per identity provider; zero denied events. The admin metrics show the lab's whole Access configuration at a glance: two applications (grafana and lab-private) and two Allow policies (no Block or other policy types).
Piece 3 status: positive path proven in the browser (E-087), in the authentication log (E-089) and in the dashboard (this entry). The negative test (a denied account) is NOT done: the author did not mention a second Google account. Left as "not tested".

## E-091 — Piece 4.1: origin stopped on purpose -> Cloudflare answers 502 (terminal on Cloudlab-1 + Mac screenshot, 17:15 CST)
Source: the author's terminal output pasted as text (Cloudlab-1) and a screenshot (Mac terminal).
Cloudlab-1 (commands: `pgrep -af "http.server 8081"`, `pkill -f "http.server 8081"`, `pgrep -af "http.server 8081" || echo "servidor apagado"`):
```
3738629 python3 -m http.server 8081 --bind 127.0.0.1 --directory /home/<user>/lab-site
servidor apagado
```
The temporary static server (PID 3738629, the one started in E-030) was found and stopped; afterwards no process matched. cloudflared was left running.
Mac terminal (commands: `curl -sI "https://lab.jdjagustin-lab.dev/" | grep -i -E "^(HTTP|server|cf-ray)"` and `curl -s "https://lab.jdjagustin-lab.dev/" | grep -i -E "<title>|error code|Bad gateway"`), output as shown in the screenshot:
```
HTTP/2 502
server: cloudflare
cf-ray: a58083c549456717-DFW
error code: 502
```
Facts:
- With the origin down and the tunnel up, the public hostname answers `HTTP/2 502` generated by Cloudflare (`server: cloudflare`, a `cf-ray`, and the page body contains "error code: 502"). The prediction made in the plan ("502") held.
- CORRECTION to the earlier plan: the initial plan expected 530/1033 for "origin down behind a tunnel". That was wrong for this scenario; those codes belong to the case where the tunnel itself is not connected (to be tested in 4.2; a docs snippet mentioned 1016 for a DNS record pointing to a stopped tunnel (later corrected: E-097, E-122, E-127), so the exact code for 4.2 is still unknown).
- Meaning of 502 here (reasoning, to be confirmed by the cloudflared log): Cloudflare reached the tunnel (cloudflared is connected), but cloudflared could not get an answer from http://localhost:8081, so Cloudflare returns Bad Gateway to the visitor.
- The title/"Bad gateway" text of the page body did not match the grep patterns (only "error code: 502" was printed); the page was not read in full.
Next in 4.1: read cloudflared's own error in the journal and test the origin directly (layered diagnosis), then capture a HAR in Chrome while the origin is still down, then restart the origin.

## E-092 — Layered diagnosis of the 502: cloudflared's journal and a direct test of the origin (terminal on Cloudlab-1, 17:17 CST)
Source: terminal output pasted as text by the author.
Shell notice at the start of the output: `[1]+  Terminated  nohup nice -n 19 python3 -m http.server 8081 --bind 127.0.0.1 --directory ~/lab-site > /tmp/lab-site.log 2>&1` (bash reporting that the background job started in E-030 ended after `pkill`, see E-091).
Command 1: `journalctl -u cloudflared --since "10 minutes ago" --no-pager | grep -i -E "ERR|origin" | tail -n 6`. Output (4 lines, two pairs, all at 17:14:37 CST = 23:14:37Z; shown shortened with `...`):
```
ERR  error="Unable to reach the origin service. The service may be down or it may not be responding to traffic from cloudflared: dial tcp 127.0.0.1:8081: connect: connection refused" connIndex=1 event=1 ingressRule=1 originService=http://localhost:8081
ERR Request failed error="Unable to reach the origin service. ... dial tcp 127.0.0.1:8081: connect: connection refused" connIndex=1 dest=https://lab.jdjagustin-lab.dev/ event=0 ip=198.41.192.37 type=http
(the same two lines repeated once more)
```
Command 2: `curl -sS -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:8081/"`. Output:
```
curl: (7) Failed to connect to 127.0.0.1 port 8081 after 0 ms: Could not connect to server
000
```
Facts (the three layers agree):
1. Edge (visitor side): 502 from Cloudflare (E-091).
2. Tunnel (cloudflared): for the request to `https://lab.jdjagustin-lab.dev/`, it logged "Unable to reach the origin service ... dial tcp 127.0.0.1:8081: connect: connection refused", naming the rule that failed (`ingressRule=1`, the second rule of config.yml, the `lab` hostname, E-031) and the target (`originService=http://localhost:8081`). Two request/error pairs at 17:14:37 correspond to the two curls the author sent (a HEAD and a GET, E-091); the log does not print the Cloudflare ray id, so the link is by time and destination. The `ip=198.41.192.37` is the Cloudflare edge address of the connection (connIndex=1).
3. Origin (direct test): nothing listens on 127.0.0.1:8081: connection refused, HTTP code 000 (no HTTP response at all).
Root cause (supported by all three): the origin service stopped; cloudflared is healthy and connected, which is why Cloudflare returned 502 (Bad Gateway) and not a tunnel-down error. Fix: start the origin again.
Method for the runbook: start from what the user sees (status and Ray ID), go one hop inward (tunnel log with the ingress rule and target), then test the last hop directly (origin on localhost); `connection refused` means nothing is listening, while a timeout would point to a firewall or a hung process.
Note for restarting: the original start command used `>` to write the log, which would erase /tmp/lab-site.log (evidence of E-048, E-054, E-064). Use `>>` to append.

## E-093 — Piece 4.1: HAR of the 502 page captured with Safari Web Inspector (file + screenshot, 19:42 CST)
Source: the author's screenshot of Safari's Network tab and the exported file `lab.jdjagustin-lab.dev.har` (Safari proposed that name; 51,386 bytes; creator "WebKit Web Inspector", HAR version 1.2; 8 entries; page loaded 2026-11-10T01:40:21.734Z = 19:40:21 CST). the author reported the six steps done. The origin was still stopped (since 17:14 CST, about 2.5 hours; planned only for the capture, restart pending).
Screenshot: the page "Bad gateway - Error code 502 - Visit cloudflare.com for more information. 2026-11-10 01:40:22 UTC"; Network list with 8 requests (document 578 ms, main.css 339 ms, five cf-icon-*.png 130-416 ms, favicon.ico 155 ms); footer: 8 requests, 20.1 KB, 16.4 KB transferred, 1.37 s.
HAR entries (method, path -> status; server is `cloudflare` in all):
1. GET / -> 502, text/html, cf-ray a581594609ea5473-DFW, 578 ms
2. GET /cdn-cgi/styles/main.css -> 200, text/css
3-7. GET /cdn-cgi/images/cf-icon-browser|ok|cloud|server|error.png -> 200, image/png
8. GET /favicon.ico -> 404, text/html;charset=utf-8, 155 ms
Facts:
- The error document: Content-Length 6448; title "jdjagustin-lab.dev | 502: Bad gateway"; `Cache-Control: private, max-age=0, no-store, no-cache, ...` (not cacheable); `retry-after: 60`; `Server-Timing: cfEdge;dur=32,cfOrigin;dur=62` (Cloudflare reports 32 ms in the edge and 62 ms trying the origin through the tunnel, about 94 ms in total); the body contains the Ray ID, the visitor IP and the status diagram words ("Working", "Error", "Host"). Browser timings for that request: blocked 14.6 ms, wait 562.7 ms, receive 0.65 ms; dns/connect/ssl = -1 (connection reused). The roughly 470 ms between the browser's wait and Cloudflare's own 94 ms is time outside Cloudflare's processing (network and queueing); not investigated.
- The error page is self-contained at the edge: its stylesheet and five icons come from `/cdn-cgi/...` on the same hostname and are served by Cloudflare itself (status 200), not by Cloudlab-1. That is why the error page renders correctly with the origin dead.
- Finding: `favicon.ico` came back as `404` with `cf-cache-status: STALE`, `Age: 15247` (about 4 h 14 min), `Cache-Control: max-age=14400`, body "Error response" (460 bytes; the 404 page of Python's http.server). Cloudflare served an expired cached copy of an earlier 404 because it could not reach the origin. Date minus Age puts the moment it was cached at about 21:26 UTC = 15:26 CST (that request is not in the part of the origin log read earlier, which ended around 15:11). So a cacheable object survived the outage as STALE while the uncached HTML returned 502: the cache can hide an origin failure for cacheable URLs. (The meaning of STALE is from Cloudflare's documentation as I remember it; not re-checked in this session.)
- HAR hygiene: no Authorization header, no Set-Cookie, no CF_Authorization, request cookie lists empty, no Gmail address. The word "cookie" appears 16 times in the file (likely static text of the error page; not checked line by line). The only personal datum found was the author's public IP address, once, in the body of entry 1 (the "Your IP" field); it is masked in the copy.
- Files: masked copy `evidence/lab-502_origin-down_2026-11-09_masked.har` (51,392 bytes, valid JSON). The unmasked original was archived, following the author's rule for replaced versions, to an archive folder (the author empties that folder). The file name differs from the one suggested to the author because Safari proposed its own.
Not verified yet: whether a cached stylesheet (style.css, cached at 13:33 CST with max-age 14400, now expired) is also served STALE while the origin is down (test planned before restarting the origin); test 4.2 (tunnel stopped).

## E-094 — Piece 4.1 experiment: cached files are served STALE while the origin is down (terminal, 19:48 CST)
Source: the author's Mac terminal output (screenshot as text), run with the origin still stopped.
Commands: `curl -sI "https://lab.jdjagustin-lab.dev/style.css" | grep -i -E "^(HTTP|cf-cache-status|age)"` and the same for `/style.css?test=1`.
Output:
```
/style.css          -> HTTP/2 200   age: 10579   cf-cache-status: STALE
/style.css?test=1   -> HTTP/2 200   age: 21911   cf-cache-status: STALE
```
Facts:
- Hypothesis confirmed: with the origin unreachable, Cloudflare answers 200 from its cache with `STALE` for cacheable files (the hypothesis was "STALE or 502"; the result is STALE for both). Together with the favicon in E-093 (404 served STALE) and the 502 for the uncached HTML (E-091), the same outage gives three different answers depending on what is cached.
- Definition from Cloudflare's docs ("Cloudflare cache responses", read through search snippets): STALE = the resource was served from Cloudflare's cache but was expired, and Cloudflare could not contact the origin to retrieve an updated resource. The docs also say Cloudflare sets `Age` on HIT, STALE and UPDATING responses.
- Why the files were expired: Cloudflare's default edge TTL when the origin sends no Cache-Control (the Python server sends none) is 120 minutes for 200, 206 and 301 and 3 minutes for 404 and 410 (docs "Default cache behavior"). Ages of 10579 s (2 h 56 min) and 21911 s (6 h 05 min) exceed 120 minutes; the favicon 404 (age 15247 s) exceeded 3 minutes. The header `cache-control: max-age=14400` seen earlier (E-046) is a different thing: it is what Cloudflare tells the BROWSER to keep the file (4 hours), not the edge's freshness window. This clarifies my earlier remark in E-046/E-093.
- The ages match events in the lab (Date 19:48:26 CST minus Age): `?test=1` was stored at about 13:43:15 CST = the MISS of E-047 (origin log 13:43:14); `/style.css` was last refreshed at about 16:52:07 CST = the author's private-window login to /private/ (E-087, 16:52:03), whose page loads /style.css. Prediction to verify in the origin log after restart: a `GET /style.css` at about 16:52 (a refresh of the expired copy), and no origin request for `?test=1` after 13:43:14.
Lesson for the runbook: during an origin outage some URLs keep working (STALE copies) and others fail (502); a customer reporting "some pages work and others do not" fits an origin problem, and `cf-cache-status: STALE` plus a large `Age` is the signature.
Reminder: the origin is still down at the time of this entry (since 17:14 CST).

## E-095 — Origin restarted (append mode) and the origin log confirms the STALE/revalidation story (terminal on Cloudlab-1, about 19:53 CST)
Source: terminal output pasted as text by the author. Commands (one block): `nohup nice -n 19 python3 -m http.server 8081 --bind 127.0.0.1 --directory ~/lab-site >> /tmp/lab-site.log 2>&1 &`, `sleep 1`, `curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:8081/"`, `grep "style.css" /tmp/lab-site.log`.
Output:
```
[1] 3888257
200
127.0.0.1 - - [09/Nov/2026 13:09:17] "GET /style.css HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 13:33:05] "GET /style.css HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 13:43:14] "GET /style.css?test=1 HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 16:52:06] "GET /style.css HTTP/1.1" 304 -
```
Facts:
- The temporary origin is UP again: new process 3888257 (the previous one was 3738629), local check returns 200. Origin outage window: stopped about 17:14 CST (E-091), restarted about 19:53 CST: roughly 2 h 39 min (the stop time is from the cloudflared errors at 17:14:37; the restart time is the time of the author's message, not a captured log timestamp).
- The log was APPENDED, not overwritten: the lines from 13:09 to 16:52 are still there, so the evidence of E-048, E-054, E-064 is preserved.
- The two predictions of E-094 held: (1) there is a `GET /style.css` at 16:52:06 CST (my estimate from the Age header was about 16:52:07), which is Cloudflare refreshing the expired copy right after the author's private-window login (E-087); (2) there is no origin request for `?test=1` after 13:43:14.
- New detail: that 16:52:06 request was answered `304 Not Modified`, not 200. The origin has `Last-Modified` on the file (seen in E-046), so Cloudflare revalidated its expired copy with a conditional request and the origin replied "not modified" without sending the body; Cloudflare then kept serving the copy as fresh. In Cloudflare's own vocabulary this is the `REVALIDATED` cache status (revalidated by If-Modified-Since / If-None-Match, per the cache-status docs read in the previous step; the status itself was not observed for this request, only the 304 at the origin).
- None of the lines show the two `curl` requests of E-094 (STALE) because they never reached the origin, as expected.
Cache lifecycle now observed end to end for one file: MISS (13:33, fetched 200) -> HIT (served by the edge, invisible at the origin) -> expired after the 2-hour default edge TTL -> conditional refresh (304 at 16:52) -> expired again -> STALE while the origin was down (19:48).

## E-096 — Baseline "everything up" before stopping the tunnel (three screenshots, 19:58 CST)
Source: three screenshots pasted in chat (not on disk yet; transcribed here; Gmail masked). the author's words: everything is up before bringing the tunnel down; "matando tunel" (he is about to stop / is stopping cloudflared for test 4.2).
1. Cloudflare Domains overview: `<other-zone>` Active, "4 insights", unique visitors 4; `jdjagustin-lab.dev` Active, "3 insights", unique visitors 9 (sparklines).
2. Grafana Home at grafana.jdjagustin-lab.dev, logged in as the author's user (profile menu open: name, <Gmail>, Profile, Notification history, Change password, Sign out): the Grafana path (Access -> tunnel -> Grafana) works before the test.
3. Safari Network tab on https://lab.jdjagustin-lab.dev/ (page "Lab site" renders): requests: document `lab.jdjagustin-lab.dev` (866 B transferred, 612 ms), `style.css` (366 B, 204 ms, initiator lab.jdjagustin-lab.dev:6), a JavaScript file with a long hash name from `static.cloudflareinsights.com` (10.48 KB, 417 ms, initiator lab.jdjagustin-lab.dev:11), and an XHR named `rum` to lab.jdjagustin-lab.dev (365 B, 124 ms, initiator the cloudflareinsights script).
Facts:
- Baseline before test 4.2: lab page up (the origin was restarted at about 19:53, E-095) and Grafana up.
- New finding: Cloudflare is injecting its Web Analytics beacon into the HTML of the proxied site. Evidence: a script from static.cloudflareinsights.com that the author's origin file does not contain is loaded with initiator "lab.jdjagustin-lab.dev:11"; line 6 of our index.html is the `<link rel="stylesheet">` (style.css has initiator :6, consistent) and line 11 of the file is `</body>`, so the snippet sits right before the closing body tag; the script then posts a `rum` (real user monitoring) beacon to the same hostname. My reading: this is Cloudflare Web Analytics' automatic setup for proxied sites (my understanding of the feature, not re-checked in this session); it explains the "unique visitors" counters in screenshot 1 and the earlier "Web analytics" entry in the dashboard's Recents. Consequence: the HTML a visitor receives is not byte-identical to the file on Cloudlab-1 (the origin file is 276 bytes; the transferred document is 866 B including headers).
- Not verified: the document body that the browser actually received (would need to open the response in the Network tab or run `curl` and look for "cloudflareinsights").
Next: stop cloudflared (Cloudlab-1), run the three curls from the Mac, restart cloudflared and check 4/4 connections.

## E-097 — Piece 4.2: tunnel stopped on purpose -> HTTP 530 with Cloudflare error 1033; a fresh cached file still answers HIT (terminals, about 20:00 CST)
Source: terminal output pasted by the author (Cloudlab-1) and a Mac terminal screenshot (prompt time 08:00:11 PM).
Cloudlab-1: `sudo systemctl stop cloudflared.service` then `systemctl is-active cloudflared` -> `inactive` (the usual "Failed to allocate directory watch: Too many open files" warning appeared again, see E-011).
Mac (commands: `curl -sI "https://lab.jdjagustin-lab.dev/" | grep -i -E "^(HTTP|server|cf-ray)"`, `curl -s "https://lab.jdjagustin-lab.dev/" | grep -i -E "<title>|error code"`, `curl -sI ".../style.css" | grep -i -E "^(HTTP|cf-cache-status|age)"`):
```
/           -> HTTP/2 530   server: cloudflare   cf-ray: a581764fa8ed6477-DFW   (body: "error code: 1033")
/style.css  -> HTTP/2 200   age: 130   cf-cache-status: HIT
```
Restart (Cloudlab-1): `sudo systemctl start cloudflared.service`, then the journal check printed ONLY `Registered tunnel connection connIndex=0` at that moment (the check was run immediately; the other connections had not registered yet when it ran). The full 4/4 is NOT yet confirmed.
Facts:
- Stopping cloudflared gives a different error from stopping the origin: HTTP 530 with Cloudflare error code 1033, instead of the 502 of E-091. The original plan's expectation (530/1033) was right for THIS scenario (tunnel down) and wrong for origin-down (corrected in E-091).
- Cloudflare's docs (Error 1033 page and Tunnel troubleshooting, read through snippets): 1033 means the tunnel is not connected to Cloudflare's network because Cloudflare cannot find a healthy cloudflared instance; the dashboard shows tunnel health as Healthy (four connections), Degraded (cloudflared running but at least one connection failed) or Down (it was connected but cloudflared stopped). The docs also state the contrast we measured: a 502 with "Unable to reach the origin service" means the tunnel IS connected and the problem is between cloudflared and the local service, unlike 1033 where the tunnel itself is disconnected.
- The earlier docs mention of "error 1016" (E-037) did not occur in this test: for a tunnel that was connected and then stopped the result is 1033. 1016 was not reproduced here; its exact scenario remains unverified.
- `style.css` answered `HIT` (not STALE, not an error) with `Age: 130` while the tunnel was down: the copy had been refreshed about 130 s earlier, around 19:57:58 CST, when the author loaded the lab page in Safari with the origin up (E-096, screenshot 3); a fresh cached file is served by the edge without needing the tunnel. Prediction to verify in the origin log: a request for /style.css at about 19:57 (probably a 304).
Three-state picture for the runbook (same site, three situations): file fresh in cache -> HIT (works even with the tunnel down); file expired in cache -> STALE (works while the origin or tunnel is down, E-094); file not cached -> error: 502 if the tunnel is up but the origin is down (E-091), 530/1033 if the tunnel is down (this entry).
Status of cloudflared at the time of this entry: restarted, connections still registering. Grafana depends on it.

## E-098 — Origin log for 19:5x confirms the 304 prediction; the cloudflared connection check came back EMPTY (terminal on Cloudlab-1, about 20:05 CST)
Source: terminal output pasted as text by the author. Commands: `journalctl -u cloudflared --since "3 minutes ago" --no-pager | grep -o -E "Registered tunnel connection connIndex=[0-9]"` and `grep "19:5" /tmp/lab-site.log`.
Output: the first command printed NOTHING. The second printed:
```
127.0.0.1 - - [09/Nov/2026 19:52:08] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 19:58:00] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [09/Nov/2026 19:58:01] "GET /style.css HTTP/1.1" 304 -
```
Facts:
- Prediction of E-097 confirmed: the `style.css` request I expected "at about 19:57" happened at 19:58:01 and was a 304 (revalidation of the expired copy), right after the author loaded the page in Safari (`GET /` at 19:58:00, E-096 screenshot 3). The edge's `Age: 130` at the 20:00:11 curl (E-097) places the refresh at 19:58:01 exactly (20:00:11 minus 130 s).
- CORRECTION to E-095: the log shows the origin was restarted at about 19:52:07-08 CST (the local check `GET /` at 19:52:08 is the 200 test of that command), not 19:53 as estimated from the time of the author's message. Origin outage: from about 17:14:37 (E-092) to about 19:52:08, roughly 2 h 37 min.
- UNRESOLVED, urgent: the journal check printed no "Registered tunnel connection" line for the last 3 minutes. Two possible readings, not distinguished yet: (a) cloudflared restarted at about 20:01 and all four connections registered within the first seconds, before the 3-minute window began (the window was about 20:02-20:05); (b) cloudflared is not running or not connected. Only a wider look can tell (service state, a wider journal window, a request from outside).

## E-099 — Recovery verified: cloudflared active, 4/4 connections re-registered, public site 200 (terminals, 20:08 CST)
Source: terminal output pasted by the author (Cloudlab-1 and Mac).
Cloudlab-1: `systemctl is-active cloudflared` -> `active`. Journal (last 15 minutes, filtered, lines cut at 120 characters), times CST with the UTC time inside each line:
```
19:59:34 (01:59:34Z) ERR Connection terminated connIndex=2, connIndex=0, connIndex=1, connIndex=3
19:59:34 (01:59:34Z) ERR no more connections active and exiting          (old process 3740956)
20:01:34 (02:01:34Z) INF Registered tunnel connection connIndex=0        (new process 3891951)
20:01:34 INF Registered tunnel connection connIndex=1
20:01:35 INF Registered tunnel connection connIndex=2
20:01:36 INF Registered tunnel connection connIndex=3
```
Mac: `curl -sI "https://lab.jdjagustin-lab.dev/" | grep -i -E "^(HTTP|cf-ray)"` -> `HTTP/2 200`, `cf-ray: a58181dfec06e7a6-DFW`.
Facts:
- Reading (a) of E-098 was right: all four connections registered at 20:01:34-36 (before the 3-minute window of that earlier check began), and cloudflared is running as a new process (3891951; the stopped one was 3740956).
- The planned tunnel outage is measured by the journal: connections terminated and process exiting at 19:59:34; four connections registered again at 20:01:34-36. The tunnel was down for about 2 minutes, a window that includes the time the author took to run the test commands (the 530/1033 curls at about 20:00:11, E-097, fall inside it). It is NOT a measure of a normal restart.
- The public site answers 200 again (cf-ray a58181dfec06e7a6-DFW).
- Not verified in this entry: Grafana in the browser after the restart (the author has not reported it); the dashboard tunnel health (expected Healthy).
Piece 4 status: 4.1 (origin down: 502, layered diagnosis, HAR, STALE) and 4.2 (tunnel down: 530/1033) done and the service restored.

## E-100 — Screenshot: Grafana Home on screen after the tunnel restart (20:09 CST) — NOT conclusive by itself
Source: screenshot pasted in chat (not on disk yet; transcribed here; Gmail masked).
Safari at grafana.jdjagustin-lab.dev showing Grafana Home ("Welcome to Grafana", the "Basic" setup cards) with the user menu open (name, <Gmail>, Profile, Notification history, Change password, Sign out). The layout and the open menu are the same as in the baseline screenshot taken before the tunnel was stopped (E-096, screenshot 2).
Facts and limit: a Grafana page that was already open in a tab stays on screen even if the tunnel is down, so this image cannot prove that Grafana is reachable AFTER the restart; it only shows an open session. The proof would be a fresh load: reload the tab (Command+R); if the tunnel were still down the browser would show a Cloudflare error page instead. Request made to the author; result pending.
What is already proven about the restart: cloudflared active with 4/4 connections (E-099) and the lab hostname answering 200 from outside (E-099). Grafana shares the same tunnel and connections, so it is very likely reachable, but that is inference until the reload is seen.

## E-101 — Reload of the Grafana tab after the tunnel restart: the author's report is AMBIGUOUS (20:13 CST) — PROVISIONAL
Source: the author's message "recargue la pagina y eso salio", with no new attachment. "Eso" most likely refers to the Grafana Home screenshot he had sent a few minutes earlier (E-100), which would then be the page that appeared after the reload; but it could also mean something else (for example an error page). I did not assume: the entry stays provisional until the author confirms in one word what appeared (Grafana Home, an Access login, or a Cloudflare error page).
If confirmed as Grafana Home: the recovery after test 4.2 is fully proven by the reload (a fresh load needs the tunnel), still as the author's report plus E-100 rather than a dedicated screenshot of the reload.

## E-102 — Grafana reload after the tunnel restart: confirmed by the author (20:14 CST) — his report, no new screenshot
Source: the author's message: after reloading the tab, the same Grafana page appeared ("volvio a aparecer la misma pagina"); he adds that it looked as if the tunnel had never gone down, but the tunnel was already up (the reload happened after the restart).
Facts:
- A fresh load of grafana.jdjagustin-lab.dev succeeded after cloudflared was restarted: Access -> tunnel -> Grafana is reachable again. This closes the open item of E-100/E-101. It rests on the author's report plus the 4/4 connections and the 200 from outside (E-099); there is no dedicated screenshot of the reload (E-100 shows the same page).
- Grafana was NOT tested during the outage (only the lab page was: 530/1033, E-097). That Grafana would have failed during the 2 minutes is an inference (it uses the same tunnel and connections), not a measurement.
Status: Piece 4 and the recovery are fully closed.

## E-103 — Reference: Google Admin Toolbox "HAR Analyzer" (page read, 20:20 CST)
Source: https://toolbox.googleapps.com/apps/har_analyzer/ (URL given by the author; page text read through a fetch).
What the page says:
- Use: choose a HAR file; the analysis screen opens. All times are shown in UTC.
- Features: group entries by page or list all; timing display relative to the page or per entry; a free-text filter with operators and field:term pairs (for example request.url:, request.method:, response.status:); a filter by HTTP status class (0, 1xx, 2xx, 3xx, 4xx, 5xx).
- Privacy warning on the page: HAR files contain sensitive data (page contents, cookies that would let someone impersonate the account, everything submitted while recording including passwords and card numbers). After uploading, a redaction button (top left) downloads a redacted copy that is safer to share.
- What the page does NOT say (in the text I read): whether the file is processed only in the browser or sent to a server. Treat it as an upload to a third party unless verified.
- Its capture instructions cover Chrome, Edge and Firefox (not Safari); Safari's Web Inspector also exports HAR (the file in E-093 was exported that way, creator "WebKit Web Inspector", HAR 1.2).
Practical rules for this lab: upload only masked copies (evidence/lab-502_origin-down_2026-11-09_masked.har has no cookies, no Authorization header and no personal IP, checked in E-093); never upload a HAR of an Access login session (it would carry the CF_Authorization cookie, which is a session credential). Same rule for the runbook.
What to look for in the 502 HAR to cross-check the reading in E-093: filter 5xx (one entry: GET /, 502, headers Server-Timing cfEdge;dur=32,cfOrigin;dur=62, retry-after 60, cache-control no-store); the /cdn-cgi/ assets with status 200 (served by Cloudflare); the favicon.ico 404 with cf-cache-status STALE and Age 15247.

## E-104 — Reference: har-analyzer.dev and local options for reading a HAR (page read, 20:30 CST)
Source: https://har-analyzer.dev (URL given by the author; page text read through a fetch).
What the site says about itself (its own claims, NOT verified by me): "local-first": the analysis runs entirely in the browser, the HAR file is not sent anywhere, no account, uploads are "saved in this browser". Features listed: request timing, payloads, redirects, server timing and TTFB breakdowns, slow endpoints, large payloads, caching issues, blocking JavaScript, waterfall stalls; exports to k6 scripts, JMeter JMX files, CSV and report snapshots; a "HAR Guard" CI automation page for developers. Differences with Google's tool (E-103): this one claims local processing (Google's page does not say) and shows Server-Timing explicitly; it also stores uploads in the browser, so a HAR stays in the browser's storage after use.
How to verify the "no upload" claim without trusting it: open Safari's Web Inspector (Network tab) before uploading the file and check that no request carries the file while the analysis runs (the page itself still has to be downloaded from the internet; only the processing is claimed to be local).
Local options that need no analyzer site: (1) Safari's Web Inspector re-imports a HAR (the "Importar" button seen next to "Exportar" in the screenshots of E-093); Chrome and Firefox also open HAR files in their Network panel (drag the file in). (2) A short Python script on the Mac that prints status, method, URL, time, cache status and Server-Timing for each entry (the same kind of reading done for E-093); it needs python3 on the Mac. (3) A JSON-aware text editor.
Honest note about asking Claude to read the file: that is not offline. The content that Claude prints back into the conversation is processed by the model and leaves the machine; what stays local is only what the author reads himself.
Rule unchanged: only masked HARs; never an Access-login HAR.

## E-105 — Tool: scripts/har_summary.py (local HAR reader), written and tested (20:35 CST)
What it is: a small Python script placed next to the HAR files in `evidence/`, requested by the author to read HARs offline. It uses only the Python standard library, opens no network connection and never modifies the HAR. Run: `cd <project-folder>/evidence` then `python3 har_summary.py` (it picks the `*_masked.har` file in its folder; an explicit file can be passed as an argument).
What it prints: file name, creator and HAR version, number of requests, start time in UTC and CST; one line per request (index, status, method, URL, total ms, cf-cache-status, Age, Server-Timing); flags for any status 400 or higher and for STALE responses; and a sensitive-data check (counts of requests with Cookie or Authorization headers, responses that set cookies, mentions of CF_Authorization) with a warning not to upload or share a file that has credentials-like data.
Test: run in Claude's local workspace (the Linux VM tied to the author's connected folder) on the masked HAR of E-093. Output matched the reading of E-093: 8 requests; #1 GET / 502 (578 ms, Server-Timing cfEdge;dur=32,cfOrigin;dur=62); #2-#7 the /cdn-cgi/ assets, 200; #8 favicon.ico 404 with cache STALE and Age 15247; flags #1 502, #8 404 and #8 STALE; sensitive-data check all zeros.
Limits: it was not run on the author's Mac yet (needs python3 there; if macOS asks to install developer tools, decline); the `cf-cache-status` column shows "-" for responses that do not carry the header (the 502 page and the Cloudflare error-page assets have none, consistent with E-093). The check detects headers and the CF_Authorization string; it does not search for personal data such as an IP or an email, so a manual look is still needed before sharing.

## E-106 — har_summary.py run on the author's Mac, and a Safari Web Inspector detail of the injected analytics script (terminal + screenshot, 20:30 CST)
Source: the author's Mac terminal output (pasted as text) and a screenshot of Safari's Web Inspector, Network tab.
1) Script on the Mac: `cd <project-folder>/evidence` and `python3 har_summary.py` (prompt time 08:26:04 PM). The output is identical, line by line, to the output obtained in Claude's workspace (E-105): 8 requests; #1 GET / 502 (578 ms, Server-Timing cfEdge;dur=32,cfOrigin;dur=62); #2-#7 /cdn-cgi/ assets 200; #8 favicon.ico 404 STALE age 15247; same three flags; sensitive-data check all zeros. Facts: python3 exists on the author's Mac, the script runs there without installing anything, and the result is reproducible on two different machines. the author notes it was the first time he sees a HAR file, finds it useful, thinks the script gives the important details and suggests extending it with more of the information a HAR holds.
2) Safari screenshot (page "Lab site" above; Network list: lab.jdjagustin-lab.dev, style.css, a hash-named script, and two `rum` entries; detail panel with tabs Previsualizar, Encabezados, Cookies, Tamaños, Tiempo, Seguridad). Details of the selected script: URL `https://static.cloudflareinsights.com/beacon.min.js/<site token, masked>`; Estado 200; Fuente: "Caché de memoria"; Iniciador `lab.jdjagustin-lab.dev:11`; Solicitud: "Ninguna solicitud, se sirvió desde la caché de la memoria." Response headers shown: Access-Control-Allow-Origin `*`, Cache-Control `public, max-age=86400`, Content-Encoding `gzip`, Content-Type `text/javascript;charset=UTF-8`, Cross-Origin-Resource-Policy `cross-origin`, Date `Tue, 10 Nov 2026 01:58:01 GMT` (= 19:58:01 CST, the moment of the page load recorded in E-098), ETag `W/"2026.10.1"`, Last-Modified `Thu, 15 Oct 2026 18:26:54 GMT` (more headers below the visible part).
Facts: this confirms the inference of E-096: the extra script is Cloudflare's Web Analytics beacon (beacon.min.js from static.cloudflareinsights.com), injected at line 11 of the page. "Source: memory cache" is the BROWSER's cache: Safari sent no request at all for it this time. This is a second, different cache layer from the Cloudflare edge cache that the HIT/MISS/STALE statuses describe. The two `rum` entries are the analytics beacon's reports (types differ in the list; not inspected).

## E-107 — har_summary.py v2: five extensions added and tested (about 20:45 CST, time approximate)
Requested by the author ("dale a las 5 sugerencias"). File: `scripts/har_summary.py` (standard library only, offline, never modifies the input; the two output-writing options refuse to overwrite an existing file).
Options added to the default table/flags/hygiene view:
1. `--detail N`: everything about request N (method, URL, start time in UTC and CST, status, sizes, ALL request and response headers, timings, and for HTML the title and the first characters of the body). Values of Cookie, Authorization, Proxy-Authorization and Set-Cookie headers are printed as "<hidden by har_summary>".
2. `--timings`: per-request breakdown (blocked, dns, connect, ssl, send, wait/TTFB, receive) and, when the response has a Server-Timing header, a comparison "Cloudflare edge + origin" versus "wait minus that" (network and queueing, approximate).
3. New columns in the table: size in bytes, content-encoding and content type; plus status-class counts, total content size, wall-clock span and the slowest request.
4. `--redact OUT.har`: writes a masked copy: removes Cookie/Authorization/Proxy-Authorization request headers, Set-Cookie response headers, cookie lists and form bodies; masks URL secret parameters (meta, kid, token, code, state, sig, signature, access_token, id_token, key, jwt), JWTs, CF_Authorization values, e-mail addresses (also URL-encoded) and IPv4 addresses; it KEEPS each entry's `serverIPAddress` (that is the Cloudflare edge address, not personal data); validates that the result is still JSON; prints counts. Automatic masking is best effort (it can also hit four-part version numbers such as those in some user-agent strings).
5. `--csv OUT.csv`: exports the table with all timing columns (floats rounded to one decimal).
The hygiene check now reports e-mail-like strings and separates server addresses from other IPv4-like strings.
Tests run in Claude's local workspace on the masked HAR of E-093 (default view, --timings, --detail 8, --csv, --redact) and on a SYNTHETIC HAR built for the purpose with fake secrets (a Cookie with CF_Authorization, an Authorization bearer, Set-Cookie, a form body with a password, an e-mail in plain and URL-encoded form, a JWT in `meta=`, an IP in a header and in the body). Results: before redaction the check reported the credentials-like data and advised not to share; `--redact` removed 6 headers/cookie lists/form bodies, masked 4 URL secret parameters, 1 plain and 1 encoded e-mail and 2 IPs, kept the server address; a text search of the masked file for every fake secret returned nothing; the summary of the masked file reported all zeros; running `--redact` on the already masked real HAR changed nothing (same entries, server address kept). The synthetic files were deleted after the test.
A bug found while testing: the first version of the hygiene check flagged the Cloudflare edge address (104.21.51.133, present in the `serverIPAddress` field of all 8 entries) as "personal data". Fixed by treating that field separately. The real HAR now reports 8 server addresses (one distinct: 104.21.51.133, the same address `dig` returned in E-042) and 0 other IPs.
Limits: not yet run by the author on his Mac in this v2 form (v1 ran there, E-106); the masked copy of a real HAR with cookies has only been tested with the synthetic file; masking patterns do not catch every possible secret, so always read the result before sharing.

## E-108 — Dashboard Observability exports (chart + logs JSON/CSV) analyzed and cross-checked with the HAR (21:03 CST)
Source: Cloudflare dashboard > Observability ("New") > Request outcomes over time (window 19:39-20:39 CST; chart legend: Mitigated 0, Served by Cloudflare 39, Served by Origin 42) and Logs (exports taken 20:42-20:43 CST). the author asked whether this resembles a HAR and whether har_summary.py extracts it.
Files (masked copies in `evidence/`): `cf-observability-logs_2026-11-09_1940-2015CST_masked.json` and `.csv`; `cf-request-outcomes_2026-11-09_1939-2039CST.json` and `.csv` (chart data, no personal data). Masking: client IP replaced by x.x.x.x (81 rows) and the 32-hex hash in one `/avatar/<hash>` path (Grafana avatar; it looks like a hash of the e-mail, not verified). The originals stay only where the author downloaded them.
Fields in the logs export (9): datetime, clientRequestHTTPMethodName, clientRequestHTTPHost, clientRequestPath, edgeResponseStatus, cacheStatus, clientIP, clientCountryName, originResponseStatus. No headers, no timings, no sizes, and NO Ray ID column in this export.
Not a HAR: HAR = the browser's view of one page load (nested JSON `log.entries`); these logs = Cloudflare's edge view of every request. har_summary.py cannot read them (by its code it looks for the `log` key; not run against these files). New script written for them: `scripts/cf_logs_summary.py`.
Checks run (Claude's workspace, python):
1. JSON and CSV logs hold the same 81 rows; chart totals 39 + 42 + 0 = 81 = number of log rows.
2. Observed rule for the chart categories: in every minute, "Served by Origin" equals the rows with cacheStatus `dynamic`; "Served by Cloudflare" equals all other rows (hit, stale, revalidated, none). No minute disagreed. Rule inferred from this export, not taken from Cloudflare documentation.
3. Consequence: the 42 "Served by Origin" include 3 failures (one 502 and two 530). It does not mean 42 successful origin answers.
4. Hosts: 60 rows grafana.jdjagustin-lab.dev, 21 rows lab.jdjagustin-lab.dev. cacheStatus: dynamic 42, none 15, hit 15, revalidated 6, stale 3.
5. The two outages differ in the logs: 502 has originResponseStatus 502 (cloudflared answered, origin down); the two 530 have originResponseStatus 0 (no origin response, tunnel stopped).
6. Cross-check with the HAR of E-093: the 8 log rows at 01:40:22-23Z (19:40 CST) match the 8 HAR entries (502 on `/`, `/cdn-cgi/styles/main.css`, 5 `/cdn-cgi/images/*.png`, `/favicon.ico` 404 `stale`); cache status agrees (`none` for /cdn-cgi/ assets, `stale` for the favicon).
7. Other events visible: 19:48 CST two HEAD /style.css `stale` with the origin down (E-094); 19:58 CST GET /style.css `revalidated` with origin 304 (E-098); 20:00:11 CST GET and HEAD `/` = 530 plus HEAD /style.css `hit` (E-097); `/api/live/ws` = 101 with origin 101 (WebSocket upgrade passes through the tunnel).
8. One 302 (GET grafana /public/img/grafana_mask_icon.svg, cache none, origin 0) was answered by Cloudflare without contacting the origin. Hypothesis, NOT verified: the Access redirect for a request without the session cookie. To verify: read the Location header or the Access authentication log.
9. Time zones: exports are in UTC (Z); the chart and the dashboard show GMT-6. 01:40Z = 19:40 CST.
Cleanup question closed: the `grafana` CNAME and its Access application are meant to stay (the private cleanup checklist steps 4, 7, 9 and 10 already say so); only `lab` is temporary.
Limits: one hour of traffic from one client (the author's IP, MX), about 81 requests; the export has no Ray ID, so HAR-to-log matching used time + path; not tried: other Observability sections, Logpush.
Tool tests of cf_logs_summary.py: default view and `--timeline` on the masked CSV; `--host` filter on the masked JSON; hygiene check on the unmasked original (reported 1 real IP, 1 avatar hash, advised --redact); `--redact` on both original formats (81 IPs and 1 hash masked, re-check reports 0, JSON still valid); a HAR-like file is rejected with a clear message; the script then ran from the Mac folder (`python3 -I cf_logs_summary.py`, 81 rows, same output).

Beacon clarification (21:10 CST, the author asked whether the injected `beacon.min.js` produces this data): No. The Web Analytics beacon runs in the visitor's browser (navigation timings, Core Web Vitals) and posts them to `/cdn-cgi/rum` (204); that feeds Web Analytics, not Observability. Observability logs are produced by Cloudflare's edge for every request with no script on the page: the export contains Cloudflare-generated 502/530 error pages and non-HTML files, and fields only the edge knows (cacheStatus, originResponseStatus, country). The beacon only leaves its footprint as 8 rows `POST /cdn-cgi/rum` 204, cache none, origin 0 (4 on lab, 4 on grafana in the masked CSV; answered by Cloudflare itself). Three views of one request: HAR = browser, Observability = edge, Web Analytics = visitor-side beacon. Consistent with E-096 (beacon injected at line 11 of the HTML, two `rum` calls per visit).


## E-109 — The 302 on grafana_mask_icon.svg is the Cloudflare Access redirect (VERIFIED, 21:13 CST)
Closes the open hypothesis of E-108 check 8. the author ran `curl -sI https://grafana.jdjagustin-lab.dev/public/img/grafana_mask_icon.svg` from his Mac (no session cookie). Masked copy: `evidence/curl-302-grafana-mask-icon_2026-11-09_2113CST_masked.txt` (kid, JWT, session cookie and NEL endpoint masked).
Facts from the response: HTTP/2 302; `location:` points to `<team-name>.cloudflareaccess.com/cdn-cgi/access/login/grafana.jdjagustin-lab.dev` with `redirect_url=/public/img/grafana_mask_icon.svg`; `www-authenticate: Cloudflare-Access ...`; `set-cookie: CF_AppSession` (HttpOnly, Secure); `cache-control: private, no-store`; `server: cloudflare`; `cf-ray` present (ends in -DFW, the edge data center).
Decoded `meta` token: hostname grafana.jdjagustin-lab.dev, `auth_status: NONE`, `mtls_auth.cert_presented: false`, `real_country: MX`, `service_token_status: false`.
Reading: the whole hostname `grafana` is protected by Access, not only one path, so an unauthenticated request to any file (even a static icon) is answered by Cloudflare with a redirect to the login and never reaches the tunnel or the origin. That is why the logs show edge 302, cache none, origin 0. Consistent with the Access setup of the earlier pieces.
Side lessons: (1) a cf-ray header gives the Ray ID that the Observability export lacks, so a `curl -I` is a way to get a Ray ID to search in the logs; (2) the `kid`/`meta` values are session-specific tokens: mask them before sharing; (3) the Cloudflare edge answered from DFW (Dallas) for a client in Mexico.
Still open: the Ray ID column in the Observability export; the Access authentication log was not consulted (not needed, the header evidence is direct).


## E-110 — The panel's log detail has 11 fields; the export had 9 (rayName and securityAction missing) (21:23 CST)
Source: two screenshots from the author of the expanded log rows in Dashboard > Observability (rows: 20:15:21 POST grafana `/cdn-cgi/rum` 204 cache none origin 0; 20:09:23 GET grafana `/api/search` 200 cache dynamic origin 200). Screenshots NOT stored: they show the real client IP unmasked. Facts below were copied from them (Ray IDs are not personal data).
Fields shown in the panel (11): securityAction, rayName, originResponseStatus, edgeResponseStatus, datetime, clientRequestPath, clientRequestHTTPMethodName, clientRequestHTTPHost, clientIP, clientCountryName, cacheStatus. The earlier export had 9: the same list without securityAction and rayName. Inference (not yet tested): the export contains the columns selected under the panel's "Fields" button, so adding rayName and securityAction there before exporting should include them.
Ray IDs seen: `a5818c88c8f29d60` (the 20:15:21 rum row, present in the masked CSV at 02:15:21Z) and `a58183ccb8196b47` (the 20:09:23 `/api/search` row). `rayName` is the same value as the `cf-ray` response header without the data-center suffix (curl in E-109 showed `a581e1f6d8c1e98b-DFW`; `rayName` holds the 16 hex characters only), so a Ray ID from a HAR or curl can be matched to a log row exactly, instead of by time + path as in E-108.
`securityAction: unknown` on both rows (no WAF/rate-limit rule matched); this field is what would show a block or challenge on mitigated requests (the chart legend said Mitigated 0).
Open: add the two columns, export again and check; then cf_logs_summary.py needs optional rayName/securityAction support (today it reads only the 9 fields).


## E-111 — First real Cloudflare API calls with a scoped read-only token (22:20 CST)
What ran: the author created a custom API token `lab-readonly` (all permissions Read: DNS, Zone, Zone Settings, Zone Observability, Analytics, Logs; scope only the zone jdjagustin-lab.dev; expiry 7 days, until 2026-11-16 23:59 CST; no IP filter). While building it, the first draft had DNS **Edit** (write) ticked; Claude spotted it in the screenshot and the author corrected it to Read before creating the token. The summary screen was reviewed: only Read permissions.
Calls (from the author's Mac, token kept in a shell variable with `read -s`, never pasted in chat): (1) `GET /user/tokens/verify` -> success true, status active. (2) `GET /zones?name=jdjagustin-lab.dev` -> zone id. (3) `GET /zones/<id>/dns_records` -> two CNAME records, `grafana` and `lab`, both proxied=True, ttl=1 (Automatic), both pointing to the same tunnel `<uuid>.cfargotunnel.com`. Masked copy: `evidence/api-call-1-dns-records_2026-11-09_2220CST_masked.txt`.
Honest scope: these are read calls only (no change made through the API yet). The token string and zone id were not saved anywhere. Cloudflare's own suggested `curl` puts the token in the command line (shell history), so the author used a variable instead.
Cleanup (added to the plan): revoke the token in Dashboard > My Profile > API Tokens at the end, `unset CF_API_TOKEN ZONE_ID`, and delete any history line that contains the token if he ran Cloudflare's suggested curl.
Next: second call (read SSL/TLS mode via `/zones/<id>/settings/ssl`), then decide Terraform.


## E-112 — Second API call: the zone's SSL/TLS mode read through the API (22:22 CST)
Call: `GET /zones/<id>/settings/ssl` with the read-only token. Copy: `evidence/api-call-2-ssl-setting_2026-11-09_2222CST.txt`.
Result: `value: full`, `certificate_status: active`, `validation_errors: []`, `editable: true`, `modified_on: null`, `success: true`.
Cross-check: matches E-049, where the dashboard showed "Current encryption mode: Full" under Automatic SSL/TLS. `modified_on: null` fits that: nobody changed the setting by hand; Cloudflare's automatic mode chose it. Correction of a statement made in chat at 22:21 ("lo que configuramos en el dashboard"): the value was not set by us, it came from Automatic mode.
Meaning of the values: Full = Cloudflare connects to the origin over HTTPS without requiring a publicly valid certificate; Full (strict) would require one. In this lab the origin hop goes through the tunnel (cloudflared speaks HTTP to localhost), see E-049.
Scope: two read-only list/get calls so far (DNS records, SSL setting) plus the token verify. Still no change made through the API.


## E-113 — API write cycle: create, read and delete a DNS record through the Cloudflare API (22:36-22:50 CST)
What ran (the author, own Mac, second terminal window, second token): token `lab-dns-edit` (permission DNS: Edit, only the zone jdjagustin-lab.dev, expiry 2026-11-10 23:59 CST; verified active). Cycle on a throwaway TXT record `api-test.jdjagustin-lab.dev`:
1. POST create (22:46): success true, TXT with ttl 120. A first attempt at 22:36 failed with error 7003 because the variable ZONE_ID was empty in the new window (URL `/zones/dns_records`); nothing was created. Fixed by copying the Zone ID from Overview > API (32 characters, checked with `echo ${#ZONE_ID}`); a typo with a space after `export ZONE_ID=` was also corrected.
2. GET by id (22:47): same record; `dig +short TXT` returned the content about 80 seconds after creation (the zone uses Cloudflare DNS).
3. DELETE by id (22:49): success true, same id.
4. Verification (22:50): `dig +short TXT` empty; list of records = only the `grafana` and `lab` CNAMEs (both proxied).
Files in `evidence/`: api-call-3-create-txt, api-call-4-read-and-dig, api-call-5-delete-txt, api-call-6-verify-clean (record id masked in 3-5).
Why it matters: this is the first change made through the API (write call), reversible and scoped; the token had least privilege (one permission, one zone, 1-day expiry). With E-111 and E-112 (reads) it supports the statement "ran Cloudflare API calls: verify token, list records, read zone setting, create/read/delete a DNS record with scoped tokens".
Honest limits: done by hand with curl, not a script or pipeline; only DNS records on a free-plan lab zone; no error handling, pagination, rate-limit handling or CI. Terraform (Option B) is still pending.
Cleanup still pending: revoke `lab-dns-edit` now (no longer needed) and `lab-readonly` at the end; `unset CF_API_TOKEN CF_API_TOKEN_EDIT ZONE_ID RECORD_ID` in both windows.


## E-114 — Terraform installed on the Mac (00:10 CST, 2026-11-10)
the author chose to keep Terraform installed permanently (he will use it in other projects). Checks before: Homebrew present (`/opt/homebrew/bin/brew`), `uname -m` = arm64, Terraform not installed. Install: `brew tap hashicorp/tap`, `brew install hashicorp/tap/terraform` (official HashiCorp tap; the core Homebrew formula is frozen on an old version). Result: `Terraform v1.17.1 on darwin_arm64`. File: `evidence/terraform-install_2026-11-10_0010CST.txt`.
Side effects noted: Homebrew updated its own index; no other package was upgraded; an unrelated tap (romkatv/powerlevel10k) shows a "not trusted" warning that was already there. Removal commands are in the file and in the private cleanup checklist (only if the author decides to remove it).
Scope: this proves the tool is installed, not yet that any infrastructure was managed with it. Next: exercise folder, provider, init/plan/apply/destroy on one throwaway TXT record with a short-lived DNS Edit token.


## E-115 — First Terraform run: init, plan, apply, verify, destroy on one throwaway DNS record (00:18-00:34 CST, 2026-11-10)
What ran (the author, own Mac, Terraform v1.17.1, provider cloudflare/cloudflare v5.28.1): folder `terraform-exercise/` with a `main.tf` (copy in `evidence/terraform-main.tf.txt`) that declares ONE resource `cloudflare_dns_record.tf_test` (TXT `tf-test.jdjagustin-lab.dev`, ttl 120). Token `lab-terraform` (DNS Edit, only this zone, 7 days) passed through the environment variable CLOUDFLARE_API_TOKEN (never in a file); zone id through TF_VAR_zone_id.
Timeline: 00:18 `terraform init` OK (provider downloaded, lock file) | 00:24 `terraform plan`: 1 to add, 0 to change, 0 to destroy | 00:30 `terraform apply` (typed yes): 1 added, created in 1 s | 00:32 `dig +short TXT` returned the text exactly as written, `terraform state list` showed only the one resource | 00:34 `terraform destroy` (typed yes): plan showed 0 to add, 0 to change, 1 to destroy, destroy complete in 1 s; `created_on` 06:30:22Z matches the apply.
Files in `evidence/`: terraform-install, terraform-1-init, terraform-2-plan, terraform-3-apply, terraform-4-verify, terraform-5-destroy, terraform-main.tf.txt (ids masked).
What it supports honestly: "installed Terraform and ran the init/plan/apply/destroy cycle with the Cloudflare provider against a real zone, managing a DNS record as code with a scoped token". Design choices worth saying: the real records grafana and lab were NOT imported (a destroy would delete them); the token comes from the environment; the state files and .terraform are excluded from git by .gitignore; the token was short-lived and scoped to one permission and one zone.
Limits (do not overclaim): one resource only, local state (no remote backend, no locking), no modules, no variables files for environments, no CI pipeline, no import of existing infrastructure, no drift detection test, no Terraform for WAF/rules/Access/tunnels, only a beginner cycle on a free-plan lab zone.
Verified clean at 00:37 CST (`evidence/terraform-6-verify-clean_2026-11-10_0037CST.txt`): `dig` empty and the zone lists only the grafana and lab CNAMEs (proxied). Exercise CLOSED at 00:40 CST: token lab-terraform deleted in the dashboard, variables unset (env check = 0), `.terraform/` and `terraform.tfstate*` deleted (`evidence/terraform-7-local-cleanup_2026-11-10_0040CST.txt`). Terraform itself stays installed by the author's choice.


## E-116 — Cache Rule exercise, step 1: the "before" (01:25 CST, 2026-11-10)
What ran (the author, Mac terminal): `curl -sI "https://lab.jdjagustin-lab.dev/" | grep -i -E "^(HTTP|cf-cache-status|age|cache-control|cf-ray)"` twice in a row. File: `evidence/cache-rule-1-before_2026-11-10_0125CST.txt`.
Result: both `HTTP/2 200`, both `cf-cache-status: DYNAMIC`, no `age`, no `cache-control`; Ray IDs `...067b-DFW` and `...3aa6-DFW` (different per request; suffix = Dallas data center).
Meaning: DYNAMIC = Cloudflare decided this response is not eligible for cache (HTML is not in the default cached extensions), so it forwards the request to the origin every time. It does NOT prove the content is generated dynamically (it is a static file served by Python http.server). Cache is stored per data center (colo), the one that received the request.
Next: create a Cache Rule only for hostname `lab.jdjagustin-lab.dev` (eligible for cache), repeat the curl twice (expect MISS then HIT), then delete the rule and add it to the private cleanup checklist.


## E-117 — Cache Rule exercise, step 2: custom Cache Rule makes the HTML cacheable (01:49 CST, 2026-11-10)
What was done: in Dashboard > Caching > Cache Rules, rule `lab-cache-html`: filter Hostname equals `lab.jdjagustin-lab.dev` (first attempt used the field "URI Full", which would never have matched; caught before Deploy), Cache eligibility = Eligible for cache, Edge TTL = ignore cache-control and use 2 hours (Free plan minimum), Browser TTL untouched. Deployed about 01:48 CST.
Test (the author, Mac terminal): the same curl as E-116, twice. File: `evidence/cache-rule-2-after_2026-11-10_0149CST.txt`.
Result: 1st request `MISS`, 2nd request `HIT` with `age: 0`, both from DFW. Before the rule (E-116) both were `DYNAMIC`.
Also seen: `cache-control: max-age=14400` in the response although the origin sends none. Most likely Cloudflare adds it from the zone Browser Cache TTL default (4 h); inference, not tested.
What it supports: "created a Cache Rule scoped to one hostname, saw the HTML go from DYNAMIC to MISS then HIT, and understood why a rule can validate and still not match (wrong field)". Limits: Free plan, one hostname, static page, no cache key/Vary/purge-by-tag tests, no Tiered Cache, no origin-log comparison for this rule yet.
Exercise CLOSED at 01:54 CST: rule deleted, Purge Everything run (both by the author's report), and the same curl twice returned `DYNAMIC` both times with no cache-control header (`evidence/cache-rule-3-after-cleanup_2026-11-10_0154CST.txt`). Note: the `cache-control: max-age=14400` header disappeared with the rule, so it is more likely tied to the rule's cache settings than to the zone Browser Cache TTL default; I wrote the zone-default explanation above as an inference and it is not confirmed.


## E-118 — Observability export of the Cache Rule test, and the Fields dialog (02:02-02:04 CST, 2026-11-10)
What the author did: opened Observability > Logs (HTTP requests, All domains, Last 1 hour), exported the 6 rows as CSV at 02:02 CST, and opened the Fields dialog. Files: `evidence/observability-cache-rule_2026-11-10_0202CST_masked.csv` (client IP replaced by `<client-ip>`; the original export stays in his Downloads folder with the real IP). Screenshots not saved (they show part of his account name).
Edge-side view of E-116/E-117 (times in UTC, CST = UTC-6): 07:25:13 and 07:25:14Z two `dynamic` (originResponseStatus 200) = the "before"; 07:49:11Z `miss` (origin 200) then `hit` (origin 0) = the rule working; 07:54:11Z two `dynamic` (origin 200) = after deleting the rule and purging. The `hit` shows originResponseStatus 0: that request never reached the origin. This matches the terminal outputs, from an independent source (Cloudflare's own logs).
Fields dialog: 33 fields available; 8 were selected (HTTP method, Host, Path, Edge status code, Cache status, Source IP, Country, Origin status code), which is exactly the set of columns in the export (plus datetime). So the export follows the selected columns. `Ray ID` (rayName) and `Security Action` (securityAction) exist in the list but were NOT yet selected. Other fields seen in the list: Security Source, Origin response duration (ms), Source user agent, SSL Protocol, Content type, Session ID hash, among others (not all read).
Limits: HEAD requests only (curl -I), 6 rows, one hostname; the purge itself does not show in these logs.
Next: add Ray ID and Security Action with the + button, export again, check the CSV has the two new columns, then update `scripts/cf_logs_summary.py`.


## E-119 — Ray ID and Security Action columns work; curl cf-ray values match the logs' rayName (02:10 CST, 2026-11-10)
What the author did: in Observability > Logs > Fields he selected `Ray ID` (rayName) and `Security Action` (securityAction) (10 fields selected; the list then shows 31 more), and exported the CSV again. File: `evidence/observability-cache-rule-with-rayname_2026-11-10_0210CST_masked.csv` (client IP masked; the original stays in his Downloads folder). Screenshot not saved (shows part of his account name).
Result: the export now has 11 columns, the two new ones right after datetime. `rayName` is the cf-ray header without the data-center suffix; all 6 `cf-ray` values copied from the curl outputs of E-116/E-117 (`...-DFW`) match the 6 `rayName` values in the logs exactly (checked with a script: 6 of 6 matched, none left over on either side). So one request can be followed from the terminal to Cloudflare's own log by its Ray ID. `securityAction` is `unknown` on all 6 rows; these requests triggered no security rule, but I have not confirmed what the label means beyond that (a blocked request, like the WAF test of E-049, should show a different value; not tested here).
Script: `scripts/cf_logs_summary.py` now reads the two optional columns and has a new `--rays` option (one line per request with its Ray ID); an export without those columns still works (checked with the previous export). The previous version of the script was archived in an archive folder
Limits: 6 HEAD requests, one hostname, the 1-hour window; securityAction values other than `unknown` not seen in this export.

## E-121 — RUNBOOK.md extended with 3 sections that did run (2026-11-10, ~03:58 CST)
Text work only, nothing executed. New sections in `docs/RUNBOOK.md`: 8 DNS check with dig (from E-042), 9 cloudflared upgrade via dpkg (from E-010, E-011, E-012), 10 Observability logs and HAR (from E-093, E-105 to E-108, E-118, E-119 and the HOWTO). Old sections 8 and 9 became 11 and 12; triage table got 3 rows. Limits: in section 8 only the "resolves to Cloudflare addresses" case was observed; NXDOMAIN and DNS-only cases are marked as general knowledge. Section 9 rests on documentation read through snippets. Runbook now 124 lines, 12 sections; none of it used in production.

## E-122 — Piece 2, step 1: official docs read for errors 1016, 520-526 and SSL/TLS modes (web fetch, 2026-11-10 ~04:15 CST)
Source: Cloudflare docs pages fetched one by one (summaries by the fetch tool, not the full raw text): developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1016/ ; .../cloudflare-5xx-errors/error-520/ to error-526/ ; developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full/ and /full-strict. The 5xx index page lists titles only. Nothing was executed or changed in the lab.
Facts (what the docs say):
- 1016 "Origin DNS error": Cloudflare cannot resolve the origin's IP address. Listed causes: the origin A record is missing; a CNAME in Cloudflare DNS points to an external domain that does not resolve; unresolvable hostnames in Load Balancer pools; Spectrum CNAME origin without its record; Workers fetch to a hostname without a record in a Partial (CNAME) zone; SSL for SaaS custom hostname problems. Fix: confirm the record points to a valid IP / that the CNAME target resolves. The page I read does NOT mention Cloudflare Tunnel or a deleted tunnel; the tunnel DNS-records page I fetched was truncated and did not show it either. So "1016 appears when the tunnel was deleted" is NOT confirmed by documentation (my earlier runbook text says "documented"; check wording).
- 520 empty/unknown/unexpected response from origin (crash, firewall blocking Cloudflare IPs, response headers over 128 KB, HTTP/2 misconfig, Authenticated Origin Pull mismatch). Log hint: OriginResponseStatus 0 with CacheStatus miss/expired = failed origin connection.
- 521 origin refused the connection (app offline, or origin security blocking Cloudflare IPs; wrong port: 80 for Flexible, 443 for Full/Full strict).
- 522 connection timed out: no SYN+ACK within 19 s, or no ACK for the request within 90 s (blocking/rate limiting of Cloudflare IPs is the most common cause; overloaded origin; DNS record IP not matching the server).
- 523 origin unreachable: no route from a network device to the origin IP (AWS VPC route example with 172.64.0.0/13).
- 524 origin connected but no HTTP response within 125 s Proxy Read Timeout (30 s Proxy Write Timeout); Enterprise can raise to 6000 s.
- 525 SSL handshake failed between Cloudflare and origin, with SSL mode Full or Full (strict) (no valid cert, port 443 closed, no SNI, cipher mismatch).
- 526 invalid SSL certificate: origin certificate fails validation in Full (strict). Quick fix in docs: switch to Full; proper fix: valid cert or Cloudflare Origin CA certificate.
- Full: encrypts visitor-Cloudflare and Cloudflare-origin; the origin certificate is NOT validated in any way (can be expired, self-signed, wrong hostname); origin must still accept HTTPS on 443 or visitors may get 525. Full (strict): adds validation (unexpired, signed by a public CA or Cloudflare Origin CA, CN/SAN matches hostname); failure gives 526.
Limits: summaries via the fetch tool; Flexible and Off were not described by the pages read; nothing here was reproduced.
Reproducibility in THIS lab (my assessment, not tested): origins sit behind a Tunnel, so origin failures show as 502/530 (E-091, E-097), not 520-524. 525/526 and 520-524 need a proxied A/AAAA record to a public origin IP, which the lab does not have. 1016 can be tried with a proxied CNAME to a name that does not resolve.

## E-123 — Piece 2: CGNAT check for using CloudSpartan as a public origin (terminal + router screenshot, 04:13-04:23 CST)
Source: the author's terminal output pasted as text and a screenshot of his home router (Arris, WAN Setup > Dynamic, "Dynamic Configuration Settings"). Read-only; nothing was changed.
Facts:
- On CloudSpartan, `curl -s https://ifconfig.me` returned a public IPv4 address <public-ip> (the value stays only in his terminal; not written to files).
- The router's WAN page shows the router's WAN address obtained by DHCP in a PRIVATE range (10.x.x.x, subnet mask <ip>, gateway also in 10.x.x.x). It is NOT the same address as <public-ip>.
- Interpretation (mine, standard networking): the WAN address is private, so the ISP does NAT before the internet (carrier-grade NAT). A port-forward on his router cannot make CloudSpartan reachable from outside, so Cloudflare could not connect to it with an IPv4 A record. Not proven by a connection test; it follows from the two addresses differing and the WAN one being private.
- The screenshot also shows tabs "Dynamic (IPv6)" and "Static (IPv6)"; whether the ISP delivers a global IPv6 address to CloudSpartan was NOT checked.
Files: screenshot saved PRIVATE (router admin page): `evidence/screenshots_PRIVATE_originals/E-123_router_wan_setup_2026-11-10_0423CST.png`. Not for the repo (shows ISP internal addressing).
Consequence: the "port-forward to CloudSpartan" route is closed for IPv4. Options not yet decided: (A) check IPv6 reachability, (B) a temporary small cloud VM with a public IP, (C) keep 520-526 as documentation study only.

## E-124 — Piece 2: IPv6 check for CloudSpartan as a public origin (terminal + router screenshot, 04:26 CST)
Source: the author's terminal output and a screenshot of the router's "Dynamic Configuration Settings (IPV6)" page. Read-only; nothing changed.
Facts:
- On CloudSpartan, `curl -6 -s --max-time 8 https://ifconfig.me` printed nothing (no output within 8 s). With `-s` the tool is silent on failure, so the exact failure reason was not seen; it means no IPv6 answer was obtained.
- The router's IPv6 page shows DHCPv6 enabled, "IP Address V6" `::` (empty), "Delegated Prefix" `::` with length 0, and only a link-local gateway address (FE80::...). So the router has not received a global IPv6 address or a delegated prefix from the ISP.
- Interpretation: no usable global IPv6 for CloudSpartan on this connection now. Combined with E-123 (private WAN IPv4, CGNAT) there is no way to reach CloudSpartan from the internet without a third party. Limit: this is the state at 04:26 CST; the ISP could enable IPv6 later.
Files: screenshot saved PRIVATE `evidence/screenshots_PRIVATE_originals/E-124_router_wan_ipv6_2026-11-10_0426CST.png` (router admin page, not for the repo).
Consequence: options A (home origin via IPv4 port-forward) and IPv6 are closed. Remaining: B) temporary cloud VM with public IP, C) study only.

## E-125 — Piece 2: 1016 experiment, first try returned 1014 instead (terminal + form screenshot, 07:52-07:56 CST, 2026-11-10)
Source: the author's Mac terminal output pasted as text and a screenshot of the Add record form (private: `evidence/screenshots_PRIVATE_originals/E-125_add-record-err1016-a_form_2026-11-10_0752CST.png`).
What was done: DNS record created in the zone: CNAME `err1016-a` -> `no-such-host-lab-test.example.com`, Proxied. PREDICTION written before testing (the initial plan 07:45): error 1016. The prediction was WRONG.
Commands run (Mac): `dig +short err1016-a.<lab-domain>`; `curl -sI https://err1016-a.<lab-domain>/ | grep -i -E "^HTTP|cf-ray|server"`; `curl -s https://err1016-a.<lab-domain>/ | grep -i -E "<title>|error code"`.
Facts (what the output shows):
- dig returned two addresses, 172.67.180.160 and 104.21.51.133: the same two Cloudflare addresses seen for `lab` and `grafana` in E-042 (so the record resolves to Cloudflare, proxied).
- curl: `HTTP/2 403`, `server: cloudflare`, `cf-ray: a5858ec5ac9a92ba-DFW`.
- The error page body contains `error code: 1014`. The `<title>` line did not match the grep (nothing printed for it), so the title was not captured.
- Cloudflare docs (error 1014 page, fetched 2026-11-10): "CNAME Cross-User Banned" = a CNAME between domains in DIFFERENT Cloudflare accounts is prohibited; allowed within one domain, across zones of the same account, or via Cloudflare for SaaS.
Interpretation (mine, NOT verified): the target `example.com` zone is probably hosted on Cloudflare under another account, so Cloudflare answered 1014 before trying to resolve an origin. To verify: `dig +short NS example.com` (should list Cloudflare name servers). The docs match the observed code; the cause is an inference.
Lesson: a CNAME target that "does not exist" is a bad test if its parent domain is itself a Cloudflare zone; the first error you meet can be a policy error (1014) rather than the DNS error (1016). Choosing the target matters.
Verification (07:58 CST): the author ran `dig +short NS example.com`; it returned two Cloudflare name servers (elliott.ns.cloudflare.com and hera.ns.cloudflare.com). So example.com IS hosted on Cloudflare. That it belongs to a DIFFERENT account than the lab's is not visible from here; it is the reading that fits the 1014 documentation (the lab zone cannot be the same account as example.com).
Next step (not done): change the target of `err1016-a` to a nonexistent name INSIDE the lab's own zone (same account) and repeat the three commands; expectation from the 1016 docs: 1016. Cleanup unchanged (records err1016-a and err1016-b in the private cleanup checklist).

## E-126 — Piece 2: 1016 reproduced after changing only the CNAME target (terminal + screenshot, 08:07-08:10 CST, 2026-11-10)
Source: the author's Mac terminal output (text) and a screenshot of the edit panel before Save (private: `evidence/screenshots_PRIVATE_originals/E-126_edit-err1016-a_target-own-zone_2026-11-10_0807CST.png`).
What was changed (one variable): record `err1016-a` stays CNAME + Proxied; target changed from `no-such-host-lab-test.example.com` (E-125, gave 1014) to `no-such-origin.<lab-domain>` (a name that does not exist, inside the lab's own zone). PREDICTION written before the test (the initial plan 08:07): 1016. Confirmed.
Commands run: the same three as in E-125 (dig +short; curl -sI | grep -i -E "^HTTP|cf-ray|server"; curl -s | grep -i -E "title|error code").
Facts:
- dig returned the same two Cloudflare addresses (104.21.51.133 and 172.67.180.160): proxied, as in E-042 and E-125.
- curl: `HTTP/2 530`, `server: cloudflare`, `cf-ray: a585a3e72ba62c85-DFW`, and the body contains `error code: 1016`. So the HTTP status is 530 and the Cloudflare error code is 1016 (the same pairing style as 530 with 1033 in E-097).
- The `title` pattern printed nothing in either run (E-125 and E-126): the page title line was not captured; reason not investigated.
Interpretation: with the target inside the same account and not resolvable, Cloudflare returns the DNS error 1016 as the docs describe (E-122). Changing only the target moved the error from 1014 to 1016, which supports the E-125 reading that the 1014 came from the cross-account target (example.com is on Cloudflare per `dig NS`). Still an inference about the cause of 1014; the controlled change supports it, it is not a statement by Cloudflare.
Addendum (08:18 CST): the author ran `curl -s https://err1016-a.<lab-domain>/` with no filter. The whole body is one line: `error code: 1016`. So for this error, curl receives a plain-text body, not an HTML page; that is why the grep for `title` found nothing in E-125 and E-126. This closes the open question (hypothesis from 08:17 confirmed). Observed for curl only; a browser may be shown a different page (not tested).
Limit: one record, one run each; 1016 with a tunnel target not tested yet (err1016-b next). Record `err1016-a` still exists (cleanup pending).

## E-127 — Piece 2: CNAME to a tunnel that does not exist gives 530 + 1033 (terminal + zone export, 08:22 CST, 2026-11-10)
Source: the author's Mac terminal output (text) and the zone export `jdjagustin-lab.dev-2.txt` (exported 2026-11-10 14:21:27 UTC = 08:21 CST), saved masked as `evidence/jdjagustin-lab.dev_zone_export_WITH-err1016-records_2026-11-10_1421UTC_masked.txt` (the real tunnel id replaced by <tunnel-uuid>; the fake all-zero id kept).
What was created: record `err1016-b`, CNAME to `<uuid>.cfargotunnel.com` (a tunnel id that does not exist), Proxied. The export confirms both test records: `err1016-a` -> `no-such-origin.<lab-domain>` and `err1016-b` -> the fake tunnel id, both `cf-proxied:true`, next to `grafana` and `lab`.
PREDICTION (before testing): "1033 or 1016, docs silent". Half-open prediction; the answer is 1033.
Commands: dig +short; curl -sI | grep -i -E "^HTTP|cf-ray|server"; curl -s (no filter).
Facts:
- dig: the same two Cloudflare addresses as for every proxied record of the zone.
- curl: `HTTP/2 530`, `server: cloudflare`, `cf-ray: a585b550f94efa4d-DFW`; body (one plain-text line): `error code: 1033`.
Interpretation: a proxied CNAME to a tunnel id that does not exist produces the SAME pair (530 + 1033) that a real tunnel with its connector stopped produced in E-097/E-099. So the code 1033 alone does not tell "tunnel down" from "tunnel does not exist" in this lab. To tell them apart you look at the dashboard (Networking > Tunnels: is the tunnel listed, and is it Healthy/Down) rather than at the error. My earlier runbook line implied 1016 for a deleted tunnel; this result contradicts it for a non-existent tunnel id (only tested with an id that never existed, not with a tunnel that was created and then deleted).
Summary of the three codes seen in piece 2 (all with the plain-text body for curl): 1014 (E-125, target in another Cloudflare account), 1016 (E-126, target name that does not resolve), 1033 (this entry, tunnel not found / not connected).
Limits: one run each; a deleted-then-gone real tunnel not tested; browser view not tested. Both test records still exist (cleanup pending).

## E-128 — Where the docs explain the HTTP statuses and error codes seen in piece 2 (web fetch, 08:35 CST, 2026-11-10)
Source: Cloudflare docs pages (fetched one by one; summaries by the fetch tool): Support > Troubleshooting > HTTP status codes: `.../http-status-codes/cloudflare-1xxx-errors/` (index), `.../cloudflare-1xxx-errors/error-1014/`, `error-1016/`, `error-1033/`; `.../http-status-codes/cloudflare-5xx-errors/` (index) and `.../cloudflare-5xx-errors/error-530/`.
Facts (what the pages say):
- 1xxx index: 1xxx errors appear in the HTML body; each one "is returned with the HTTP status code below"; its table maps 1016 (Origin DNS error) and 1033 (Argo Tunnel error) to HTTP 530.
- error-530 page: 530 = Cloudflare "is unable to resolve the origin hostname"; the body has a 1xxx code; it sends the reader to the specific 1xxx page for causes and fixes. It does not name 1016 or 1033.
- error-1033: Cloudflare cannot find a healthy cloudflared instance. Fix by tunnel status in the dashboard (Networking > Tunnels) or `cloudflared tunnel list`: Inactive (connector never run), Down (was connected, process stopped), Degraded (at least one connection failed), Healthy (then check the DNS record points to the correct tunnel subdomain). The page does NOT describe a tunnel id that does not exist (our E-127 test).
- Difference with what we saw: the docs say 1xxx errors appear in the HTML body; with curl we received a one-line plain-text body (E-125 to E-127). Browser view not tested.
- 1014: observed 403 (E-125); the status for 1014 was not read from the docs table in this fetch.
This closes the earlier open point: the link between 530 and the 1xxx codes IS documented.

## E-129 — Piece 2: cleanup of the two test records verified (screenshot + terminal, 08:29 CST, 2026-11-10)
Source: the author's screenshot of the DNS Records list (private copy: `evidence/screenshots_PRIVATE_originals/E-129_dns-records-after-cleanup_2026-11-10_0829CST.png`) and terminal output.
What was done: the author deleted `err1016-a` and `err1016-b` in the dashboard.
Facts:
- The list shows two records, `grafana` and `lab`, both type Tunnel pointing to `lab-tunnel`, Proxied; the banner says "You have used 2 of 200 available DNS records". (The footer text still said "Showing 1-3 of 3", which does not match the two rows; probably a label not refreshed, not investigated.)
- `dig +short err1016-a...` and `dig +short err1016-b...` printed nothing (the names no longer resolve); `dig +short grafana...` returned the two Cloudflare addresses (still alive).
Addendum (08:31 CST): a second screenshot after refreshing (private: `E-129b_dns-records-refreshed_2026-11-10_0831CST.png`) shows the footer now reads "Showing 1-2 of 2", matching the two rows and the banner; so the earlier "1-3 of 3" was a stale label.
Result: piece 2 temporary records are gone; the zone is back to `grafana` and `lab` only (`lab` is the lab's own temporary record, removed at the final cleanup).

## E-130 — Piece 3, prep step 1: Access policy `allow-owner-email` checked (screenshot, 09:50 CST, 2026-11-10)
Source: the author's screenshot of the policy page opened from Zero Trust > Access controls > Applications > `lab-private` > Policies (private original with his email and policy id visible: `evidence/screenshots_PRIVATE_originals/E-130_access-policy-allow-owner-email_2026-11-10_0950CST.png`; a masked copy is made in the curation pass).
Read-only; nothing was changed.
Facts (what the screenshot shows):
- Policy name `allow-owner-email`, Total rules 1, Action Allow, Session duration "Same as application session timeout", created and last updated 2026-11-09 04:34 PM (no edits since creation).
- Policy details: one rule, Include > Emails > <email> (a single address, the author's own).
- Used by applications: 1, the application `lab-private`, URL `lab.<lab-domain>/private`, type Self-hosted.
- No Exclude or Require rules and no wide selector (Everyone, email domain) are listed.
Interpretation: only the author's email is allowed on `/private`. Cloudflare Access normally denies a user who matches no Allow policy (general knowledge; this is what the negative test will check, it is not yet proven here).
Next prep step: Google Auth Platform > Audience of project `lab-cloudflare-access` (publishing status Testing and the test users list) before asking the second account to try.

## E-131 — Piece 3, prep step 2 (partial): Google Auth Platform > Audience of project `lab-cloudflare-access` (screenshot, 09:54 CST, 2026-11-10)
Source: the author's screenshot (private original: `evidence/screenshots_PRIVATE_originals/E-131_google-audience_testing_2026-11-10_0954CST.png`; shows the Google account avatar and a free-trial banner; the Test users list is cut off at the bottom). Read-only.
Facts (what the screenshot shows):
- Project `lab-cloudflare-access`; page Google Auth Platform > Audience.
- Publishing status: Testing (the "Publish app" button is greyed out; the page says publishing needs the Branding page completed).
- User type: External.
- OAuth user cap text: while status is Testing only test users can access the app; cap before verification is 100, counted over the app's whole lifetime. Counter shows "0 users (0 test, 0 other) / 100 user cap".
Not yet seen: the Test users list itself (below the visible area). The counter "0 test" does not by itself say whether the list is empty or only counts users who already granted consent; not interpreted. the author logged in through this app earlier (E-080 era), so his account got through, possibly as project owner; not verified.
Addendum (09:56 CST): the author reported by text, after scrolling, that the Test users list shows zero test users (no screenshot of that section). So his own login earlier worked with an empty list; the reason is not verified (possibly because he is the owner of the Google Cloud project; not checked in Google's documentation). Consequence for the test: the second account must be added as a test user first, otherwise Google may block it before Cloudflare (to be seen in the test; if Google blocks, that is not an Access result).
Next: scroll down to the "Test users" section and capture it.

## E-132 — Piece 3: Test users section of the Google app now shows one test user (screenshot, 09:59 CST, 2026-11-10) - CORRECTS the E-131 addendum
Source: the author's screenshot (private original: `evidence/screenshots_PRIVATE_originals/E-132_google-audience_test-users_2026-11-10_0959CST.png`; it shows a third-party email address, so it is NEVER for the repo and is not transcribed anywhere).
Facts (what the screenshot shows):
- Test users section: one entry, a Gmail address <test-account> that is NOT the author's own address; buttons Add users, a delete icon per row, a Filter box.
- Counter: "0 users (1 test, -1 other) / 100 user cap" (the "-1 other" looks like a display quirk; not interpreted). In the previous screenshot (E-131, 09:54) it read 0 test.
- Correction: the E-131 addendum said, from the author's text, that the list was empty; this screenshot shows one test user. Either the entry was added between 09:54 and 09:59 or the text report was wrong; Claude has not been told which, and has not been told whose account it is.
- the author said "prueba 3 en standby": the negative test is paused until the second account owner is available.
Addendum (15:19 CST): the author confirmed by text that he added that Gmail account himself this morning (so the entry appeared between the 09:54 and 09:59 screenshots; step 1 of the negative test is DONE). The E-131 note "zero test users" was true at 09:54 and is superseded.
Consequence: a test user exists in the Google app now. It must be removed in the final cleanup (the final cleanup); the address is not written in any file.

---
## Note N-001 (12:05) — wrong host assumed for E-004/E-005
E-004 and E-005 were run on CloudSpartan because the initial plan (from the earlier planning) said the tunnel ran there. the author recalls Grafana (and its tunnel) are on CloudLab. earlier project notes says cloudflared was installed as a systemd service and Grafana runs in the lab k3s cluster. The results of E-004/E-005 remain valid only for CloudSpartan. The check must be repeated on CloudLab-1 (see the initial plan, Deviation 3).

## E-120 — Piece 1 (documents), step 1: runbook written from the lab evidence (2026-11-10, ~04:30 CST)
What: `docs/RUNBOOK.md` (English, 9 sections): Ray ID workflow, triage table, procedures for 502, 530/1033, 403 block page, 429, Access/IdP error, cache, escalation checklist, honest gaps.
Facts: every procedure cites the E-xxx where it was reproduced (E-046/047, E-053 to E-059, E-063/064, E-071 to E-080, E-086, E-089/090, E-091/092, E-094/095, E-097 to E-099, E-116/117, E-119). The 502 commands are the exact ones run in E-092.
Limits: written, not used in production; error 1016 and 520-526 not reproduced; TLS Full vs Full (strict), SAML, MFA and managed rules not exercised. Remaining documents of piece 1 (onboarding plan, call summary + escalation templates, 20-minute workshop outline) are NOT written yet.

## E-133 — Two study guides written: DNS deep dive and 520 to 526 errors with SSL/TLS modes (2026-11-10, ~17:25 CST)
Text work only; nothing was executed in the lab or changed in the zone. Files: `docs/DNS_DEEP_DIVE.md`, `docs/STUDY_5xx_errors_and_TLS_modes.md` and five animated diagrams (`dns-proxied-lookup`, `dns-two-clocks`, `dns-cname-target-errors`, `origin-errors-map`, `ssl-modes`).
Documentation read for them, through a fetch tool that summarizes pages (not raw text): Cloudflare pages on proxy status, DNS record types, TTL, CNAME flattening (the `index.md` versions), SSL/TLS encryption modes, Flexible, Full (strict), the 5xx index and errors 520, 521, 522, 523, 524, 525 and 526. Earlier reads: E-037, E-122, E-128.
Method: every statement carries a tag, lab-observed (with its E-xxx), from the documentation, or general knowledge. Facts about the lab come from E-036 to E-045, E-049, E-091, E-097, E-108, E-112, E-113, E-115 to E-117, E-123 to E-129.
Corrections made while writing: two diagram labels cited entries that did not support them and were fixed before publishing; the 1014 explanation says the cross-account reading is an inference that fits the documentation (E-125, E-126).
Limits: the guides about 520 to 526 and the SSL/TLS modes are documentation only; no error from 520 to 526 and no mode change was reproduced. The CNAME flattening and DNS-only behavior are documentation only. The two addresses seen in `dig` were not checked against Cloudflare's published IP list.
