"""Test setup: force offline mode and an isolated temp database.

Runs at conftest import time — before test modules import the app — so the
settings are in place before `app.main` calls `load_dotenv()`.

Offline is the honest default here. Unlike a system where the model produces
the score, nothing in this service's decision path calls an API, so the whole
suite runs with no key and still exercises every gate. What is skipped is the
advisory reading and the drafted email wording, both of which have static
fallbacks that the tests do cover.
"""

import os
import tempfile
from pathlib import Path

os.environ["LLM_API_KEY"] = ""

from app.core.config import settings  # noqa: E402
from app.services import report_repository  # noqa: E402

_TEST_ROOT = Path(tempfile.mkdtemp(prefix="irr-test-"))
settings.db_path = _TEST_ROOT / "test.db"

# Submitted attachments and generated certificates land here. Pointing them at
# the temp root keeps a test run from leaving files in the working tree.
settings.storage_root = _TEST_ROOT / "tasks"

# TestClient(app) at module level does not run the lifespan hook that would
# otherwise create the table.
report_repository.init_db()
