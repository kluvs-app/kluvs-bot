"""
Tests for admin commands
"""
import unittest
from unittest.mock import patch, MagicMock, AsyncMock, mock_open

from cogs.admin_commands import setup_admin_commands
from api.bookclub_api import APIError


def _make_bot():
    """Creates a mock bot with api and wait_for."""
    bot = MagicMock()
    bot.api = MagicMock()
    bot.wait_for = AsyncMock()
    commands = {}

    def mock_command(**kwargs):
        def decorator(func):
            commands[kwargs.get("name")] = {"func": func, "kwargs": kwargs}
            return func
        return decorator

    bot.command = mock_command
    setup_admin_commands(bot)
    return bot, commands


def _make_ctx(*, is_owner=True, author_id="111", channel_id="999", guild_id="888"):
    """Creates a mock command context."""
    ctx = AsyncMock()
    ctx.send = AsyncMock()
    ctx.author.id = author_id
    ctx.channel.id = channel_id
    ctx.guild.id = guild_id
    ctx.guild.name = "Test Server"
    ctx.guild.owner = ctx.author if is_owner else MagicMock()
    return ctx


def _club_with_admin(author_id, club_id="club-1", session_id="sess-1"):
    """Returns club data where the author is an admin."""
    return {
        "id": club_id,
        "name": "Test Club",
        "discord_channel": "999",
        "members": [{"discord_id": str(author_id), "role": "admin"}],
        "active_session": {"id": session_id, "book": {"title": "Dune", "author": "Herbert"}},
    }


