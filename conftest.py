import sys
import os
import pytest

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '.')))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Let pytest process everything first still
    outcome = yield
    result = outcome.get_result()

    # Only do custom printing if the actual test call phase failed
    if result.when == "call" and result.failed:
        # One final thing: check if we have a 'reprcrash' (the part that stores path / lineno / message)
        if hasattr(result.longrepr, "reprcrash"):
            path = result.longrepr.reprcrash.path
            lineno = result.longrepr.reprcrash.lineno
            message = result.longrepr.reprcrash.message
            print(f"[FAILED] {path}:{lineno} => {message}")
        else:
            # If, for some reason, there's no reprcrash, fall back:
            print(f"[FAILED] {item.nodeid} => {result.longrepr}")
