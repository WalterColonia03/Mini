"""Default test discovery for the applications enabled in this project."""
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.test.runner import DiscoverRunner


class ProjectTestRunner(DiscoverRunner):
    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            base = Path(settings.BASE_DIR).resolve()
            test_labels = [
                app.name for app in apps.get_app_configs()
                if Path(app.path).resolve().parent == base
            ]
            if (base / "tests").is_dir():
                test_labels.append("tests")
        return super().build_suite(test_labels, **kwargs)
