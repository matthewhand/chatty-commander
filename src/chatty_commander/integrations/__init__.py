"""Optional integrations with external services (Dograh, etc.).

Integrations in this package are *optional*. Importing this module never
forces a hard dependency on any third-party service; concrete clients
lazy-load and surface clear errors when their configuration is missing.
"""
