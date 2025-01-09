"""Unit tests for the api module."""

import pytest
from rso_cart import api


@pytest.mark.asyncio
async def test_root():
    result = await api.root()
    assert type(result) is dict
