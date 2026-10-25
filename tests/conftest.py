import pytest

import i18n


@pytest.fixture(autouse=True)
def _reset_language():
    i18n.set_language("pt")
    yield
    i18n.set_language("pt")
