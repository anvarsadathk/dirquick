#!/usr/bin/env python3
"""
dirquick - fast async web content discovery.

Brute-forces paths/files on a target web server from a wordlist using a
bounded pool of concurrent requests. Filters by status code and supports
extensions, custom headers, and a built-in starter wordlist.

Author: Anvar Sadath K.  |  License: MIT
Active tool — only run against hosts you own or are authorized to test.
"""
import argparse
import asyncio
import ssl
import sys
from urllib.parse import urljoin

try:
    import aiohttp
except ImportError:
    aiohttp = None

STARTER = """admin administrator login logout dashboard api api/v1 api/v2 app
backup backups config config.php .env .git/config .git/HEAD robots.txt
sitemap.xml server-status phpinfo.php info.php test test.php uploads upload
images img js css assets static vendor node_modules wp-admin wp-login.php
wp-content wp-json user users account accounts profile setting settings
db database sql dump.sql data private secret secrets internal debug
console actuator actuator/health status health metrics swagger swagger-ui
swagger.json openapi.json graphql .well-known .DS_Store old bak tmp temp""".split()


def build_candidates(words, extensions):
    out = []
    for w in words:
        out.append(w)
        for ext in extensions:
            ext = ext.lstrip(".")
            if ext and "." not in w:
                out.append(f"{w}.{ext}")
    seen, uniq = set(), []
    for c in out:
        if c not in seen:
            seen.add(c); uniq.append(c)
    return uniq


async def worker(session, base, queue, match, filter_len, results):
    while True:
        try:
            path = queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        url = urljoin(base, path)
        try:
            async with session.get(url, allow_redirects=False) as r:
                body = await r.read()
                length = len(body)
                if r.status in match and length != filter_len:
                    loc = r.headers.get("Location", "")
                    extra = f" -> {loc}" if loc else ""
                    print(f"[{r.status}] {url}  ({length}b){extra}")
                    results.append((r.status, url, length))
        except Exception:
            pass
        finally:
            queue.task_done()


async def run(base, words, concurrency, match, filter_len, headers, timeout):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    conn = aiohttp.TCPConnector(ssl=ctx, limit=concurrency)
    to = aiohttp.ClientTimeout(total=timeout)
    queue = asyncio.Queue()
    for w in words:
        queue.put_nowait(w)
    results = []
    async with aiohttp.ClientSession(connector=conn, timeout=to,
                                     headers=headers) as session:
        tasks = [asyncio.create_task(
                    worker(session, base, queue, match, filter_len, results))
                 for _ in range(concurrency)]
        await queue.join()
        for t in tasks:
            t.cancel()
    return results


def main():
    if aiohttp is None:
        print("[!] dirquick needs aiohttp:  pip install aiohttp", file=sys.stderr)
        sys.exit(1)

    p = argparse.ArgumentParser(description="Async web content discovery.")
    p.add_argument("url", help="base URL, e.g. https://target.tld/")
    p.add_argument("-w", "--wordlist", help="wordlist file (default: built-in starter list)")
    p.add_argument("-x", "--extensions", default="", help="comma list, e.g. php,bak,txt")
    p.add_argument("-c", "--concurrency", type=int, default=50)
    p.add_argument("-m", "--match", default="200,201,204,301,302,307,401,403",
                   help="status codes to report")
    p.add_argument("--filter-length", type=int, default=-1,
                   help="hide responses of this exact byte length")
    p.add_argument("-H", "--header", action="append", default=[],
                   help="extra header 'Name: value' (repeatable)")
    p.add_argument("-T", "--timeout", type=float, default=10)
    p.add_argument("-o", "--output", help="write hits to file")
    p.add_argument("--yes-authorized", action="store_true",
                   help="confirm you are authorized to test this host")
    args = p.parse_args()

    if not args.yes_authorized:
        print("[!] dirquick sends many live requests. Re-run with --yes-authorized "
              "to confirm the host is in scope.", file=sys.stderr)
        sys.exit(2)

    base = args.url if args.url.endswith("/") else args.url + "/"
    if args.wordlist:
        with open(args.wordlist, "r", errors="ignore") as f:
            words = [x.strip().lstrip("/") for x in f if x.strip() and not x.startswith("#")]
    else:
        words = STARTER
    exts = [e for e in args.extensions.split(",") if e]
    words = build_candidates(words, exts)

    match = {int(x) for x in args.match.split(",") if x.strip()}
    headers = {"User-Agent": "dirquick/1.0"}
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()

    print(f"[*] {base}  — {len(words)} candidates, concurrency={args.concurrency}",
          file=sys.stderr)
    results = asyncio.run(run(base, words, args.concurrency, match,
                              args.filter_length, headers, args.timeout))
    print(f"[+] Done. {len(results)} hit(s).", file=sys.stderr)

    if args.output and results:
        with open(args.output, "w") as f:
            for status, url, length in sorted(results):
                f.write(f"{status} {url} {length}\n")
        print(f"[+] Saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
