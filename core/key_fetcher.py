import re
import json
import os
import time
import concurrent.futures

try:
    import requests as _requests
    _SESSION = _requests.Session()
    _SESSION.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request

CACHE_FILE = "free_keys_cache.json"
CACHE_TTL  = 3600

BASE_URL   = "https://aiapiv2.pekpik.com/v1"
README_URL = "https://raw.githubusercontent.com/alistaitsacle/free-llm-api-keys/main/README.md"

# ── Provider detection ───────────────────────────────────────
PROVIDER_HINTS = {
    "openai":    ["gpt", "openai", "chatgpt", "o1", "o3"],
    "anthropic": ["claude", "anthropic", "opus", "haiku", "sonnet"],
    "gemini":    ["gemini", "google"],
    "deepseek":  ["deepseek"],
    "kimi":      ["kimi", "moonshot"],
    "embedding": ["embed"],
}

DEFAULT_MODELS = {
    "openai":    "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-20241022",
    "gemini":    "gemini-2.5-flash",
    "deepseek":  "deepseek-chat",
    "kimi":      "kimi-k2.5",
    "embedding": "text-embedding-3-small",
    "other":     "smart-chat",
}

CATEGORY_MAP = {
    "openai":    "GPT / OpenAI",
    "anthropic": "Claude",
    "gemini":    "Gemini",
    "deepseek":  "DeepSeek",
    "kimi":      "Kimi / Moonshot",
    "embedding": "Embeddings",
    "other":     "Router / Other",
}

def _detect_provider(text: str) -> str:
    t = text.lower()
    for prov, hints in PROVIDER_HINTS.items():
        if any(h in t for h in hints):
            return prov
    return "other"


# ── HTTP helpers (requests > urllib) ────────────────────────
def _get(url: str, timeout: int = 12) -> str | None:
    """Fetch URL text — uses requests if available (bypasses CF)."""
    try:
        if HAS_REQUESTS:
            r = _SESSION.get(url, timeout=timeout)
            r.raise_for_status()
            return r.text
        else:
            import urllib.request as _u
            req = _u.Request(url, headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                )
            })
            with _u.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
    except Exception as e:
        print(f"[key_fetcher] GET {url} failed: {e}")
        return None


