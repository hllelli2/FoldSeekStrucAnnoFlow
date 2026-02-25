# create fixtures in here

# start with the datadir

from pathlib import Path
from typing import Generator

import pytest


# I have a data dir which is in tests/data dir and this file is in tests
@pytest.fixture(scope="class")
def test_data_dir() -> Generator[Path, None, None]:
    print(Path(__file__).parent)
    yield Path(__file__).parent / "data"


@pytest.fixture(scope="class")
def tmp_dir(tmp_path_factory) -> Generator[Path, None, None]:
    yield tmp_path_factory.mktemp("tmp")
