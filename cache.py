import hashlib
import json
import os
import time

CACHE_DIR = ".cache"
CACHE_EXPIRY_SECONDS = 3600  # 1 hour


def _ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def _make_key(text: str) -> str:
    """Create a hash key from text."""
    return hashlib.md5(text.lower().strip().encode()).hexdigest()


def _cache_path(key: str) -> str:
    return os.path.join(CACHE_DIR, f"{key}.json")


def get_cached_response(user_message: str) -> dict | None:
    """Get cached response for a message if it exists and is fresh."""
    _ensure_cache_dir()
    key = _make_key(user_message)
    path = _cache_path(key)

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check expiry
        if time.time() - data["timestamp"] > CACHE_EXPIRY_SECONDS:
            os.remove(path)
            return None

        return data
    except Exception:
        return None


def save_cached_response(
    user_message: str,
    response: str,
    sources: list,
    tools_used: list,
    chunks: list
):
    """Save a response to cache."""
    _ensure_cache_dir()
    key = _make_key(user_message)
    path = _cache_path(key)

    data = {
        "timestamp": time.time(),
        "user_message": user_message,
        "response": response,
        "sources": sources,
        "tools_used": tools_used,
        "chunks": chunks,
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Cache write error: {e}")


def get_cache_stats() -> dict:
    """Get cache statistics."""
    _ensure_cache_dir()
    files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
    valid = 0
    expired = 0

    for f in files:
        path = os.path.join(CACHE_DIR, f)
        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            if time.time() - data["timestamp"] < CACHE_EXPIRY_SECONDS:
                valid += 1
            else:
                expired += 1
        except Exception:
            expired += 1

    return {
        "total": len(files),
        "valid": valid,
        "expired": expired
    }


def clear_cache():
    """Clear all cached responses."""
    _ensure_cache_dir()
    files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
    for f in files:
        os.remove(os.path.join(CACHE_DIR, f))
    return len(files)