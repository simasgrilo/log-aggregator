"""
LogAggregator app entrypoint. Decouples the app from the main module, allowing for easier testing and modularity.
This was motivated by a issue when implementing unit tests that require a mocked config.json, which I believe 
it's better not to push a real file (see file test_auth_handlers.py for more details).
"""

from LogAggregator import LogAggregator

app = LogAggregator().app
