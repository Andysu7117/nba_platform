"""FastAPI web layer for the NBA platform.

The ``api`` package is the HTTP boundary around the domain logic in ``src``.
Routers stay thin and delegate to ``api.services``; ``src`` remains free of any
web framework so it can still be used from scripts, notebooks and tests.
"""
