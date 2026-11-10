#!/usr/bin/env python3
"""har_summary.py - read a HAR file offline and explain it.

Local only: Python standard library, no network connection. It never modifies
the HAR it reads (--redact writes a NEW file).

Usage:
    python3 har_summary.py [file.har]                    table + flags + sensitive-data check
    python3 har_summary.py [file.har] --timings          timing breakdown per request
    python3 har_summary.py [file.har] --detail N         everything about request number N
    python3 har_summary.py [file.har] --csv OUT.csv      export the table (with timings) to CSV
    python3 har_summary.py [file.har] --redact OUT.har   write a masked copy of the HAR

Without a file it picks the *_masked.har file in this folder (or the first .har).
Several options can be combined (for example --timings --csv out.csv).
"""
import argparse
import csv
import glob
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CST = timezone(timedelta(hours=-6))  # Mexico City (no daylight saving time since 2022)
SECRET_HEADERS = {"cookie", "authorization", "proxy-authorization", "set-cookie"}


# ---------------------------------------------------------------- helpers
def pick_file(arg):
    if arg:
        return arg
    for pattern in ("*_masked.har", "*.har"):
        found = sorted(glob.glob(os.path.join(HERE, pattern)))
        if found:
            return found[0]
    sys.exit("No .har file found next to this script. Pass one as an argument.")


def headers(items):
    """HAR headers are a list of {name, value}; return a lowercase dict."""
    return {h["name"].lower(): h["value"] for h in items}


def short(text, width):
    return text if len(text) <= width else text[: width - 3] + "..."


def ms(value):
    """Format a HAR timing (milliseconds); -1 means 'not applicable'."""
    if value is None or value < 0:
        return "-"
    return ("%.1f" % value) if value < 10 else str(int(round(value)))


