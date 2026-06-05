import timeit
from src.chatty_commander.utils.security import mask_sensitive_data as mask_sensitive_data_orig

# Prepare optimized version
SENSITIVE_PATTERNS_TUPLE = (
    "api_key",
    "api_token",
    "access_token",
    "auth_token",
    "bridge_token",
    "password",
    "passwd",
    "secret",
    "database_url",
    "token",
)

def mask_sensitive_data_optimized(data):
    """Recursively mask sensitive keys in a dictionary or list."""
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            k_str = str(k)
            k_lower = k_str.lower()

            # Fast path checking
            is_sensitive = False
            for p in SENSITIVE_PATTERNS_TUPLE:
                if p in k_lower:
                    is_sensitive = True
                    break

            if is_sensitive:
                masked[k] = "********"
            elif k_lower == "auth":
                # Special case for 'auth' which often contains credentials
                if isinstance(v, dict):
                    masked[k] = mask_sensitive_data_optimized(v)
                else:
                    masked[k] = "********"
            else:
                masked[k] = mask_sensitive_data_optimized(v)
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data_optimized(item) for item in data]
    return data

data = {
    f"key_{i}": f"val_{i}" for i in range(100)
}
data["auth"] = {f"auth_key_{i}": f"auth_val_{i}" for i in range(20)}
data["auth"]["api_key"] = "test"
data["list_of_stuff"] = [{"token": "sec"}, "plain"]

print("Orig:", timeit.timeit("mask_sensitive_data_orig(data)", globals=globals(), number=10000))
print("Optimized:", timeit.timeit("mask_sensitive_data_optimized(data)", globals=globals(), number=10000))
