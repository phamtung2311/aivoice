import importlib
import pkgutil
import sys
import traceback

# ensure workspace root in path
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TEST_PKG = 'tests'

failed = []
passed = []

# import all modules in tests package
for finder, name, ispkg in pkgutil.iter_modules([os.path.join(ROOT, 'tests')]):
    full = f"tests.{name}"
    try:
        mod = importlib.import_module(full)
    except Exception:
        print(f"ERROR importing {full}")
        traceback.print_exc()
        failed.append((full, 'import-error'))
        continue

    # call setup_module if present
    try:
        if hasattr(mod, 'setup_module'):
            mod.setup_module(None)
    except Exception:
        print(f"ERROR in setup_module for {full}")
        traceback.print_exc()
        failed.append((full, 'setup-error'))
        continue

    # find test_ functions
    for attr in dir(mod):
        if attr.startswith('test_') and callable(getattr(mod, attr)):
            fn = getattr(mod, attr)
            try:
                fn()
                print(f"PASS {full}.{attr}")
                passed.append((full, attr))
            except AssertionError:
                print(f"FAIL {full}.{attr} (AssertionError)")
                traceback.print_exc()
                failed.append((full, attr))
            except Exception:
                print(f"ERROR {full}.{attr}")
                traceback.print_exc()
                failed.append((full, attr))

    # call teardown_module if present
    try:
        if hasattr(mod, 'teardown_module'):
            mod.teardown_module(None)
    except Exception:
        print(f"ERROR in teardown_module for {full}")
        traceback.print_exc()
        failed.append((full, 'teardown-error'))

print('\nSUMMARY:')
print(f'Passed: {len(passed)}')
print(f'Failed: {len(failed)}')
if failed:
    print('\nFailures detail:')
    for f in failed:
        print('-', f)
    sys.exit(2)
else:
    print('All tests passed')
    sys.exit(0)