class TestConfirmFlow(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot, self.commands = _make_bot()

    async def test_confirm_timeout(self):
        ctx = _make_ctx()
        self.bot.wait_for.side_effect = TimeoutError()
        club = _club_with_admin("111")
        self.bot.api.find_club_in_channel.return_value = club
        await self.commands["club_delete"]["func"](ctx)
        # Should not call API when timeout occurs
        self.bot.api.delete_club.assert_not_called()
        # Should have sent 3 messages: prompt, timeout, and cancellation
        self.assertEqual(ctx.send.call_count, 3)

    async def test_confirm_check_predicate_invoked(self):
        ctx = _make_ctx()

        async def fake_wait_for(_event, *, timeout=30.0, check=None):
            msg = MagicMock()
            msg.author = ctx.author
            msg.channel = ctx.channel
            msg.content = "y"
            check(msg)
            return msg

        self.bot.wait_for.side_effect = fake_wait_for
        club = _club_with_admin("111")
        self.bot.api.find_club_in_channel.return_value = club
        self.bot.api.delete_club.return_value = {"success": True}
        await self.commands["club_delete"]["func"](ctx)
        self.bot.api.delete_club.assert_called_once()


class TestVersionCommand(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot, self.commands = _make_bot()

    async def test_version_success(self):
        ctx = _make_ctx()
        setup_content = 'setup(name="quill-bot", version="0.0.1")'
        with patch("builtins.open", mock_open(read_data=setup_content)):
            with patch("cogs.admin_commands.os.path.join", return_value="setup.py"):
                with patch("cogs.admin_commands.os.path.dirname", return_value="/mock"):
                    await self.commands["version"]["func"](ctx)
        ctx.send.assert_called_once()
        self.assertIn("embed", ctx.send.call_args.kwargs)

    async def test_version_not_found(self):
        ctx = _make_ctx()
        with patch("builtins.open", mock_open(read_data="setup(name='quill-bot')")):
            with patch("os.path.join", return_value="setup.py"):
                with patch("os.path.dirname", return_value="/mock"):
                    await self.commands["version"]["func"](ctx)
        ctx.send.assert_called_once()

    async def test_version_file_error(self):
        ctx = _make_ctx()
        with patch("builtins.open", side_effect=FileNotFoundError()):
            with patch("os.path.join", return_value="setup.py"):
                with patch("os.path.dirname", return_value="/mock"):
                    await self.commands["version"]["func"](ctx)
        ctx.send.assert_called_once()


class TestGuildOwnerCheck(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot, self.commands = _make_bot()

    async def test_server_register_denied_for_non_owner(self):
        ctx = _make_ctx(is_owner=False)
        await self.commands["server_register"]["func"](ctx)
        ctx.send.assert_called_once_with("❌ Only the server owner can use this command.")
        self.bot.api.register_server.assert_not_called()

    async def test_server_update_denied_for_non_owner(self):
        ctx = _make_ctx(is_owner=False)
        await self.commands["server_update"]["func"](ctx, name="New Name")
        ctx.send.assert_called_once_with("❌ Only the server owner can use this command.")

    async def test_server_delete_denied_for_non_owner(self):
        ctx = _make_ctx(is_owner=False)
        await self.commands["server_delete"]["func"](ctx)
        ctx.send.assert_called_once_with("❌ Only the server owner can use this command.")


class TestServerCommands(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot, self.commands = _make_bot()

    async def test_server_register_success(self):
        ctx = _make_ctx()
        self.bot.api.register_server.return_value = {"success": True}
        await self.commands["server_register"]["func"](ctx)
        self.bot.api.register_server.assert_called_once_with("888", "Test Server")
        ctx.send.assert_called_once()
        self.assertIn("embed", ctx.send.call_args.kwargs)

    async def test_server_register_api_error(self):
        ctx = _make_ctx()
        self.bot.api.register_server.side_effect = APIError("connection failed")
        await self.commands["server_register"]["func"](ctx)
        self.assertIn("❌", ctx.send.call_args.args[0])

    async def test_server_update_success(self):
        ctx = _make_ctx()
        self.bot.api.update_server.return_value = {"success": True}
        await self.commands["server_update"]["func"](ctx, name="Updated Name")
        self.bot.api.update_server.assert_called_once_with("888", "Updated Name")
        self.assertIn("embed", ctx.send.call_args.kwargs)

    async def test_server_delete_confirmed(self):
        ctx = _make_ctx()
        confirm_msg = MagicMock()
        confirm_msg.content = "y"
        self.bot.wait_for.return_value = confirm_msg
        self.bot.api.delete_server.return_value = {"success": True}
        await self.commands["server_delete"]["func"](ctx)
        self.bot.api.delete_server.assert_called_once_with("888")

    async def test_server_delete_cancelled(self):
        ctx = _make_ctx()
        confirm_msg = MagicMock()
        confirm_msg.content = "n"
        self.bot.wait_for.return_value = confirm_msg
        await self.commands["server_delete"]["func"](ctx)
        self.bot.api.delete_server.assert_not_called()

    async def test_server_delete_api_error(self):
        ctx = _make_ctx()
        confirm_msg = MagicMock()
        confirm_msg.content = "y"
        self.bot.wait_for.return_value = confirm_msg
        self.bot.api.delete_server.side_effect = APIError("failed to delete")
        await self.commands["server_delete"]["func"](ctx)
        self.assertIn("❌", ctx.send.call_args_list[-1].args[0])

    async def test_server_update_api_error(self):
        ctx = _make_ctx()
        self.bot.api.update_server.side_effect = APIError("update failed")
        await self.commands["server_update"]["func"](ctx, name="New Name")
        self.assertIn("❌", ctx.send.call_args.args[0])


class TestCanManageClubs(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot, self.commands = _make_bot()

    async def test_guild_owner_can_create_club_without_being_admin(self):
        """Guild owner should be able to create a club even if not a club admin."""
        ctx = _make_ctx(author_id="111", is_owner=True)
        self.bot.api.create_club.return_value = {"success": True}
        self.bot.api.get_member_by_discord_id.return_value = None
        self.bot.api.create_member.return_value = {"member": {"id": 1, "name": "Owner"}}
        await self.commands["club_create"]["func"](ctx, args="New Club")
        self.bot.api.create_club.assert_called_once()

    async def test_non_owner_denied_when_not_admin(self):
        ctx = _make_ctx(author_id="999", is_owner=False)
        # Club has a different member as admin
        self.bot.api.find_club_in_channel.return_value = {
            "id": "club-1",
            "name": "Test Club",
            "members": [{"discord_id": "111", "role": "admin"}],
        }
        await self.commands["club_create"]["func"](ctx, args="New Club")
        ctx.send.assert_called_once_with("❌ You need to be a club admin or owner to use this command.")

    async def test_club_create_denied_when_no_club(self):
        ctx = _make_ctx(author_id="111", is_owner=False)
        self.bot.api.find_club_in_channel.return_value = None
        await self.commands["club_create"]["func"](ctx, args="New Club")
        ctx.send.assert_called_once_with("❌ You need to be a club admin or owner to use this command.")

    async def test_club_create_denied_when_role_is_member(self):
        ctx = _make_ctx(author_id="111", is_owner=False)
        self.bot.api.find_club_in_channel.return_value = {
            "id": "club-1",
            "name": "Test Club",
            "members": [{"discord_id": "111", "role": "member"}],
        }
        await self.commands["club_create"]["func"](ctx, args="New Club")
        ctx.send.assert_called_once_with("❌ You need to be a club admin or owner to use this command.")

    async def test_club_update_allowed_for_owner(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = {
            "id": "club-1",
            "name": "Test Club",
            "members": [{"discord_id": "111", "role": "owner"}],
        }
        self.bot.api.update_club.return_value = {"success": True}
        await self.commands["club_update"]["func"](ctx, args="--name Updated")
        self.bot.api.update_club.assert_called_once()

    async def test_club_update_denied_when_no_members_in_club(self):
        ctx = _make_ctx(author_id="111", is_owner=False)
        self.bot.api.find_club_in_channel.return_value = {
            "id": "club-1",
            "name": "Test Club",
            "members": [],
        }
        await self.commands["club_update"]["func"](ctx, args="--name X")
        ctx.send.assert_called_once_with("❌ You need to be a club admin or owner to use this command.")


class TestClubCommands(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot, self.commands = _make_bot()
        self.club = _club_with_admin("111")

    async def test_club_create_success(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.get_member_by_discord_id.return_value = None
        self.bot.api.create_member.return_value = {"member": {"id": 1, "name": "Owner"}}
        self.bot.api.create_club.return_value = {"success": True}
        await self.commands["club_create"]["func"](ctx, args="Sci-Fi Club")
        call_payload = self.bot.api.create_club.call_args[0][0]
        self.assertEqual(call_payload["members"], [{"id": 1, "name": "Owner"}])
        self.assertIn("embed", ctx.send.call_args.kwargs)

    async def test_club_create_success_existing_member(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.get_member_by_discord_id.return_value = {"id": 99, "name": "Alice"}
        self.bot.api.create_club.return_value = {"success": True}
        await self.commands["club_create"]["func"](ctx, args="Sci-Fi Club")
        call_payload = self.bot.api.create_club.call_args[0][0]
        self.assertEqual(call_payload["members"], [{"id": 99, "name": "Alice"}])
        self.bot.api.create_member.assert_not_called()

    async def test_club_create_api_error(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.get_member_by_discord_id.return_value = {"id": 99, "name": "Alice"}
        self.bot.api.create_club.side_effect = APIError("server error")
        await self.commands["club_create"]["func"](ctx, args="Sci-Fi Club")
        self.assertIn("❌", ctx.send.call_args.args[0])

    async def test_club_update_name_success(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.update_club.return_value = {"success": True}
        await self.commands["club_update"]["func"](ctx, args="--name New Name")
        self.bot.api.update_club.assert_called_once_with("club-1", {"name": "New Name"}, "888")

    async def test_club_update_no_flags(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        await self.commands["club_update"]["func"](ctx, args="--invalid")
        self.assertIn("❌", ctx.send.call_args.args[0])
        self.bot.api.update_club.assert_not_called()

    async def test_club_update_no_club_in_channel(self):
        ctx = _make_ctx(author_id="111", is_owner=True)
        # Guild owner, but no club in channel
        self.bot.api.find_club_in_channel.return_value = None
        await self.commands["club_update"]["func"](ctx, args="--name X")
        ctx.send.assert_called_once_with("❌ No book club found in that channel.")

    async def test_club_delete_confirmed(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        confirm_msg = MagicMock()
        confirm_msg.content = "y"
        self.bot.wait_for.return_value = confirm_msg
        self.bot.api.delete_club.return_value = {"success": True}
        await self.commands["club_delete"]["func"](ctx)
        self.bot.api.delete_club.assert_called_once_with("club-1", "888")

    async def test_club_delete_cancelled(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        confirm_msg = MagicMock()
        confirm_msg.content = "n"
        self.bot.wait_for.return_value = confirm_msg
        await self.commands["club_delete"]["func"](ctx)
        self.bot.api.delete_club.assert_not_called()

    async def test_club_delete_no_club_in_channel(self):
        ctx = _make_ctx(author_id="111", is_owner=True)
        self.bot.api.find_club_in_channel.return_value = None
        await self.commands["club_delete"]["func"](ctx)
        ctx.send.assert_called_once_with("❌ No book club found in that channel.")

    async def test_club_create_api_error_on_create(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.get_member_by_discord_id.return_value = {"id": 99, "name": "Alice"}
        self.bot.api.create_club.side_effect = APIError("failed")
        await self.commands["club_create"]["func"](ctx, args="New Club")
        self.assertIn("❌", ctx.send.call_args.args[0])

    async def test_club_create_owner_assigned_existing_member(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.get_member_by_discord_id.return_value = {"id": 99, "name": "Alice"}
        self.bot.api.create_club.return_value = {"success": True}
        await self.commands["club_create"]["func"](ctx, args="Sci-Fi Club")
        call_payload = self.bot.api.create_club.call_args[0][0]
        self.assertEqual(call_payload["members"][0]["id"], 99)
        self.bot.api.update_member.assert_not_called()

    async def test_club_create_with_channel_flag(self):
        ctx = _make_ctx(author_id="111", is_owner=True)
        self.bot.api.get_member_by_discord_id.return_value = None
        self.bot.api.create_member.return_value = {"member": {"id": 1, "name": "Owner"}}
        self.bot.api.create_club.return_value = {"success": True}
        await self.commands["club_create"]["func"](ctx, args="Sci-Fi Club --channel 123456")
        call_args = self.bot.api.create_club.call_args[0][0]
        self.assertEqual(call_args["discord_channel"], "123456")

    async def test_club_update_both_flags(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.update_club.return_value = {"success": True}
        await self.commands["club_update"]["func"](ctx, args="--name NewName --new-channel 555")
        self.bot.api.update_club.assert_called_once()
        call_args = self.bot.api.update_club.call_args[0][1]
        self.assertIn("name", call_args)
        self.assertIn("discord_channel", call_args)

    async def test_club_update_with_channel_targeting(self):
        ctx = _make_ctx(author_id="111", is_owner=True)
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.update_club.return_value = {"success": True}
        await self.commands["club_update"]["func"](ctx, args="--name NewName --channel 123456")
        self.bot.api.find_club_in_channel.assert_called_with("123456", "888")

    async def test_club_update_api_error(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.update_club.side_effect = APIError("update failed")
        await self.commands["club_update"]["func"](ctx, args="--name X")
        self.assertIn("❌", ctx.send.call_args.args[0])

    async def test_club_delete_api_error(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        confirm_msg = MagicMock()
        confirm_msg.content = "y"
        self.bot.wait_for.return_value = confirm_msg
        self.bot.api.delete_club.side_effect = APIError("delete failed")
        await self.commands["club_delete"]["func"](ctx)
        self.assertIn("❌", ctx.send.call_args_list[-1].args[0])

    async def test_club_create_empty_name(self):
        ctx = _make_ctx(author_id="111")
        await self.commands["club_create"]["func"](ctx, args="--channel 999")
        ctx.send.assert_called_once_with(
            "❌ Provide a club name: `!club_create <name> [--channel <id>]`"
        )
        self.bot.api.create_club.assert_not_called()

    async def test_club_delete_no_permission(self):
        ctx = _make_ctx(author_id="999", is_owner=False)
        self.bot.api.find_club_in_channel.return_value = _club_with_admin("111")
        await self.commands["club_delete"]["func"](ctx)
        ctx.send.assert_called_once_with("❌ You need to be a club admin or owner to use this command.")
        self.bot.api.delete_club.assert_not_called()


class TestMemberCommands(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot, self.commands = _make_bot()
        self.club = _club_with_admin("111")

    async def test_member_add_new_member(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.get_member_by_discord_id.return_value = None
        self.bot.api.create_member.return_value = {"success": True}
        new_member = MagicMock()
        new_member.id = "222"
        new_member.display_name = "Alice"
        await self.commands["member_add"]["func"](ctx, new_member)
        self.bot.api.create_member.assert_called_once_with({
            "name": "Alice",
            "discord_id": "222",
            "clubs": ["club-1"],
        })

    async def test_member_add_existing_member_joins_new_club(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.get_member_by_discord_id.return_value = {
            "id": 99,
            "name": "Alice",
            "discord_id": "222",
            "clubs": [{"id": "other-club"}],
        }
        self.bot.api.update_member.return_value = {"success": True}
        new_member = MagicMock()
        new_member.id = "222"
        new_member.display_name = "Alice"
        await self.commands["member_add"]["func"](ctx, new_member)
        self.bot.api.create_member.assert_not_called()
        self.bot.api.update_member.assert_called_once_with(99, {"clubs": ["other-club", "club-1"]})

    async def test_member_add_already_in_club(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.get_member_by_discord_id.return_value = {
            "id": 99,
            "name": "Alice",
            "discord_id": "222",
            "clubs": [{"id": "club-1"}],
        }
        new_member = MagicMock()
        new_member.id = "222"
        new_member.display_name = "Alice"
        await self.commands["member_add"]["func"](ctx, new_member)
        self.bot.api.create_member.assert_not_called()
        self.bot.api.update_member.assert_not_called()
        self.assertIn("already a member", ctx.send.call_args.args[0])

    async def test_member_add_api_error(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.get_member_by_discord_id.return_value = None
        self.bot.api.create_member.side_effect = APIError("failed")
        new_member = MagicMock()
        new_member.id = "222"
        new_member.display_name = "Alice"
        await self.commands["member_add"]["func"](ctx, new_member)
        self.assertIn("❌", ctx.send.call_args.args[0])

    async def test_member_remove_confirmed(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        confirm_msg = MagicMock()
        confirm_msg.content = "y"
        self.bot.wait_for.return_value = confirm_msg
        self.bot.api.delete_member.return_value = {"success": True}
        await self.commands["member_remove"]["func"](ctx, 42)
        self.bot.api.delete_member.assert_called_once_with(42)

    async def test_member_remove_cancelled(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        confirm_msg = MagicMock()
        confirm_msg.content = "no"
        self.bot.wait_for.return_value = confirm_msg
        await self.commands["member_remove"]["func"](ctx, 42)
        self.bot.api.delete_member.assert_not_called()

    async def test_member_role_admin_success(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.update_member.return_value = {"success": True}
        await self.commands["member_role"]["func"](ctx, 42, "admin")
        self.bot.api.update_member.assert_called_once_with(42, {"club_roles": {"club-1": "admin"}})

    async def test_member_role_invalid_role(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        await self.commands["member_role"]["func"](ctx, 42, "superadmin")
        ctx.send.assert_called_with("❌ Role must be `admin` or `member`.")
        self.bot.api.update_member.assert_not_called()

    async def test_member_add_no_club_in_channel(self):
        ctx = _make_ctx(author_id="111", is_owner=True)
        self.bot.api.find_club_in_channel.return_value = None
        new_member = MagicMock()
        new_member.id = "222"
        new_member.display_name = "Alice"
        await self.commands["member_add"]["func"](ctx, new_member)
        ctx.send.assert_called_once_with("❌ No book club found in that channel.")

    async def test_member_role_no_club_in_channel(self):
        ctx = _make_ctx(author_id="111", is_owner=True)
        self.bot.api.find_club_in_channel.return_value = None
        await self.commands["member_role"]["func"](ctx, 42, "admin")
        ctx.send.assert_called_once_with("❌ No book club found in that channel.")

    async def test_member_role_api_error(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.update_member.side_effect = APIError("update failed")
        await self.commands["member_role"]["func"](ctx, 42, "admin")
        self.assertIn("❌", ctx.send.call_args.args[0])

    async def test_member_remove_api_error(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        confirm_msg = MagicMock()
        confirm_msg.content = "y"
        self.bot.wait_for.return_value = confirm_msg
        self.bot.api.delete_member.side_effect = APIError("delete failed")
        await self.commands["member_remove"]["func"](ctx, 42)
        self.assertIn("❌", ctx.send.call_args_list[-1].args[0])

    async def test_member_add_no_permission(self):
        ctx = _make_ctx(author_id="999", is_owner=False)
        self.bot.api.find_club_in_channel.return_value = _club_with_admin("111")
        new_member = MagicMock()
        new_member.id = "999"
        new_member.display_name = "Intruder"
        await self.commands["member_add"]["func"](ctx, new_member)
        ctx.send.assert_called_once_with("❌ You need to be a club admin or owner to use this command.")
        self.bot.api.create_member.assert_not_called()

    async def test_member_remove_no_permission(self):
        ctx = _make_ctx(author_id="999", is_owner=False)
        self.bot.api.find_club_in_channel.return_value = _club_with_admin("111")
        await self.commands["member_remove"]["func"](ctx, 42)
        ctx.send.assert_called_once_with("❌ You need to be a club admin or owner to use this command.")
        self.bot.api.delete_member.assert_not_called()

    async def test_member_role_no_permission(self):
        ctx = _make_ctx(author_id="999", is_owner=False)
        self.bot.api.find_club_in_channel.return_value = _club_with_admin("111")
        await self.commands["member_role"]["func"](ctx, 42, "admin")
        ctx.send.assert_called_once_with("❌ You need to be a club admin or owner to use this command.")
        self.bot.api.update_member.assert_not_called()


class TestSessionCommands(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot, self.commands = _make_bot()
        self.club = _club_with_admin("111")

    async def test_session_create_success(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.create_session.return_value = {"success": True}
        await self.commands["session_create"]["func"](ctx, "Dune", author="Frank Herbert")
        self.bot.api.create_session.assert_called_once_with({
            "club_id": "club-1",
            "book": {"title": "Dune", "author": "Frank Herbert"},
        })

    async def test_session_create_api_error(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.create_session.side_effect = APIError("failed")
        await self.commands["session_create"]["func"](ctx, "Dune", author="Frank Herbert")
        self.assertIn("❌", ctx.send.call_args.args[0])

    async def test_session_update_due_date(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.update_session.return_value = {"success": True}
        await self.commands["session_update"]["func"](ctx, args="--due-date 2026-06-01")
        self.bot.api.update_session.assert_called_once_with("sess-1", {"due_date": "2026-06-01"})

    async def test_session_update_book(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.update_session.return_value = {"success": True}
        await self.commands["session_update"]["func"](ctx, args='--book "Foundation|Isaac Asimov"')
        self.bot.api.update_session.assert_called_once_with(
            "sess-1", {"book": {"title": "Foundation", "author": "Isaac Asimov"}}
        )

    async def test_session_update_no_flags(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        await self.commands["session_update"]["func"](ctx, args="--invalid")
        self.assertIn("❌", ctx.send.call_args.args[0])
        self.bot.api.update_session.assert_not_called()

    async def test_session_update_no_active_session(self):
        ctx = _make_ctx(author_id="111")
        club_no_session = {**self.club, "active_session": None}
        self.bot.api.find_club_in_channel.return_value = club_no_session
        await self.commands["session_update"]["func"](ctx, args="--due-date 2026-06-01")
        ctx.send.assert_called_with("❌ No active session found in that channel.")

    async def test_session_delete_confirmed(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        confirm_msg = MagicMock()
        confirm_msg.content = "y"
        self.bot.wait_for.return_value = confirm_msg
        self.bot.api.delete_session.return_value = {"success": True}
        await self.commands["session_delete"]["func"](ctx)
        self.bot.api.delete_session.assert_called_once_with("sess-1")

    async def test_session_delete_cancelled(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        confirm_msg = MagicMock()
        confirm_msg.content = "n"
        self.bot.wait_for.return_value = confirm_msg
        await self.commands["session_delete"]["func"](ctx)
        self.bot.api.delete_session.assert_not_called()

    async def test_session_create_no_club_in_channel(self):
        ctx = _make_ctx(author_id="111", is_owner=True)
        self.bot.api.find_club_in_channel.return_value = None
        await self.commands["session_create"]["func"](ctx, "Dune", author="Frank Herbert")
        ctx.send.assert_called_once_with("❌ No book club found in that channel.")

    async def test_session_delete_no_club_in_channel(self):
        ctx = _make_ctx(author_id="111", is_owner=True)
        self.bot.api.find_club_in_channel.return_value = None
        await self.commands["session_delete"]["func"](ctx)
        ctx.send.assert_called_once_with("❌ No active session found in that channel.")

    async def test_session_update_both_flags(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.update_session.return_value = {"success": True}
        await self.commands["session_update"]["func"](ctx, args='--due-date 2026-06-01 --book "New Book|New Author"')
        self.bot.api.update_session.assert_called_once()
        call_args = self.bot.api.update_session.call_args[0][1]
        self.assertIn("due_date", call_args)
        self.assertIn("book", call_args)

    async def test_session_update_api_error(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        self.bot.api.update_session.side_effect = APIError("update failed")
        await self.commands["session_update"]["func"](ctx, args="--due-date 2026-06-01")
        self.assertIn("❌", ctx.send.call_args.args[0])

    async def test_session_delete_api_error(self):
        ctx = _make_ctx(author_id="111")
        self.bot.api.find_club_in_channel.return_value = self.club
        confirm_msg = MagicMock()
        confirm_msg.content = "y"
        self.bot.wait_for.return_value = confirm_msg
        self.bot.api.delete_session.side_effect = APIError("delete failed")
        await self.commands["session_delete"]["func"](ctx)
        self.assertIn("❌", ctx.send.call_args_list[-1].args[0])

    async def test_session_create_no_permission(self):
        ctx = _make_ctx(author_id="999", is_owner=False)
        self.bot.api.find_club_in_channel.return_value = _club_with_admin("111")
        await self.commands["session_create"]["func"](ctx, "Dune", author="Frank Herbert")
        ctx.send.assert_called_once_with("❌ You need to be a club admin or owner to use this command.")
        self.bot.api.create_session.assert_not_called()

    async def test_session_update_no_permission(self):
        ctx = _make_ctx(author_id="999", is_owner=False)
        self.bot.api.find_club_in_channel.return_value = _club_with_admin("111")
        await self.commands["session_update"]["func"](ctx, args="--due-date 2026-06-01")
        ctx.send.assert_called_once_with("❌ You need to be a club admin or owner to use this command.")
        self.bot.api.update_session.assert_not_called()

    async def test_session_delete_no_permission(self):
        ctx = _make_ctx(author_id="999", is_owner=False)
        self.bot.api.find_club_in_channel.return_value = _club_with_admin("111")
        await self.commands["session_delete"]["func"](ctx)
        ctx.send.assert_called_once_with("❌ You need to be a club admin or owner to use this command.")
        self.bot.api.delete_session.assert_not_called()


class TestAdminHelpCommand(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot, self.commands = _make_bot()

    async def test_help_denied_for_non_admin(self):
        ctx = _make_ctx(is_owner=False, author_id="999")
        self.bot.api.find_club_in_channel.return_value = None
        await self.commands["admin_help"]["func"](ctx)
        ctx.send.assert_called_once_with("❌ You need to be a guild owner or club admin to use this command.")
        args = ctx.send.call_args.args[0]
        self.assertNotIn("embed", ctx.send.call_args.kwargs)

    async def test_help_allowed_for_guild_owner(self):
        ctx = _make_ctx(is_owner=True)
        await self.commands["admin_help"]["func"](ctx)
        ctx.send.assert_called_once()
        self.assertIn("embed", ctx.send.call_args.kwargs)
        embed = ctx.send.call_args.kwargs["embed"]
        self.assertIn("Admin Commands", embed.title)

    async def test_help_allowed_for_club_admin(self):
        ctx = _make_ctx(is_owner=False, author_id="111")
        club = _club_with_admin("111")
        self.bot.api.find_club_in_channel.return_value = club
        await self.commands["admin_help"]["func"](ctx)
        ctx.send.assert_called_once()
        self.assertIn("embed", ctx.send.call_args.kwargs)
        embed = ctx.send.call_args.kwargs["embed"]
        self.assertIn("Admin Commands", embed.title)


class TestSetupCommand(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot, self.commands = _make_bot()

    def _club_name_msg(self, ctx, name="My Book Club"):
        msg = MagicMock()
        msg.author = ctx.author
        msg.channel = ctx.channel
        msg.content = name
        return msg

    async def test_setup_denied_for_non_owner(self):
        ctx = _make_ctx(is_owner=False)
        await self.commands["setup"]["func"](ctx)
        ctx.send.assert_called_once_with("❌ Only the server owner can run `!setup`.")
        self.bot.api.register_server.assert_not_called()

    async def test_setup_happy_path_new_member(self):
        ctx = _make_ctx()
        self.bot.api.register_server.return_value = {"success": True}
        self.bot.api.get_member_by_discord_id.return_value = None
        self.bot.api.create_member.return_value = {"member": {"id": "m-1", "name": "Owner"}}
        self.bot.api.create_club.return_value = {"id": "c-1"}
        self.bot.wait_for.return_value = self._club_name_msg(ctx)

        await self.commands["setup"]["func"](ctx)

        self.bot.api.register_server.assert_called_once_with("888", "Test Server")
        self.bot.api.create_club.assert_called_once()
        call_args = self.bot.api.create_club.call_args[0][0]
        self.assertEqual(call_args["name"], "My Book Club")
        self.assertEqual(call_args["discord_channel"], "999")
        # Confirmation embed sent as last message
        last_call = ctx.send.call_args
        self.assertIn("embed", last_call.kwargs)

    async def test_setup_happy_path_existing_member(self):
        ctx = _make_ctx()
        self.bot.api.register_server.return_value = {"success": True}
        self.bot.api.get_member_by_discord_id.return_value = {"id": "m-42", "name": "Existing"}
        self.bot.api.create_club.return_value = {"id": "c-2"}
        self.bot.wait_for.return_value = self._club_name_msg(ctx, "Readers Circle")

        await self.commands["setup"]["func"](ctx)

        self.bot.api.create_member.assert_not_called()
        call_args = self.bot.api.create_club.call_args[0][0]
        self.assertEqual(call_args["name"], "Readers Circle")
        self.assertEqual(call_args["members"], [{"id": "m-42", "name": "Existing"}])

    async def test_setup_already_registered_server_continues(self):
        ctx = _make_ctx()
        self.bot.api.register_server.side_effect = APIError("already registered")
        self.bot.api.get_member_by_discord_id.return_value = {"id": "m-1", "name": "Owner"}
        self.bot.api.create_club.return_value = {"id": "c-3"}
        self.bot.wait_for.return_value = self._club_name_msg(ctx)

        await self.commands["setup"]["func"](ctx)

        # Should inform user and continue to club creation
        messages = [call.args[0] if call.args else "" for call in ctx.send.call_args_list]
        self.assertTrue(any("already registered" in m for m in messages))
        self.bot.api.create_club.assert_called_once()

    async def test_setup_register_server_api_error_stops(self):
        ctx = _make_ctx()
        self.bot.api.register_server.side_effect = APIError("connection failed")

        await self.commands["setup"]["func"](ctx)

        self.bot.api.create_club.assert_not_called()
        last_msg = ctx.send.call_args.args[0]
        self.assertIn("❌", last_msg)

    async def test_setup_timeout_waiting_for_club_name(self):
        ctx = _make_ctx()
        self.bot.api.register_server.return_value = {"success": True}
        self.bot.wait_for.side_effect = TimeoutError()

        await self.commands["setup"]["func"](ctx)

        self.bot.api.create_club.assert_not_called()
        last_msg = ctx.send.call_args.args[0]
        self.assertIn("⏰", last_msg)

    async def test_setup_create_club_api_error(self):
        ctx = _make_ctx()
        self.bot.api.register_server.return_value = {"success": True}
        self.bot.api.get_member_by_discord_id.return_value = {"id": "m-1", "name": "Owner"}
        self.bot.api.create_club.side_effect = APIError("club creation failed")
        self.bot.wait_for.return_value = self._club_name_msg(ctx)

        await self.commands["setup"]["func"](ctx)

        last_msg = ctx.send.call_args.args[0]
        self.assertIn("❌", last_msg)


if __name__ == "__main__":
    unittest.main()
