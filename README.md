# Cloudflare-lab-edge-ops

![status](https://img.shields.io/badge/status-work%20in%20progress-d29922)
![Cloudflare](https://img.shields.io/badge/Cloudflare-DNS%20%C2%B7%20WAF%20%C2%B7%20Access%20%C2%B7%20Tunnel-F38020?logo=cloudflare&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-throwaway%20record-844FBA?logo=terraform&logoColor=white)
![Python](https://img.shields.io/badge/Python-stdlib%20only-3776AB?logo=python&logoColor=white)
![evidence](https://img.shields.io/badge/evidence-133%20entries-3fb950)
![diagrams](https://img.shields.io/badge/diagrams-11%20animated%20SVG%20%2B%20Mermaid-f85149)
[![license](https://img.shields.io/badge/license-MIT-97ca00)](LICENSE)

A one-person, hands-on lab that puts a small origin behind Cloudflare and exercises the edge the way an operator would: DNS and proxy, TLS mode, cache, WAF and rate limiting, Access with an identity provider, Tunnel failures and how to diagnose them, the API, Terraform and Observability logs.

> **Status: work in progress.** Everything under "Done" actually ran and was observed by the author. Everything under "To be completed" has **not** been done yet and is listed so the gaps are visible. Entries like [E-042](docs/EVIDENCE.md#e-042) link to the evidence log [`docs/EVIDENCE.md`](docs/EVIDENCE.md): what ran, the output, and the limits of each claim. Masked screenshots are in [`evidence/screenshots/`](evidence/screenshots/README.md); the log refers to some private originals that are not published.

## Architecture

![Animated architecture diagram: a request goes from the client through DNS, WAF and rate limiting, Access, cache and a Tunnel to cloudflared on the lab host; four outcomes alternate](docs/diagrams/architecture.svg)

The animation shows one request at a time. The four outcomes alternate (success, blocked by a WAF custom rule, `429` from the rate limit, `530` with error `1033`); they do not all happen at once. Each was observed in the lab, see the Done table. The Access denial for a second account is not drawn because it has not been run yet.

<details>
<summary>Static version (Mermaid source, also in <code>docs/diagrams/architecture.mmd</code>)</summary>

```mermaid
flowchart LR
  U[Browser / curl] -->|HTTPS| E

  subgraph CF[Cloudflare edge]
    direction TB
    E[DNS: proxied CNAME<br/>anycast IPs] --> W[WAF custom rule<br/>+ rate limit]
    W --> A[Access<br/>Google OIDC<br/>path /private]
    A --> C[Cache Rules<br/>HIT / MISS / DYNAMIC]
    C --> T[Tunnel endpoint]
  end

  T -. outbound QUIC .- D

  subgraph LAB[Lab host, no inbound ports]
    direction TB
    D[cloudflared<br/>systemd service] --> O1[Static origin<br/>127.0.0.1:8081]
    D --> O2[Grafana on k3s<br/>behind Access]
  end

  CF -.-> L[Observability logs<br/>Ray ID / securityAction]
  API[API + Terraform<br/>scoped short-lived tokens] -.->|manage| CF
```

</details>

A browser or `curl` reaches proxied hostnames on Cloudflare's edge. Requests pass DNS, WAF and rate limiting, Access (on `/private` and on the Grafana host) and cache rules, then travel through a Cloudflare Tunnel. `cloudflared` runs on the lab host and opens outbound connections only, so the origin has no inbound ports. Logs and the API sit beside the data path.

## Flow diagrams

Animated SVGs, each drawn only from cases that ran, plus the architecture diagram above. Four of them also sit next to the text they support in the runbook; the Terraform one lives only here. Open each one below, or use the links in the table. The `E-xxx` labels drawn inside the diagrams are not clickable on GitHub; look them up in the [evidence log](docs/EVIDENCE.md).

| Diagram | What it shows | Where |
|---|---|---|
| [Triage map](docs/diagrams/runbook-triage.svg) | From what the visitor sees to the likely layer and the first check (502, 530 with 1033 or 1016, 403 with 1014, block page, 429, Access redirect) | [Runbook, section 1](docs/RUNBOOK.md) |
| [Access login flow](docs/diagrams/access-login-flow.svg) | Allowed account: 302, Google sign-in, policy, page loads. The denial for a second account is not drawn | [Runbook, section 6](docs/RUNBOOK.md) |
| [Cache lifecycle](docs/diagrams/cache-lifecycle.svg) | `DYNAMIC`, `MISS`, `HIT`, and back to `DYNAMIC` after the rule is deleted and the cache purged | [Runbook, section 7](docs/RUNBOOK.md) |
| [Browser view vs edge view](docs/diagrams/har-vs-logs.svg) | A HAR (one page load) and Observability logs (every request) meet at the Ray ID; what `originResponseStatus` 502 and 0 mean | [Runbook, section 10](docs/RUNBOOK.md), [how-to](docs/HOWTO_cf_logs_summary.md) |
| [Terraform cycle](docs/diagrams/terraform-cycle.svg) | `init`, `plan`, `apply`, `dig`, `destroy` on one throwaway TXT record, with the limits of that run | [`terraform/`](terraform/main.tf) |

<details>
<summary>Triage map: what the visitor sees, likely layer, first check</summary>

![Animated triage map: what the visitor sees, the most likely layer and the first check, for 502, 530 with 1033 or 1016, 403 with 1014, a security block page, 429 and the Access redirect](docs/diagrams/runbook-triage.svg)

</details>

<details>
<summary>Access login flow: allowed account only</summary>

![Animated Access login flow for the allowed account: request without session, 302 to the login page, Google sign-in, policy allows one email, page loads](docs/diagrams/access-login-flow.svg)

The denial for a second account has not been run, so it is not drawn.

</details>

<details>
<summary>Cache lifecycle: DYNAMIC, MISS, HIT, back to DYNAMIC</summary>

![Animated cache status lifecycle: DYNAMIC, MISS, HIT, and back to DYNAMIC after the Cache Rule is deleted and the cache purged](docs/diagrams/cache-lifecycle.svg)

</details>

<details>
<summary>Browser view (HAR) vs edge view (logs), joined by the Ray ID</summary>

![Animated diagram: a request seen by the browser (HAR) and by the edge (Observability logs), joined by the Ray ID](docs/diagrams/har-vs-logs.svg)

</details>

<details>
<summary>Terraform cycle on one throwaway record</summary>

![Animated Terraform cycle: init, plan, apply, verify with dig, destroy, on one throwaway TXT record](docs/diagrams/terraform-cycle.svg)

One resource, local state, no modules, no CI.

</details>

## Guides

Written guides. Each statement in them is tagged as lab-observed, from the documentation, or general knowledge, and their animated diagrams are embedded in the guides themselves.

| Guide | What it covers | Basis |
|---|---|---|
| [DNS deep dive](docs/DNS_DEEP_DIVE.md) | Record types, `CNAME`, proxied vs DNS-only, the tunnel record, DNS TTL vs cache TTL, the `1014`, `1016` and `1033` cases | Lab evidence plus Cloudflare documentation |
| [520 to 526 errors and SSL/TLS modes](docs/STUDY_5xx_errors_and_TLS_modes.md) | Meaning, causes and first checks per error; what each encryption mode does | Documentation only; 520 to 526 were not reproduced |

## Done (ran and observed)

| Area | What ran | Evidence |
|---|---|---|
| DNS and proxy | Proxied CNAMEs to a tunnel; `dig` returns Cloudflare anycast IPs, not the origin | [E-036](docs/EVIDENCE.md#e-036), [E-041](docs/EVIDENCE.md#e-041), [E-042](docs/EVIDENCE.md#e-042) |
| TLS | SSL/TLS mode read in the dashboard and through the API (`full`); read only, not changed | [E-049](docs/EVIDENCE.md#e-049), [E-112](docs/EVIDENCE.md#e-112) |
| Cache | Default cache by file extension; HTML is `DYNAMIC`; a Cache Rule by hostname gives `MISS` then `HIT`; rule deleted and cache purged returns to `DYNAMIC` | [E-046](docs/EVIDENCE.md#e-046), [E-047](docs/EVIDENCE.md#e-047), [E-116](docs/EVIDENCE.md#e-116), [E-117](docs/EVIDENCE.md#e-117) |
| WAF custom rule | Block `/blocked` at the edge; the origin log shows the request never arrived | [E-052](docs/EVIDENCE.md#e-052) to [E-058](docs/EVIDENCE.md#e-058) |
| Rate limit | 5 requests per 10 s on one path: `404` x5 then `429` x5 | [E-060](docs/EVIDENCE.md#e-060) to [E-064](docs/EVIDENCE.md#e-064) |
| Access (positive test) | Google as identity provider, application on `/private`, policy allowing one email; the allowed account got in | [E-065](docs/EVIDENCE.md#e-065) to [E-090](docs/EVIDENCE.md#e-090), [E-130](docs/EVIDENCE.md#e-130) |
| Failures | Origin stopped: `502`. Tunnel stopped: `530` with Cloudflare error `1033` | [E-091](docs/EVIDENCE.md#e-091) to [E-099](docs/EVIDENCE.md#e-099) |
| Failures (DNS-level) | Temporary proxied records reproduced `1014` (CNAME to a hostname in another Cloudflare account), `1016` (origin name that does not resolve) and `1033` (tunnel id that does not exist); all removed and verified | [E-125](docs/EVIDENCE.md#e-125) to [E-129](docs/EVIDENCE.md#e-129) |
| Observability | Edge logs export; `cf-ray` from `curl` matches `rayName` in the logs (6 of 6) | [E-108](docs/EVIDENCE.md#e-108), [E-118](docs/EVIDENCE.md#e-118), [E-119](docs/EVIDENCE.md#e-119) |
| API | Scoped read-only token; create, read and delete a throwaway TXT record | [E-111](docs/EVIDENCE.md#e-111) to [E-113](docs/EVIDENCE.md#e-113) |
| Terraform | `init`, `plan`, `apply`, verify with `dig`, `destroy` on one throwaway TXT record | [E-114](docs/EVIDENCE.md#e-114), [E-115](docs/EVIDENCE.md#e-115) |
| Connector maintenance | `cloudflared` upgraded from a local `.deb` after a security advisory; version and tunnel health checked | [E-009](docs/EVIDENCE.md#e-009) to [E-012](docs/EVIDENCE.md#e-012) |
| Runbook | Diagnosis guide written only from the cases above | [`docs/RUNBOOK.md`](docs/RUNBOOK.md) |
| Evidence log | 133 entries with commands, outputs, corrections and limits; personal values replaced by placeholders | [`docs/EVIDENCE.md`](docs/EVIDENCE.md) |
| Masked screenshots | 61 dashboard, browser and terminal captures, each named after the log entry it supports; sensitive values masked or covered | [`evidence/screenshots/`](evidence/screenshots/README.md) |

## To be completed (not done yet)

| Topic | Status |
|---|---|
| Access, negative test | Prepared (policy allows one email; a second Google account is registered as a test user). Not run yet: no denial has been captured, so no claim is made |
| Errors `520`-`526` | **Not reproduced.** Read in the documentation only. The home connection is behind carrier NAT and has no global IPv6, so no public origin was available ([E-122](docs/EVIDENCE.md#e-122) to [E-124](docs/EVIDENCE.md#e-124)). Option kept open: a temporary cloud VM |
| TLS modes Full vs Full (strict) | Read only; not exercised. Study guide written from the documentation: [`docs/STUDY_5xx_errors_and_TLS_modes.md`](docs/STUDY_5xx_errors_and_TLS_modes.md) |
| SAML vs OIDC identity providers, enforced MFA | Not started |
| WAF managed rules / OWASP | Not started (only a custom rule was used) |
| Terraform at scale | Not started (one resource, local state, no modules, no CI) |
| Network fundamentals notes (BGP, CIDR, NAT) and Network Services | Not started |
| Onboarding plan, call summary template, escalation templates, 20-minute workshop outline | Not started |

## Tools in this repo

- `scripts/cf_logs_summary.py`: summarises an Observability logs export (edge view); `--rays`, `--timeline`, `--host`, `--redact`. See [`docs/HOWTO_cf_logs_summary.md`](docs/HOWTO_cf_logs_summary.md).
- `scripts/har_summary.py`: summarises a browser HAR (browser view of one page load).

Both use only the Python standard library and run locally.

## Lessons learned

- Access identity provider: an autofilled *Email claim* field caused "User email was not returned"; the field must stay empty ([E-071](docs/EVIDENCE.md#e-071) to [E-080](docs/EVIDENCE.md#e-080)).
- Cache Rule: matching on *URI Full* would not have matched a hostname-only rule; use *Hostname* ([E-117](docs/EVIDENCE.md#e-117)).
- A token form meant to be read-only had *DNS Edit* ticked in one capture; it was corrected and the final token was read-only ([E-111](docs/EVIDENCE.md#e-111)).
- A prediction was wrong: a CNAME to an `example.com` name gave `1014`, not `1016`, because that name is hosted on Cloudflare. Changing one variable (target inside the same zone) produced `1016` ([E-125](docs/EVIDENCE.md#e-125), [E-126](docs/EVIDENCE.md#e-126)).
- A CNAME to a tunnel id that does not exist also gives `530` + `1033`, so the code alone does not tell "tunnel down" from "tunnel does not exist"; check the tunnel list ([E-127](docs/EVIDENCE.md#e-127)).

## Known limits

One client, small traffic windows, free plan, a single zone, local Terraform state, no modules and no CI. See "To be completed" for what is not covered.

## Repository layout

```
docs/            runbook, evidence log, how-to, diagrams (eleven animated SVGs, architecture.mmd source), two study guides
evidence/        masked exports and command outputs referenced by the log
  screenshots/   61 masked captures and an index (evidence/screenshots/README.md)
scripts/         the two local summary tools
terraform/       the throwaway-record exercise (main.tf only; no state)
LICENSE          MIT
```

## Credits and references

Cloudflare documentation, by topic:

- DNS and proxy: [Proxy status](https://developers.cloudflare.com/dns/proxy-status/), [Manage DNS records](https://developers.cloudflare.com/dns/manage-dns-records/), [DNS record types](https://developers.cloudflare.com/dns/manage-dns-records/reference/dns-record-types/), [TTL](https://developers.cloudflare.com/dns/manage-dns-records/reference/ttl/), [CNAME flattening](https://developers.cloudflare.com/dns/cname-flattening/), [Tunnel DNS records](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/dns/)
- Tunnel: [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/), [Tunnel fundamentals](https://developers.cloudflare.com/tunnel/concepts/)
- SSL/TLS: [Encryption modes](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/), [Flexible](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/flexible/), [Full](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full/), [Full (strict)](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/)
- Cache: [Cache responses (HIT, MISS, DYNAMIC)](https://developers.cloudflare.com/cache/concepts/cache-responses/), [Cache Rules settings](https://developers.cloudflare.com/cache/how-to/cache-rules/settings/)
- WAF: [Custom rules](https://developers.cloudflare.com/waf/custom-rules/), [Rate limiting rules](https://developers.cloudflare.com/waf/rate-limiting-rules/)
- Access: [Access policies](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/), [Google as identity provider](https://developers.cloudflare.com/cloudflare-one/identity/idp-integration/google/), [Enforce MFA](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/mfa-requirements/)
- Errors: [1xxx errors](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/), [Error 1033](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1033/), [5xx errors](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/) ([520](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-520/), [521](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-521/), [522](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-522/), [523](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-523/), [524](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-524/), [525](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-525/), [526](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-5xx-errors/error-526/)), [Error 1014](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1014/), [Error 1016](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1016/), [Error diagnostic headers](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-error-headers/)
- Logs: [Cloudflare Ray ID](https://developers.cloudflare.com/fundamentals/reference/cloudflare-ray-id/), [Log Search](https://developers.cloudflare.com/observability/logs/log-explorer/log-search/)
- API: [Create an API token](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/), [API overview](https://developers.cloudflare.com/api/overview/)
- Terraform: [Cloudflare Terraform provider](https://developers.cloudflare.com/api/terraform/), [provider on the Terraform Registry](https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs)

Other:

- Grafana: [Deploy Grafana on Kubernetes](https://grafana.com/docs/grafana/latest/setup-grafana/installation/kubernetes/)
- Badges: [Shields.io](https://shields.io/)