def parse_time(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def when(iso):
    try:
        t = parse_time(iso)
        return t.astimezone(timezone.utc).strftime("%H:%M:%S.%f")[:-3] + "Z = " + t.astimezone(CST).strftime("%H:%M:%S") + " CST"
    except Exception:
        return iso


def server_timing(value):
    """'cfEdge;dur=32,cfOrigin;dur=62' -> {'cfEdge': 32.0, 'cfOrigin': 62.0}"""
    out = {}
    for part in (value or "").split(","):
        name = part.split(";")[0].strip()
        m = re.search(r"dur=([\d.]+)", part)
        if name and m:
            out[name] = float(m.group(1))
    return out


def build_rows(entries):
    rows = []
    for i, e in enumerate(entries, 1):
        req, resp = e["request"], e["response"]
        rh = headers(resp["headers"])
        t = e.get("timings", {})
        st = server_timing(rh.get("server-timing"))
        wait = t.get("wait")
        cf = st.get("cfEdge", 0) + st.get("cfOrigin", 0)
        rows.append({
            "n": i, "status": resp["status"], "method": req["method"], "url": req["url"],
            "total_ms": e.get("time", 0), "size": resp.get("content", {}).get("size", 0),
            "wire": resp.get("bodySize", -1), "enc": rh.get("content-encoding", "-"),
            "type": rh.get("content-type", "-").split(";")[0],
            "cache": rh.get("cf-cache-status", "-"), "age": rh.get("age", "-"),
            "server_timing": rh.get("server-timing", "-"),
            "cfEdge": st.get("cfEdge"), "cfOrigin": st.get("cfOrigin"),
            "blocked": t.get("blocked"), "dns": t.get("dns"), "connect": t.get("connect"),
            "ssl": t.get("ssl"), "send": t.get("send"), "wait": wait, "receive": t.get("receive"),
            "outside_cf": (wait - cf) if (wait is not None and wait > 0 and cf > 0) else None,
        })
    return rows


# ---------------------------------------------------------------- views
def view_table(path, log, rows):
    entries = log["entries"]
    creator = log.get("creator", {})
    print("File     :", os.path.basename(path))
    print("Creator  : %s %s (HAR %s)" % (creator.get("name"), creator.get("version"), log.get("version")))
    print("Requests :", len(rows))
    if entries:
        starts = [parse_time(e["startedDateTime"]) for e in entries]
        ends = [s + timedelta(milliseconds=e.get("time", 0)) for s, e in zip(starts, entries)]
        print("First one:", when(entries[0]["startedDateTime"]))
        print("Wall time: %d ms from the first request starting to the last one finishing" % round((max(ends) - min(starts)).total_seconds() * 1000))
    print()
    print("%-3s %-4s %-6s %-56s %6s %7s %-5s %-6s %-6s %s" % ("#", "code", "method", "url", "ms", "bytes", "enc", "cache", "age", "type / server-timing"))
    flagged = []
    for r in rows:
        url = r["url"].split("://", 1)[-1]
        extra = r["type"] if r["server_timing"] == "-" else r["type"] + " | " + r["server_timing"]
        print("%-3d %-4s %-6s %-56s %6d %7s %-5s %-6s %-6s %s" % (
            r["n"], r["status"], r["method"], short(url, 56), round(r["total_ms"]),
            r["size"] if r["size"] > 0 else "-", r["enc"], r["cache"], r["age"], extra))
        if r["status"] >= 400:
            flagged.append("#%d is a %d (%s)" % (r["n"], r["status"], url))
        if r["cache"].upper() == "STALE":
            flagged.append("#%d was served STALE (expired copy, origin not consulted)" % r["n"])
    print()
    print("Flags:")
    for line in flagged or ["none"]:
        print("  -", line)
    classes = {}
    for r in rows:
        key = "%dxx" % (r["status"] // 100)
        classes[key] = classes.get(key, 0) + 1
    print()
    print("By status class:", ", ".join("%s: %d" % kv for kv in sorted(classes.items())))
    print("Total content size: %d bytes" % sum(r["size"] for r in rows if r["size"] > 0))
    if rows:
        slow = max(rows, key=lambda r: r["total_ms"])
        print("Slowest request: #%d (%d ms) %s" % (slow["n"], round(slow["total_ms"]), short(slow["url"].split("://", 1)[-1], 70)))


def view_timings(rows):
    print()
    print("Timing breakdown in ms ('-' = not applicable; a reused connection has no dns/connect/ssl).")
    print("%-3s %-4s %-44s %7s %7s %7s %7s %7s %8s %6s  %s" % ("#", "code", "url", "blocked", "dns", "connect", "ssl", "send", "wait", "recv", "Cloudflare vs rest"))
    for r in rows:
        note = "-"
        if r["cfEdge"] is not None or r["cfOrigin"] is not None:
            cf = (r["cfEdge"] or 0) + (r["cfOrigin"] or 0)
            note = "Server-Timing: edge %s + origin %s = %s ms" % (ms(r["cfEdge"]), ms(r["cfOrigin"]), ms(cf))
            if r["outside_cf"] is not None:
                note += "; wait minus that = %s ms (network and queueing, approximate)" % ms(r["outside_cf"])
        print("%-3d %-4s %-44s %7s %7s %7s %7s %7s %8s %6s  %s" % (
            r["n"], r["status"], short(r["url"].split("://", 1)[-1], 44), ms(r["blocked"]), ms(r["dns"]),
            ms(r["connect"]), ms(r["ssl"]), ms(r["send"]), ms(r["wait"]), ms(r["receive"]), note))
    print("wait = time to first byte after the request was sent (TTFB); it includes the network round trip.")


def view_detail(entries, n):
    if n < 1 or n > len(entries):
        sys.exit("Request number must be between 1 and %d." % len(entries))
    e = entries[n - 1]
    req, resp = e["request"], e["response"]
    print("Request #%d: %s %s" % (n, req["method"], req["url"]))
    print("Started   :", when(e["startedDateTime"]), "| total %d ms" % round(e.get("time", 0)))
    print("Response  : %s %s | %s | content %s bytes | body on the wire %s bytes" % (
        resp["status"], resp.get("statusText", ""), resp.get("content", {}).get("mimeType", "-"),
        resp.get("content", {}).get("size", "-"), resp.get("bodySize", "-")))
    print("\nRequest headers:")
    for h in req["headers"]:
        v = "<hidden by har_summary>" if h["name"].lower() in SECRET_HEADERS else h["value"]
        print("  %s: %s" % (h["name"], v))
    print("\nResponse headers:")
    for h in resp["headers"]:
        v = "<hidden by har_summary>" if h["name"].lower() in SECRET_HEADERS else short(h["value"], 160)
        print("  %s: %s" % (h["name"], v))
    print("\nTimings (ms):", ", ".join("%s=%s" % (k, ms(v)) for k, v in e.get("timings", {}).items()))
    content = resp.get("content", {})
    text = content.get("text")
    if text and content.get("encoding") != "base64" and "html" in content.get("mimeType", ""):
        m = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
        print("\nHTML title:", m.group(1).strip() if m else "(none)")
        print("Body starts:", short(" ".join(text.split()), 240))


def write_csv(rows, out):
    cols = ["n", "status", "method", "url", "total_ms", "size", "wire", "enc", "type", "cache", "age",
            "server_timing", "cfEdge", "cfOrigin", "blocked", "dns", "connect", "ssl", "send", "wait", "receive", "outside_cf"]
    if os.path.exists(out):
        sys.exit("Refusing to overwrite: " + out)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if r[c] is None else (round(r[c], 1) if isinstance(r[c], float) else r[c]) for c in cols])
    print("CSV written:", out, "(%d rows)" % len(rows))


