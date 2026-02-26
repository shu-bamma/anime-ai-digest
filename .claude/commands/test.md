Run the test suite: `python -m pytest tests/ -v`

If $ARGUMENTS is provided, run only that specific test file or test function. Examples:
- `/test test_fetchers` → `python -m pytest tests/test_fetchers.py -v`
- `/test test_config` → `python -m pytest tests/test_config.py -v`
- `/test test_fetchers::test_all_fetchers_return_list` → `python -m pytest tests/test_fetchers.py::test_all_fetchers_return_list -v`

If tests fail, read the failing test and the relevant source code, then diagnose the root cause.
