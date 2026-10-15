"""Test package.

The environment is configured here, at import time of the ``tests`` package, so
that it is set BEFORE ``tests.conftest`` imports the application and its database
engine. No API key value is committed anywhere: the key is rolled per run.
"""

import os
import secrets
import tempfile

os.environ["LIBRARY_API_KEY"] = secrets.token_hex(32)
_TEST_DB_DIR = tempfile.mkdtemp(prefix="library-test-")
os.environ["LIBRARY_DB_PATH"] = os.path.join(_TEST_DB_DIR, "test_library.db")
