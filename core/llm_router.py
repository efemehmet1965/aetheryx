import os
import json

try:
    import requests as _req
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Browser-like headers to bypass Cloudflare on pekpik.com
_CF_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://aiapiv2.pekpik.com",
    "Referer": "https://aiapiv2.pekpik.com/",
}

def _post(url, headers, payload, timeout=30):
    """
    POST helper — uses requests with CF-bypass headers when available,
    falls back to urllib with the same headers.
    Returns (status_code, response_dict).
    """
    merged = {**_CF_HEADERS, **headers}
    if HAS_REQUESTS:
        try:
            r = _req.post(url, headers=merged, json=payload, timeout=timeout)
            try:
                return r.status_code, r.json()
            except Exception:
                return r.status_code, {"error": r.text}
        except Exception as e:
            return 0, {"error": str(e)}
    else:
        import urllib.request
        data = json.dumps(payload).encode()
        req  = urllib.request.Request(url, data=data, headers=merged, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read().decode())
            except Exception:
                body = {"error": str(e)}
            return e.code, body
        except Exception as e:
            return 0, {"error": str(e)}


class MultiLLMRouter:
    def __init__(self):
        self.default_base_url = "https://aiapiv2.pekpik.com/v1"
        self.custom_keys = {
            "OpenAI":    os.getenv("OPENAI_API_KEY", ""),
            "Anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
            "Gemini":    os.getenv("GEMINI_API_KEY", ""),
            "DeepSeek":  os.getenv("DEEPSEEK_API_KEY", "")
        }

    def update_custom_key(self, provider, key):
        if provider in self.custom_keys:
            self.custom_keys[provider] = key

    def get_custom_key(self, provider):
        return self.custom_keys.get(provider, "")

    def execute_completion(self, model, messages, custom_mode=False, custom_key="", provider="", free_keys_pool=None):
        """
        Routes completion through custom keys or free-key pool with CF-bypass headers.
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
        }

        # ── Custom key mode ───────────────────────────────────
        if custom_mode and custom_key:
            headers = {
                "Authorization": f"Bearer {custom_key}",
                "Content-Type": "application/json",
            }
            endpoint = f"{self.default_base_url}/chat/completions"
            if provider == "OpenAI":
                endpoint = "https://api.openai.com/v1/chat/completions"
            elif provider == "DeepSeek":
                endpoint = "https://api.deepseek.com/chat/completions"
            elif provider == "Anthropic":
                endpoint = "https://api.anthropic.com/v1/messages"

            status, data = _post(endpoint, headers, payload, timeout=30)
            if status == 200:
                try:
                    return data["choices"][0]["message"]["content"], None
                except Exception:
                    return None, f"Unexpected response format: {str(data)[:200]}"
            return None, f"Custom API error ({status}): {str(data)[:200]}"

        # ── Free keys pool mode ───────────────────────────────
        if not free_keys_pool:
            return None, "No free keys pool provided and no custom keys configured."

        # Match model keyword to pool category (updated to match new category names)
        category_map = {
            "gemini":   "Gemini",
            "claude":   "Claude",
            "deepseek": "DeepSeek",
            "gpt":      "GPT / OpenAI",
            "kimi":     "Kimi / Moonshot",
        }
        selected_category = None
        for kw, cat in category_map.items():
            if kw in model.lower():
                selected_category = cat
                break

        # Build target list: preferred category first, then all active keys as fallback
        target_keys = []
        if selected_category:
            target_keys = [k for k in free_keys_pool.get(selected_category, [])
                           if k.get("status") == "Active"]

        if not target_keys:
            # fallback: all active keys across every category
            for lst in free_keys_pool.values():
                target_keys.extend(k for k in lst if k.get("status") == "Active")

        if not target_keys:
            # last resort: every key regardless of tested status
            for lst in free_keys_pool.values():
                target_keys.extend(lst)

        if not target_keys:
            return None, "Free keys pool is empty."

        endpoint = f"{self.default_base_url}/chat/completions"
        last_error = ""

        for key_info in target_keys:
            key         = key_info["key"]
            actual_model = key_info.get("model", model)
            payload["model"] = actual_model

            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type":  "application/json",
            }
            status, data = _post(endpoint, headers, payload, timeout=20)

            if status == 200:
                try:
                    content = data["choices"][0]["message"]["content"]
                    return content, {
                        "key":       f"{key[:8]}...{key[-4:]}",
                        "model":     actual_model,
                        "status":    "Success",
                        "latency":   key_info.get("latency", "N/A"),
                    }
                except Exception as e:
                    last_error = f"Parse error: {e}"
                    continue
            else:
                err_msg = data.get("error", {})
                if isinstance(err_msg, dict):
                    err_msg = err_msg.get("message", str(data))
                last_error = f"HTTP {status}: {str(err_msg)[:120]}"
                print(f"[router] Key {key[:10]} failed — {last_error}")
                continue

        return None, f"All keys failed. Last error: {last_error}"
