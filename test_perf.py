import timeit

def orig(data):
    sensitive_patterns = {
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
    }

    masked = {}
    for k, v in data.items():
        if any(p in str(k).lower() for p in sensitive_patterns):
            masked[k] = "********"
        else:
            masked[k] = v
    return masked

SENSITIVE_PATTERNS = (
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

def new2(data):
    masked = {}
    for k, v in data.items():
        k_lower = str(k).lower()
        is_sensitive = False
        for p in SENSITIVE_PATTERNS:
            if p in k_lower:
                is_sensitive = True
                break

        if is_sensitive:
            masked[k] = "********"
        else:
            masked[k] = v
    return masked

data = {f"key_{i}": f"val_{i}" for i in range(100)}
data["my_api_key_1"] = "test"

print("Orig:", timeit.timeit("orig(data)", globals=globals(), number=10000))
print("New2:", timeit.timeit("new2(data)", globals=globals(), number=10000))
