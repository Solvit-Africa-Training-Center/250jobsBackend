"""Aggregate tests package so `python manage.py test tests` works."""

from importlib import import_module
from pathlib import Path

from django.conf import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_IMPORTED_PACKAGES = []

for app_label in settings.INSTALLED_APPS:
    try:
        module = import_module(f"{app_label}.tests")
    except ModuleNotFoundError:
        continue
    module_path = Path(getattr(module, "__file__", ""))
    try:
        module_path.resolve().relative_to(_PROJECT_ROOT)
    except ValueError:
        continue
    _IMPORTED_PACKAGES.append(module)


def load_tests(loader, tests, pattern):
    suite = loader.suiteClass()
    pattern = pattern or "test*.py"
    for package in _IMPORTED_PACKAGES:
        module_path = Path(getattr(package, "__file__", ""))
        if not module_path:
            continue
        start_dir = module_path.parent
        suite.addTests(loader.discover(
            start_dir=str(start_dir),
            pattern=pattern,
            top_level_dir=str(_PROJECT_ROOT)
        ))
    return suite
