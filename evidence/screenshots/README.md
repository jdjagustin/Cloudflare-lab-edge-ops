# Masked screenshots

Screenshots that back entries in [`docs/EVIDENCE.md`](../../docs/EVIDENCE.md). Each file name starts with the evidence entry it belongs to.

All of them were masked before publication: personal email, public IP, carrier details, account and team names, token and session values. Some values are covered with grey boxes (token names, one policy name, one version string). A few other captures were kept private on purpose.

The images are a visual aid. The claims themselves are in the evidence log, with commands, outputs and limits.

| File | Entry | What it shows |
|---|---|---|
| [`E-003_26350395.png`](E-003_26350395.png) | [E-003](../../docs/EVIDENCE.md#e-003) | Cloudflare advisory e-mail header (upgrade cloudflared to 2026.10.2+), received 2026-10-26 |
| [`E-006_66f0a8ce.png`](E-006_66f0a8ce.png) | [E-006](../../docs/EVIDENCE.md#e-006) | Dashboard Networking > Tunnels: lab-tunnel Healthy, version 2026.8.3, 1 app, usage 1/1,000 |
| [`E-007_28f3c187.png`](E-007_28f3c187.png) | [E-007](../../docs/EVIDENCE.md#e-007) | Tunnel detail Overview: 1 replica, Healthy, uptime 2 days, hostname Cloudlab-1, edge locations dfw01/08/15, linux_amd64 |
| [`E-013_8557c709.png`](E-013_8557c709.png) | [E-013](../../docs/EVIDENCE.md#e-013) | Browser: Cloudflare Access login page "Log in to grafana", sign in with Cloudflare |
| [`E-015_1379d36f.png`](E-015_1379d36f.png) | [E-015](../../docs/EVIDENCE.md#e-015) | Tunnel Replicas table after the upgrade: Cloudlab-1, edge dfw05/06/06/14, version 2026.10.7, linux_amd64 |
| [`E-015_fb0f1221.png`](E-015_fb0f1221.png) | [E-015](../../docs/EVIDENCE.md#e-015) | Tunnels list after the upgrade: lab-tunnel Healthy, version 2026.10.7, 1 app (cropped, no header) |
| [`E-016_e1c0b21f.png`](E-016_e1c0b21f.png) | [E-016](../../docs/EVIDENCE.md#e-016) | Cloudflare "Sign in" page (Google/Apple/GitHub/SSO + email/password), fields empty |
| [`E-018_aed51d6b.png`](E-018_aed51d6b.png) | [E-018](../../docs/EVIDENCE.md#e-018) | Safari: https://grafana.jdjagustin-lab.dev "Welcome to Grafana" login |
| [`E-036_dc3b3200.png`](E-036_dc3b3200.png) | [E-036](../../docs/EVIDENCE.md#e-036) | DNS records of jdjagustin-lab.dev BEFORE the lab record: "1 of 200", grafana = Tunnel lab-tunnel Proxied Auto; 3 recommendations |
| [`E-039_f128b9c2.png`](E-039_f128b9c2.png) | [E-039](../../docs/EVIDENCE.md#e-039) | "Add record" dialog with the Type list open (A, AAAA, CAA, CERT, CNAME, DNSKEY, DS, HTTPS, LOC, MX, NAPTR, NS, OPENPGPKEY, PTR, SMIMEA) |
| [`E-040_dffea891.png`](E-040_dffea891.png) | [E-040](../../docs/EVIDENCE.md#e-040) | "Add record" form filled: CNAME lab -> <tunnel-uuid>.cfargotunnel.com, Proxied, TTL Auto, before Save |
| [`E-041_f12c7ac7.png`](E-041_f12c7ac7.png) | [E-041](../../docs/EVIDENCE.md#e-041) | DNS records AFTER saving: "2 of 200", grafana and lab both Tunnel lab-tunnel Proxied Auto |
| [`E-043_d76d6430.png`](E-043_d76d6430.png) | [E-043](../../docs/EVIDENCE.md#e-043) | Safari: https://lab.jdjagustin-lab.dev "Lab site - Temporary static page used for Cloudflare lab tests" |
| [`E-049_d1cd440e.png`](E-049_d1cd440e.png) | [E-049](../../docs/EVIDENCE.md#e-049) | SSL/TLS Overview: "Current encryption mode: Full", Automatic mode enabled 66 days ago, next scan Nov 17, TLS v1.3 = 136 requests (24 h) |
| [`E-052_0d4504fc.png`](E-052_0d4504fc.png) | [E-052](../../docs/EVIDENCE.md#e-052) | Security rules after deploying: custom rule `lab-block-blocked-path` (Hostname equals lab... and URI Path equals /blocked) = Block, Custom rules 1/5, Rate limiting 0/1 |
| [`E-057_91f16308.png`](E-057_91f16308.png) | [E-057](../../docs/EVIDENCE.md#e-057) | Safari: Cloudflare block page "Sorry, you have been blocked" for lab.jdjagustin-lab.dev |
| [`E-058_4095fb81.png`](E-058_4095fb81.png) | [E-058](../../docs/EVIDENCE.md#e-058) | Bottom of the block page: Cloudflare Ray ID a57f8f0e8d9ff2f0, "Your IP" line, "Performance & security by Cloudflare" |
| [`E-059_9e2ce4ea.png`](E-059_9e2ce4ea.png) | [E-059](../../docs/EVIDENCE.md#e-059) | Security Analytics > Events filtered by Ray ID a57f8f0e8d9ff2f0: Custom rules / Block, rule lab-block-blocked-path, request details |
| [`E-060_16e80091.png`](E-060_16e80091.png) | [E-060](../../docs/EVIDENCE.md#e-060) | New rate limiting rule form: host+path /ratelimit-test, IP characteristic, 5 requests / 10 s, Block 10 s, Active, "Deploy with API call" curl |
| [`E-061_0010b765.png`](E-061_0010b765.png) | [E-061](../../docs/EVIDENCE.md#e-061) | Mac terminal: the rate-limit `for` loop stuck at the `for>` prompt (backslash before `;`) |
| [`E-062_b662c33b.png`](E-062_b662c33b.png) | [E-062](../../docs/EVIDENCE.md#e-062) | Mac terminal: second attempt with quoted URL, same `for>` prompt (backslash still inserted) |
| [`E-063_0ca9b7c8.png`](E-063_0ca9b7c8.png) | [E-063](../../docs/EVIDENCE.md#e-063) | Security rules after the rate limit exists: custom rule `lab-block-blocked-path` Block (1/5), rate limiting `lab-ratelimit-test` Block (1/1), Managed rules none, php2shell banner |
| [`E-063_ecc3bde2.png`](E-063_ecc3bde2.png) | [E-063](../../docs/EVIDENCE.md#e-063) | Mac terminal: loop with `url=` variable prints 404 x5 then 429 x5 (rate limit works) |
| [`E-067_d0d02f57.png`](E-067_d0d02f57.png) | [E-067](../../docs/EVIDENCE.md#e-067) | Google Cloud, Google Auth Platform Overview for project lab-cloudflare-access: "OAuth configuration created!", no clients yet |
| [`E-068_f6b5bd65.png`](E-068_f6b5bd65.png) | [E-068](../../docs/EVIDENCE.md#e-068) | Zero Trust Settings > Team domain: team name and full `<team>.cloudflareaccess.com` |
| [`E-069_d3dbe8df.png`](E-069_d3dbe8df.png) | [E-069](../../docs/EVIDENCE.md#e-069) | Google "Create OAuth client ID" form filled: JS origin + redirect URI `/cdn-cgi/access/callback`, project lab-cloudflare-access |
| [`E-071_485df782.png`](E-071_485df782.png) | [E-071](../../docs/EVIDENCE.md#e-071) | Cloudflare Access "Failed to get your identity": "User email was not returned. API permissions are likely incorrect." + JSON id and name |
| [`E-073_eea257f5.png`](E-073_eea257f5.png) | [E-073](../../docs/EVIDENCE.md#e-073) | Google "Update selected scopes" panel: 31 scopes, none checked (userinfo.email, userinfo.profile, openid first) |
| [`E-075_E-076_d4de9e2c.png`](E-075_E-076_d4de9e2c.png) | [E-075](../../docs/EVIDENCE.md#e-075) / [E-076](../../docs/EVIDENCE.md#e-076) | Google "How Google helps you sign in to cloudflareaccess.com": shares "See your profile info", Delete all |
| [`E-076_0c925341.png`](E-076_0c925341.png) | [E-076](../../docs/EVIDENCE.md#e-076) | Google "How Google helps you sign in" detail: access given 11 minutes ago, "Stop using Sign in with Google" |
| [`E-077_77909891.png`](E-077_77909891.png) | [E-077](../../docs/EVIDENCE.md#e-077) | Second view of "Failed to get your identity" (same message, id and name), cropped differently |
| [`E-079_26c7b08d.png`](E-079_26c7b08d.png) | [E-079](../../docs/EVIDENCE.md#e-079) | Identity provider google-lab, "Optional configurations": Email claim field contained an email address, masked here (the cause of the error) |
| [`E-080_2b6f31d7.png`](E-080_2b6f31d7.png) | [E-080](../../docs/EVIDENCE.md#e-080) | Access Test passes: "Your connection works!" with name and email JSON |
| [`E-081_bb72acb3.png`](E-081_bb72acb3.png) | [E-081](../../docs/EVIDENCE.md#e-081) | Empty "Create new self-hosted application" form (No policy associated, Accept all identity providers ON) |
| [`E-082_603091cc.png`](E-082_603091cc.png) | [E-082](../../docs/EVIDENCE.md#e-082) | Access "Create new self-hosted application" filled: lab.jdjagustin-lab.dev/private, policy `allow-...-email` (name covered), IdP Google-lab only, name lab-private, 24 h |
| [`E-083_4ffba779.png`](E-083_4ffba779.png) | [E-083](../../docs/EVIDENCE.md#e-083) | Create self-hosted app error: `use_clientless_isolation_app_launcher_url can only be enabled for apps with private destinations` |
| [`E-085_85afd414.png`](E-085_85afd414.png) | [E-085](../../docs/EVIDENCE.md#e-085) | Access application `lab-private` saved: same settings as above, Delete/Save buttons |
| [`E-087_318a3fff.png`](E-087_318a3fff.png) | [E-087](../../docs/EVIDENCE.md#e-087) | Access login page "Log in to lab-private" with Google / Google-lab button |
| [`E-087_56560737.png`](E-087_56560737.png) | [E-087](../../docs/EVIDENCE.md#e-087) | Safari private window: Google sign-in page "Ir a cloudflareaccess.com" |
| [`E-087_ff33a1cb.png`](E-087_ff33a1cb.png) | [E-087](../../docs/EVIDENCE.md#e-087) | Safari private window: lab.jdjagustin-lab.dev shows "Private area" after login (positive Access test) |
| [`E-090_0bb002b4.png`](E-090_0bb002b4.png) | [E-090](../../docs/EVIDENCE.md#e-090) | Zero Trust Application Access Report (last 24 h): 2 events, both Granted, apps grafana and lab-private, IdPs google and cloudflare, 1 user, country MX, 1 IP |
| [`E-091_9b780925.png`](E-091_9b780925.png) | [E-091](../../docs/EVIDENCE.md#e-091) | Mac terminal: origin stopped, `curl -sI` shows HTTP/2 502, server cloudflare, cf-ray a58083c549456717-DFW, error code 502 |
| [`E-093_8ecb24a2.png`](E-093_8ecb24a2.png) | [E-093](../../docs/EVIDENCE.md#e-093) | Safari: Cloudflare "Bad gateway, Error code 502" page (2026-11-10 01:40:22 UTC) with Web Inspector Network tab: 8 requests, 20.1 KB, 1.37 s |
| [`E-093_a52b5122.png`](E-093_a52b5122.png) | [E-093](../../docs/EVIDENCE.md#e-093) | Safari Settings > Desarrollador tab, all options unchecked (Develop menu prerequisite for Web Inspector) |
| [`E-096_463ea968.png`](E-096_463ea968.png) | [E-096](../../docs/EVIDENCE.md#e-096) | Safari Network > Headers of beacon.min.js: 200, "Caché de memoria", Cache-Control public max-age=86400, ETag W/"2026.10.1" |
| [`E-096_5ec87501.png`](E-096_5ec87501.png) | [E-096](../../docs/EVIDENCE.md#e-096) | Grafana Home through Access, user menu open showing name and email |
| [`E-096_d0b005a9.png`](E-096_d0b005a9.png) | [E-096](../../docs/EVIDENCE.md#e-096) | Safari: "Lab site" page, Network tab: document 866 B, style.css, beacon js from static.cloudflareinsights.com, rum xhr |
| [`E-100_6911ba15.png`](E-100_6911ba15.png) | [E-100](../../docs/EVIDENCE.md#e-100) | Grafana Home after the tunnel restart, user menu with name and email |
| [`E-108_31424552.png`](E-108_31424552.png) | [E-108](../../docs/EVIDENCE.md#e-108) | Observability chart "Request outcomes over time" 7:39-8:39 PM: Mitigated 0, Served by Cloudflare 39, Served by Origin 42 |
| [`E-110_8db3beab.png`](E-110_8db3beab.png) | [E-110](../../docs/EVIDENCE.md#e-110) | Observability: expanded row JSON for grafana host /api/search at 20:09:23 with securityAction, rayName, originResponseStatus, edgeResponseStatus, clientIP, cacheStatus |
| [`E-110_cfe51e37.png`](E-110_cfe51e37.png) | [E-110](../../docs/EVIDENCE.md#e-110) | Observability expanded row JSON: POST grafana /cdn-cgi/rum at 20:15:21, edge 204, origin 0, cacheStatus none, clientIP highlighted |
| [`E-111_cf6c371a.png`](E-111_cf6c371a.png) | [E-111](../../docs/EVIDENCE.md#e-111) | Zone Overview of jdjagustin-lab.dev (24 h: 2 unique visitors, 392 requests, 47.24% cached, 8 MB), right column API box with the Zone ID and Account ID masked |
| [`E-111_f2ded873.png`](E-111_f2ded873.png) | [E-111](../../docs/EVIDENCE.md#e-111) | Token Summary (token name covered): expires Nov 16, 2026; Logs, Analytics, Zone Observability, DNS, Zone, Zone Settings all Read; all IPs allowed |
| [`E-113_0db0ced5.png`](E-113_0db0ced5.png) | [E-113](../../docs/EVIDENCE.md#e-113) | API Tokens > Create Token (token name covered): Specific zone jdjagustin-lab.dev, DNS = Edit only (1/12), expiration "Today - Nov 10", no IP filter |
| [`E-115_99626272.png`](E-115_99626272.png) | [E-115](../../docs/EVIDENCE.md#e-115) | Create Token (token name covered): Specific zone jdjagustin-lab.dev, DNS = Edit only (1/12), expiration 7 days selected (later shortened) |
| [`E-117_060cc1f6.png`](E-117_060cc1f6.png) | [E-117](../../docs/EVIDENCE.md#e-117) | New Cache Rule form `lab-cache-html` with Field "URI Full" equals lab.jdjagustin-lab.dev, Eligible for cache, Edge TTL 2 h (the first attempt that was corrected to Hostname) |
| [`E-117_86c4a3a0.png`](E-117_86c4a3a0.png) | [E-117](../../docs/EVIDENCE.md#e-117) | Caching > Cache Rules list: `lab-cache-html`, 1 active, "Hostname equals lab.jdjagustin-lab.dev", Eligible for cache, Edge TTL |
| [`E-118_475c1056.png`](E-118_475c1056.png) | [E-118](../../docs/EVIDENCE.md#e-118) | Observability > Logs (HTTP requests, last 1 hour): chart Mitigated 0 / Served by Cloudflare 1 / Served by Origin 5; 6 HEAD rows for lab host, 200 OK |
| [`E-118_5dedbaa9.png`](E-118_5dedbaa9.png) | [E-118](../../docs/EVIDENCE.md#e-118) | Observability "Select fields" dialog: Ray ID (rayName), Security Action (securityAction), Security Source, Source browser, SSL Protocol... each with a + button |
| [`E-118_abb6dcd5.png`](E-118_abb6dcd5.png) | [E-118](../../docs/EVIDENCE.md#e-118) | Observability "Select fields" dialog, 8 selected (method, host, path, edge status, cache status, source IP, country, origin status) out of 33 fields |
| [`E-119_c2c86586.png`](E-119_c2c86586.png) | [E-119](../../docs/EVIDENCE.md#e-119) | Observability "Select fields" dialog, 10 selected: securityAction and rayName added to the 8 |
