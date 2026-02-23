# create fixtures in here

# start with the datadir

import pytest
from pathlib import Path
from typing import Generator


# I have a data dir which is in tests/data dir and this file is in tests
@pytest.fixture(scope="class")
def test_data_dir() -> Generator[Path, None, None]:
    yield Path(__file__).parent / "data"
