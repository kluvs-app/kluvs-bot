"""
Tests for scheduled tasks
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from utils.schedulers import setup_scheduled_tasks


class TestSchedulers(unittest.IsolatedAsyncioTestCase):
    """Test cases for scheduled tasks - PROPERLY ASYNC"""

    def setUp(self):
        """Set up common test fixtures"""
        self.bot = MagicMock()
        self.bot.config = MagicMock()
        mock_guild = MagicMock()
        mock_guild.id = 111111
        self.bot.guilds = [mock_guild]
        self.bot.api.get_server_clubs.return_value = [{'id': 'club-1', 'discord_channel': '123456'}]
        self.bot.get_channel = MagicMock()

    @patch('utils.schedulers.tasks.loop')
    async def test_reminder_at_5pm_pacific_triggers(self, mock_loop):
        """Scheduler is disabled pending per-club notification settings — no messages sent"""
        mock_channel = AsyncMock()
        self.bot.get_channel.return_value = mock_channel

        captured_func = None

        def capture_loop(*args, **kwargs):
            def decorator(func):
                nonlocal captured_func
                captured_func = func
                mock_task = MagicMock()
                mock_task.start = MagicMock()
                return mock_task
            return decorator

        mock_loop.side_effect = capture_loop
        setup_scheduled_tasks(self.bot)
        self.assertIsNotNone(captured_func)
        await captured_func()

        # Scheduler is intentionally disabled — no messages should be sent
        mock_channel.send.assert_not_called()

    @patch('utils.schedulers.tasks.loop')
    async def test_reminder_wrong_hour_no_send(self, mock_loop):
        """Scheduler is disabled — no messages sent regardless of time"""
        mock_channel = AsyncMock()
        self.bot.get_channel.return_value = mock_channel

        captured_func = None

        def capture_loop(*args, **kwargs):
            def decorator(func):
                nonlocal captured_func
                captured_func = func
                mock_task = MagicMock()
                mock_task.start = MagicMock()
                return mock_task
            return decorator

        mock_loop.side_effect = capture_loop
        setup_scheduled_tasks(self.bot)
        await captured_func()

        mock_channel.send.assert_not_called()

    @patch('utils.schedulers.tasks.loop')
    async def test_reminder_probability_check(self, mock_loop):
        """Scheduler is disabled — no messages sent regardless of probability"""
        mock_channel = AsyncMock()
        self.bot.get_channel.return_value = mock_channel

        captured_func = None

        def capture_loop(*args, **kwargs):
            def decorator(func):
                nonlocal captured_func
                captured_func = func
                mock_task = MagicMock()
                mock_task.start = MagicMock()
                return mock_task
            return decorator

        mock_loop.side_effect = capture_loop
        setup_scheduled_tasks(self.bot)
        await captured_func()

        mock_channel.send.assert_not_called()

    @patch('utils.schedulers.tasks.loop')
    async def test_reminder_no_channel(self, mock_loop):
        """Scheduler is disabled — runs without error even with no channel"""
        self.bot.get_channel.return_value = None

        captured_func = None

        def capture_loop(*args, **kwargs):
            def decorator(func):
                nonlocal captured_func
                captured_func = func
                mock_task = MagicMock()
                mock_task.start = MagicMock()
                return mock_task
            return decorator

        mock_loop.side_effect = capture_loop
        setup_scheduled_tasks(self.bot)
        await captured_func()

        # No exception should be raised

    @patch('utils.schedulers.tasks.loop')
    def test_setup_scheduled_tasks_returns_task(self, mock_loop):
        """Test that setup returns the scheduled task"""
        mock_task = MagicMock()
        mock_task.start = MagicMock()

        def mock_loop_decorator(*args, **kwargs):
            def decorator(func):
                return mock_task
            return decorator

        mock_loop.side_effect = mock_loop_decorator

        result = setup_scheduled_tasks(self.bot)

        # Verify task was returned
        self.assertEqual(result, mock_task)

    @patch('utils.schedulers.tasks.loop')
    def test_loop_configured_correctly(self, mock_loop):
        """Test that the task loop is configured for 1 hour intervals"""
        mock_task = MagicMock()

        def mock_loop_decorator(*args, **kwargs):
            # Verify hours=1 was passed
            self.assertEqual(kwargs.get('hours'), 1)

            def decorator(func):
                return mock_task
            return decorator

        mock_loop.side_effect = mock_loop_decorator

        setup_scheduled_tasks(self.bot)

        # Verify loop was called with correct parameters
        mock_loop.assert_called_once_with(hours=1)


if __name__ == '__main__':
    unittest.main()
