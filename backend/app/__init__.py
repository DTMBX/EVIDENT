# Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
# PROPRIETARY — See LICENSE.

# Expose the Flask `app` object for tests that import `from app import app`.
# The main application object lives in `backend/src/app.py` as `app`.
try:
	# Prefer importing the app from the source module used by the test suite.
	from src.app import app as app  # type: ignore
except Exception:
	# If import fails (development layouts), leave package empty — tests will
	# surface an import error with full traceback.
	pass