# ---------------------------------------------------------------- redaction
IPV4 = re.compile(r"(\"serverIPAddress\"\s*:\s*\")?\b(?:\d{1,3}\.){3}\d{1,3}\b")  # group 1 present = the server address field of a HAR entry
EMAIL = re.compile(r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
EMAIL_ENC = re.compile(r"[A-Za-z0-9._+-]+%40[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I)
JWT = re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")
PARAM = re.compile(r"([?&](?:meta|kid|token|code|state|sig|signature|access_token|id_token|key|jwt)=)[^&\"\s\\]+", re.I)
CFAUTH = re.compile(r"CF_Authorization=[^;\"\s\\]+")


def ip_split(text):
    """Return (server_ips, other_ips): addresses of the 'serverIPAddress' field vs any other IPv4-like string."""
    server, other = [], []
    for m in IPV4.finditer(text):
        (server if m.group(1) else other).append(m.group(0)[len(m.group(1) or ""):])
    return server, other


def redact(raw, out):
    if os.path.exists(out):
        sys.exit("Refusing to overwrite: " + out)
    data = json.loads(raw)
    removed = 0
    for e in data["log"]["entries"]:
        for part, names in (("request", {"cookie", "authorization", "proxy-authorization"}), ("response", {"set-cookie"})):
            hs = e[part]["headers"]
            keep = [h for h in hs if h["name"].lower() not in names]
            removed += len(hs) - len(keep)
            e[part]["headers"] = keep
            if e[part].get("cookies"):
                removed += len(e[part]["cookies"])
                e[part]["cookies"] = []
        if "postData" in e["request"]:  # form bodies can hold passwords
            e["request"]["postData"] = {"mimeType": e["request"]["postData"].get("mimeType", ""), "text": "<removed by har_summary --redact>"}
            removed += 1
    text = json.dumps(data, ensure_ascii=False, indent=1)
    counts = []
    for label, rx, repl in (
        ("URL secret parameters (meta, kid, token, code, state...)", PARAM, r"\1<masked>"),
        ("JWT tokens", JWT, "<jwt masked>"),
        ("CF_Authorization values", CFAUTH, "CF_Authorization=<masked>"),
        ("e-mail addresses", EMAIL, "<email masked>"),
        ("URL-encoded e-mail addresses", EMAIL_ENC, "<email masked>"),
    ):
        text, n = rx.subn(repl, text)
        counts.append((label, n))
    masked_ips = []
    def _mask_ip(m):
        if m.group(1):  # keep the server address of each entry (a Cloudflare edge address, not personal data)
            return m.group(0)
        masked_ips.append(m.group(0))
        return "x.x.x.x"
    text = IPV4.sub(_mask_ip, text)
    counts.append(("other IPv4 addresses (may also hit 4-part version numbers; 'serverIPAddress' kept)", len(masked_ips)))
    json.loads(text)  # the result must still be valid JSON
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print("Masked copy written:", out)
    print("  cookie/authorization headers, cookie lists and form bodies removed:", removed)
    for label, n in counts:
        print("  %s masked: %d" % (label, n))
    print("Automatic masking is best effort: open the result and look for personal data before sharing it.")


# ---------------------------------------------------------------- hygiene
def hygiene(raw, entries):
    low = raw.lower()
    c = sum(1 for e in entries if any(h["name"].lower() == "cookie" for h in e["request"]["headers"]))
    a = sum(1 for e in entries if any(h["name"].lower() == "authorization" for h in e["request"]["headers"]))
    s = sum(1 for e in entries if any(h["name"].lower() == "set-cookie" for h in e["response"]["headers"]))
    print()
    print("Sensitive-data check (counts):")
    print("  requests carrying a Cookie header        :", c)
    print("  requests carrying an Authorization header:", a)
    print("  responses setting a cookie               :", s)
    print("  mentions of CF_Authorization             :", low.count("cf_authorization"))
    print("  e-mail-like strings                      :", len(EMAIL.findall(raw)) + len(EMAIL_ENC.findall(raw)))
    server_ips, other_ips = ip_split(raw)
    print("  server addresses (serverIPAddress field) :", len(server_ips), sorted(set(server_ips)))
    print("  other IPv4-like strings                  :", len(other_ips))
    if c or a or s or "cf_authorization" in low:
        print("  -> This file has credentials-like data. Do NOT upload or share it as it is (use --redact).")
    elif EMAIL.findall(raw) or EMAIL_ENC.findall(raw) or other_ips:
        print("  -> No credentials found, but personal data (e-mail or IP) is present. Use --redact before sharing.")
    else:
        print("  -> No cookie, authorization, e-mail or other IP patterns found. Still give it a quick look before sharing.")


def main():
    ap = argparse.ArgumentParser(description="Read a HAR file offline (see the top of the script).")
    ap.add_argument("file", nargs="?", help="HAR file (default: the *_masked.har next to this script)")
    ap.add_argument("--timings", action="store_true", help="timing breakdown per request")
    ap.add_argument("--detail", type=int, metavar="N", help="show everything about request number N")
    ap.add_argument("--csv", metavar="OUT.csv", help="export the table (with timings) to CSV")
    ap.add_argument("--redact", metavar="OUT.har", help="write a masked copy of the HAR")
    args = ap.parse_args()

    path = pick_file(args.file)
    raw = open(path, encoding="utf-8").read()
    log = json.loads(raw)["log"]
    rows = build_rows(log["entries"])

    if args.detail is not None:
        view_detail(log["entries"], args.detail)
        return
    if args.redact:
        redact(raw, args.redact)
        return
    view_table(path, log, rows)
    if args.timings:
        view_timings(rows)
    if args.csv:
        print()
        write_csv(rows, args.csv)
    hygiene(raw, log["entries"])


if __name__ == "__main__":
    main()
