import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture()
def temp_path():
    """Temporary path cleaned after the tests run."""
    path = Path(tempfile.mkdtemp())
    yield path
    shutil.rmtree(path)
