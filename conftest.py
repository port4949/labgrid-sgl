import pytest

@pytest.fixture
def beaglev(strategy):
  strategy.transition("shell")
  return strategy.shell
