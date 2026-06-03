import subprocess
import sys
from pathlib import Path


def test_celery_app_imports_grid_storyboard_task_without_import_cycle():
    backend_dir = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from app.core.celery_app import celery_app; "
                "assert 'tasks.grid_storyboard_sheet_generate' in celery_app.tasks"
            ),
        ],
        cwd=backend_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
