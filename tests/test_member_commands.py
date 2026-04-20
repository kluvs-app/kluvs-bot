"""
Tests for member commands (join, leave)
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from cogs.member_commands import setup_member_commands
from api.bookclub_api import ResourceNotFoundError


class TestMemberCommands(unittest.IsolatedAsyncioTestCase):
    """Test cases for member commands - PROPERLY ASYNC"""

    def setUp(self):
        """Set up common test fixtures"""
        # Create a mock bot
        self.bot = MagicMock()
        self.bot.tree = MagicMock()

        # Mock API
        self.bot.api = MagicMock()

        # Store the registered commands
        self.commands = {}

        # Mock the bot.tree.command decorator
        def mock_command(**kwargs):
            def decorator(func):
                # Store the command and its properties
                self.commands[kwargs.get('name')] = {
                    'func': func,
                    'kwargs': kwargs
                }
                return func
            return decorator

        self.bot.tree.command = mock_command

        # Register the commands
        setup_member_commands(self.bot)

        # Verify commands were registered
        self.assertIn('join', self.commands)
        self.assertIn('leave', self.commands)

    async def test_join_command_success(self):
        """Test the join command with a new member"""
        # Mock API responses
        self.bot.api.find_club_in_channel = MagicMock(return_value={
            'id': 'club-1',
            'name': 'Test Book Club',
            'server_id': '123456'
        })
        self.bot.api.get_member_by_discord_id = MagicMock(return_value=None)
        self.bot.api.create_member = MagicMock(return_value={
            'id': 'member-1',
            'name': 'Test User',
            'discord_id': '111111',
            'clubs': ['club-1']
        })

        # Mock interaction
        interaction = AsyncMock()
        interaction.guild_id = 123456
        interaction.channel_id = 789012
        interaction.user.id = 111111
        interaction.user.display_name = 'Test User'
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        # Run the command
        join_command = self.commands['join']['func']
        await join_command(interaction)

        # Verify defer was called
        interaction.response.defer.assert_called_once()

        # Verify API was called correctly
        self.bot.api.find_club_in_channel.assert_called_once_with('789012', '123456')
        self.bot.api.get_member_by_discord_id.assert_called_once_with('111111')
        self.bot.api.create_member.assert_called_once()

        # Verify response was sent
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        self.assertIn('embed', call_args.kwargs)
        embed = call_args.kwargs['embed']
        self.assertIn('Welcome to the Club', embed.title)

    async def test_join_command_no_club_found(self):
        """Test the join command when no club is found in channel"""
        # Mock API to return no club
        self.bot.api.find_club_in_channel = MagicMock(return_value=None)

        # Mock interaction
        interaction = AsyncMock()
        interaction.guild_id = 123456
        interaction.channel_id = 789012
        interaction.user.id = 111111
        interaction.user.display_name = 'Test User'
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        # Run the command
        join_command = self.commands['join']['func']
        await join_command(interaction)

        # Verify defer was called
        interaction.response.defer.assert_called_once()

        # Verify API was called
        self.bot.api.find_club_in_channel.assert_called_once_with('789012', '123456')

        # Verify error message was sent
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        self.assertIn('No book club found', call_args.args[0])

    async def test_join_command_already_member(self):
        """Test the join command when user is already a member"""
        # Mock API responses
        club_data = {
            'id': 'club-1',
            'name': 'Test Book Club',
            'server_id': '123456'
        }
        self.bot.api.find_club_in_channel = MagicMock(return_value=club_data)
        self.bot.api.get_member_by_discord_id = MagicMock(return_value={
            'id': 'member-1',
            'name': 'Test User',
            'discord_id': '111111',
            'clubs': [{'id': 'club-1', 'name': 'Test Book Club'}]
        })

        # Mock interaction
        interaction = AsyncMock()
        interaction.guild_id = 123456
        interaction.channel_id = 789012
        interaction.user.id = 111111
        interaction.user.display_name = 'Test User'
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        # Run the command
        join_command = self.commands['join']['func']
        await join_command(interaction)

        # Verify defer was called
        interaction.response.defer.assert_called_once()

        # Verify info message was sent
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        self.assertIn('already a member', call_args.args[0])

        # Verify create_member was NOT called
        self.bot.api.create_member.assert_not_called()

    async def test_join_command_dm_not_allowed(self):
        """Test that join command fails in DM"""
        # Mock interaction with no guild_id
        interaction = AsyncMock()
        interaction.guild_id = None
        interaction.response.send_message = AsyncMock()

        # Run the command
        join_command = self.commands['join']['func']
        await join_command(interaction)

        # Verify error message was sent
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        self.assertIn('Discord server', call_args.args[0])

    async def test_leave_command_success(self):
        """Test the leave command when user is a member"""
        # Mock API responses
        club_data = {
            'id': 'club-1',
            'name': 'Test Book Club',
            'server_id': '123456'
        }
        self.bot.api.find_club_in_channel = MagicMock(return_value=club_data)
        self.bot.api.get_member_by_discord_id = MagicMock(return_value={
            'id': 'member-1',
            'name': 'Test User',
            'discord_id': '111111',
            'clubs': [{'id': 'club-1', 'name': 'Test Book Club'}]
        })
        self.bot.api.delete_member = MagicMock(return_value={
            'success': True,
            'message': 'Member deleted'
        })

        # Mock interaction
        interaction = AsyncMock()
        interaction.guild_id = 123456
        interaction.channel_id = 789012
        interaction.user.id = 111111
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        # Run the command
        leave_command = self.commands['leave']['func']
        await leave_command(interaction)

        # Verify defer was called
        interaction.response.defer.assert_called_once()

        # Verify API was called correctly
        self.bot.api.find_club_in_channel.assert_called_once_with('789012', '123456')
        self.bot.api.get_member_by_discord_id.assert_called_once_with('111111')
        self.bot.api.delete_member.assert_called_once_with('member-1')

        # Verify response was sent
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        self.assertIn('embed', call_args.kwargs)
        embed = call_args.kwargs['embed']
        self.assertIn('See You Later', embed.title)

    async def test_leave_command_with_multiple_clubs(self):
        """Test the leave command when user is in multiple clubs"""
        # Mock API responses
        club_data = {
            'id': 'club-1',
            'name': 'Test Book Club 1',
            'server_id': '123456'
        }
        self.bot.api.find_club_in_channel = MagicMock(return_value=club_data)
        self.bot.api.get_member_by_discord_id = MagicMock(return_value={
            'id': 'member-1',
            'name': 'Test User',
            'discord_id': '111111',
            'clubs': [
                {'id': 'club-1', 'name': 'Test Book Club 1'},
                {'id': 'club-2', 'name': 'Test Book Club 2'}
            ]
        })
        self.bot.api.update_member = MagicMock(return_value={
            'success': True,
            'message': 'Member updated'
        })

        # Mock interaction
        interaction = AsyncMock()
        interaction.guild_id = 123456
        interaction.channel_id = 789012
        interaction.user.id = 111111
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        # Run the command
        leave_command = self.commands['leave']['func']
        await leave_command(interaction)

        # Verify defer was called
        interaction.response.defer.assert_called_once()

        # Verify update_member was called (not delete_member)
        self.bot.api.update_member.assert_called_once()
        call_args = self.bot.api.update_member.call_args
        self.assertEqual(call_args[0][0], 'member-1')
        # Verify that remaining clubs only include club-2
        self.assertEqual(call_args[0][1]['clubs'], ['club-2'])

        # Verify delete_member was NOT called
        self.bot.api.delete_member.assert_not_called()

    async def test_leave_command_not_member(self):
        """Test the leave command when user is not a member"""
        # Mock API responses
        self.bot.api.find_club_in_channel = MagicMock(return_value={
            'id': 'club-1',
            'name': 'Test Book Club',
            'server_id': '123456'
        })
        self.bot.api.get_member_by_discord_id = MagicMock(return_value=None)

        # Mock interaction
        interaction = AsyncMock()
        interaction.guild_id = 123456
        interaction.channel_id = 789012
        interaction.user.id = 111111
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        # Run the command
        leave_command = self.commands['leave']['func']
        await leave_command(interaction)

        # Verify defer was called
        interaction.response.defer.assert_called_once()

        # Verify info message was sent
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        self.assertIn('not a member', call_args.args[0])

    async def test_leave_command_no_club_found(self):
        """Test the leave command when no club is found in channel"""
        # Mock API to return no club
        self.bot.api.find_club_in_channel = MagicMock(return_value=None)

        # Mock interaction
        interaction = AsyncMock()
        interaction.guild_id = 123456
        interaction.channel_id = 789012
        interaction.user.id = 111111
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        # Run the command
        leave_command = self.commands['leave']['func']
        await leave_command(interaction)

        # Verify defer was called
        interaction.response.defer.assert_called_once()

        # Verify error message was sent
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        self.assertIn('No book club found', call_args.args[0])

    async def test_leave_command_dm_not_allowed(self):
        """Test that leave command fails in DM"""
        # Mock interaction with no guild_id
        interaction = AsyncMock()
        interaction.guild_id = None
        interaction.response.send_message = AsyncMock()

        # Run the command
        leave_command = self.commands['leave']['func']
        await leave_command(interaction)

        # Verify error message was sent
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        self.assertIn('Discord server', call_args.args[0])


if __name__ == '__main__':
    unittest.main()
