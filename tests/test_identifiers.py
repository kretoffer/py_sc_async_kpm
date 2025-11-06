from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch

from sc_async_client.models import ScAddr

from sc_async_kpm.identifiers import _IdentifiersResolver


class TestIdentifiers(IsolatedAsyncioTestCase):
    @patch("sc_async_kpm.identifiers.ScKeynodes", new_callable=MagicMock)
    async def test_resolve(self, keynodes_mock: MagicMock):
        keynodes_mock.resolve = AsyncMock(return_value=ScAddr(1))

        # First call
        await _IdentifiersResolver.resolve()
        self.assertTrue(_IdentifiersResolver.is_resolved)
        self.assertGreater(keynodes_mock.resolve.call_count, 0)

        # Second call (should be skipped)
        call_count = keynodes_mock.resolve.call_count
        await _IdentifiersResolver.resolve()
        self.assertEqual(keynodes_mock.resolve.call_count, call_count)

        # Reset for another test
        _IdentifiersResolver.is_resolved = False
