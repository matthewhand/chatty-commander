from chatty_commander.utils.security import mask_sensitive_data
data = {
    "api_key": "secret",
    "other": "value",
    "auth": {
        "token": "secret2",
        "nested": {
            "api_key": "secret3"
        }
    },
    "list_of_stuff": [
        {"api_key": "secret4"},
        "plain"
    ]
}
print(mask_sensitive_data(data))