def _post_json(url: str, payload: dict, api_key: str, timeout: int = 8):
    """
    POST JSON with browser-like headers to bypass Cloudflare.
    Returns (status_code, body_dict_or_None, latency_ms).
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://aiapiv2.pekpik.com",
        "Referer": "https://aiapiv2.pekpik.com/",
    }
    t0 = time.time()
    try:
        if HAS_REQUESTS:
            resp = _requests.post(url, json=payload, headers=headers, timeout=timeout)
            lat  = int((time.time() - t0) * 1000)
            try:
                body = resp.json()
            except Exception:
                body = {"_raw": resp.text}
            return resp.status_code, body, lat
        else:
            import urllib.request as _u
            data = json.dumps(payload).encode()
            req  = _u.Request(url, data=data, headers=headers, method="POST")
            with _u.urlopen(req, timeout=timeout) as r:
                lat  = int((time.time() - t0) * 1000)
                body = json.loads(r.read().decode())
                return r.status, body, lat
    except Exception as e:
        lat = int((time.time() - t0) * 1000)
        return 0, {"error": str(e)}, lat


# ── README fetch & parse ─────────────────────────────────────
def fetch_readme() -> str | None:
    return _get(README_URL)


def parse_keys_from_markdown(md: str) -> dict:
    if not md:
        return {}

    pool: dict[str, list] = {name: [] for name in CATEGORY_MAP.values()}
    current_provider = "other"

    for raw_line in md.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("#"):
            current_provider = _detect_provider(line)
            continue

        key_match = re.search(r"(sk-[A-Za-z0-9\-]{20,90})", line)
        if not key_match:
            if any(h in line.lower() for hints in PROVIDER_HINTS.values() for h in hints):
                current_provider = _detect_provider(line)
            continue

        key    = key_match.group(1)
        model  = DEFAULT_MODELS.get(current_provider, "smart-chat")
        budget = rate = expires = desc = "-"

        if line.startswith("|"):
            cols = [c.strip().replace("`", "") for c in line.split("|") if c.strip()]
            if all(re.match(r"^[-:]+$", c) for c in cols):
                continue
            ki = next((i for i, c in enumerate(cols) if c.startswith("sk-")), -1)
            if ki != -1:
                model   = cols[ki + 1] if ki + 1 < len(cols) else model
                budget  = cols[ki + 3] if ki + 3 < len(cols) else "-"
                rate    = cols[ki + 4] if ki + 4 < len(cols) else "-"
                expires = cols[ki + 5] if ki + 5 < len(cols) else "-"
                desc    = cols[ki + 6] if ki + 6 < len(cols) else "-"
        else:
            rest   = line.replace(key, "").strip()
            tokens = [t.strip() for t in re.split(r"\t|\s{2,}", rest) if t.strip()]
            if not tokens:
                tokens = rest.split()
            if any(t.lower() in ("key", "model", "status", "budget") for t in tokens):
                continue
            for tok in tokens:
                if re.match(r"^\d{4}-\d{2}-\d{2}$", tok):
                    expires = tok
                elif tok.startswith("$") or re.match(r"^\d+\$?$", tok):
                    budget = tok
                elif re.match(r"^\d+\s*RPM$", tok, re.I) or "rpm" in tok.lower():
                    rate = tok
                elif tok.lower() not in ("new", "active", "🆕") \
                     and not tok.startswith("$") \
                     and "rpm" not in tok.lower():
                    model = tok

        prov   = _detect_provider(model) if model else current_provider
        ui_cat = CATEGORY_MAP.get(prov, CATEGORY_MAP["other"])

        entry = {
            "key":      key,
            "model":    model,
            "provider": prov,
            "budget":   budget,
            "rate":     rate,
            "expires":  expires,
            "desc":     desc,
            "status":   "pending",
            "latency":  "—",
        }
        if ui_cat in pool:
            pool[ui_cat].append(entry)

    return {cat: lst for cat, lst in pool.items() if lst}


# ── Key tester ────────────────────────────────────────────────
def _test_key(entry: dict) -> dict:
    """Tests one key through the pekpik proxy with proper CF-bypass headers."""
    key   = entry["key"]
    model = entry.get("model", "smart-chat")
    is_emb = "embed" in model.lower()

    if is_emb:
        url     = f"{BASE_URL}/embeddings"
        payload = {"model": model, "input": "ok"}
    else:
        url     = f"{BASE_URL}/chat/completions"
        payload = {
            "model":     model,
            "messages":  [{"role": "user", "content": "Say ok"}],
            "max_tokens": 5,
        }

    status_code, body, lat = _post_json(url, payload, key, timeout=8)

    if status_code == 200 and ("choices" in body or "data" in body):
        entry["status"]  = "Active"
        entry["latency"] = f"{lat}ms"
    else:
        entry["status"]  = "Offline"
        entry["latency"] = "—"
        err = body.get("error", {})
        if isinstance(err, dict):
            entry["_err"] = err.get("message", str(body))[:80]
        else:
            entry["_err"] = str(err)[:80]

    return entry


def verify_all_keys(pool: dict, max_workers: int = 10) -> dict:
    flat = [(cat, e) for cat, lst in pool.items() for e in lst]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_test_key, e): (cat, e) for cat, e in flat}
        for f in concurrent.futures.as_completed(futs):
            try:
                f.result()
            except Exception:
                pass
    return pool


# ── Public entry point ────────────────────────────────────────
def get_free_keys(force_refresh: bool = False, test_active: bool = True) -> dict:
    pool = None

    if not force_refresh and os.path.exists(CACHE_FILE):
        if time.time() - os.path.getmtime(CACHE_FILE) < CACHE_TTL:
            try:
                with open(CACHE_FILE, encoding="utf-8") as f:
                    pool = json.load(f)
                # If cached keys have no status yet, still re-test them
            except Exception:
                pool = None

    if not pool:
        print("[key_fetcher] Fetching live README…")
        md   = fetch_readme()
        pool = parse_keys_from_markdown(md) if md else {}
        if pool:
            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(pool, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[key_fetcher] Cache write failed: {e}")

    if not pool:
        return {}

    if test_active:
        print("[key_fetcher] Testing key connectivity with CF-bypass headers…")
        pool = verify_all_keys(pool)

    return pool


if __name__ == "__main__":
    result = get_free_keys(force_refresh=True, test_active=True)
    active = sum(1 for lst in result.values() for e in lst if e["status"] == "Active")
    total  = sum(len(lst) for lst in result.values())
    print(f"\n=== {active} active / {total} total ===")
    for cat, lst in result.items():
        for e in lst:
            flag = "OK " if e["status"] == "Active" else "ERR"
            print(f"  [{flag}] {cat:<22} {e['model'][:28]:<28} {e['latency']:<7} {e['key'][:14]}...")
