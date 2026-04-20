"""
Admin commands (version, server, club, member, session management)
"""
import re
import os
import discord
from discord.ext import commands

from utils.embeds import create_embed
from api.bookclub_api import APIError


def setup_admin_commands(bot):
    """
    Setup admin (prefix) commands

    Args:
        bot: The bot instance
    """

    def _check_guild_owner(ctx):
        """Returns True if the command author is the Discord guild owner."""
        return ctx.author == ctx.guild.owner

    async def _can_manage_clubs(ctx, channel_id: str = None):
        """Returns True if user is guild owner OR club admin in the target channel's club."""
        if _check_guild_owner(ctx):
            return True
        target = channel_id or str(ctx.channel.id)
        club_data = bot.api.find_club_in_channel(target, str(ctx.guild.id))
        if not club_data:
            return False
        for member in club_data.get("members", []):
            if str(member.get("discord_id")) == str(ctx.author.id):
                return member.get("role") in ("admin", "owner")
        return False

    def _resolve_channel_id(ctx, args: str = ""):
        """Extracts --channel <id> from args, falling back to the current channel."""
        match = re.search(r'--channel\s+(\d+)', args)
        return match.group(1) if match else str(ctx.channel.id)

    async def _confirm(ctx, prompt):
        """Sends a y/n prompt; returns True only if the user replies 'y' within 30 seconds."""
        await ctx.send(prompt)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", timeout=30.0, check=check)
            return msg.content.strip().lower() == "y"
        except TimeoutError:
            await ctx.send("⏰ Confirmation timed out. Action cancelled.")
            return False

    # ── Version ──────────────────────────────────────────────────────────────

    @bot.command(name="version", help="Shows the current version of the bot")
    async def version(ctx: commands.Context):
        """
        Extracts and displays the current version from setup.py
        Usage: !version
        """
        try:
            setup_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "setup.py")
            with open(setup_path, "r") as file:
                setup_content = file.read()

            version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', setup_content)
            if version_match:
                v = version_match.group(1)
                embed = create_embed(
                    title=f"📚 Quill Bot version: v{v}",
                    color_key="blank",
                    timestamp=True
                )
                await ctx.send(embed=embed)
            else:
                embed = create_embed(
                    title="❌ Error",
                    description="Couldn't find version information in setup.py",
                    color_key="error"
                )
                await ctx.send(embed=embed)
        except Exception as e:
            embed = create_embed(
                title="❌ Error",
                description=f"Error retrieving version: {str(e)}",
                color_key="error"
            )
            await ctx.send(embed=embed)

    # ── Server commands (guild owner only) ───────────────────────────────────

    @bot.command(name="server_register", help="Register this Discord server with the bot")
    async def server_register(ctx: commands.Context):
        """
        Registers the Discord server.
        Usage: !server_register
        """
        if not _check_guild_owner(ctx):
            await ctx.send("❌ Only the server owner can use this command.")
            return
        try:
            bot.api.register_server(str(ctx.guild.id), ctx.guild.name)
            embed = create_embed(
                title="✅ Server Registered",
                description=f"**{ctx.guild.name}** has been registered.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to register server: {e}")

    @bot.command(name="server_update", help="Update this server's registered name")
    async def server_update(ctx: commands.Context, *, name: str):
        """
        Updates the server's registered name.
        Usage: !server_update <name>
        """
        if not _check_guild_owner(ctx):
            await ctx.send("❌ Only the server owner can use this command.")
            return
        try:
            bot.api.update_server(str(ctx.guild.id), name)
            embed = create_embed(
                title="✅ Server Updated",
                description=f"Server name updated to **{name}**.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to update server: {e}")

    @bot.command(name="server_delete", help="Delete this server's registration")
    async def server_delete(ctx: commands.Context):
        """
        Deletes the server registration and all associated data.
        Usage: !server_delete
        """
        if not _check_guild_owner(ctx):
            await ctx.send("❌ Only the server owner can use this command.")
            return
        confirmed = await _confirm(
            ctx,
            "⚠️ This will delete **all server data** including clubs, members, and sessions. "
            "Type `y` to confirm or anything else to cancel."
        )
        if not confirmed:
            await ctx.send("Action cancelled.")
            return
        try:
            bot.api.delete_server(str(ctx.guild.id))
            embed = create_embed(
                title="✅ Server Deleted",
                description="Server registration and all associated data have been removed.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to delete server: {e}")

    # ── Club commands (club admin+) ───────────────────────────────────────────

    @bot.command(name="club_create", help="Create a new book club in a channel")
    async def club_create(ctx: commands.Context, *, args: str):
        """
        Creates a new book club. Caller is automatically assigned as owner.
        Usage: !club_create <name> [--channel <channel_id>]
        """
        channel_id = _resolve_channel_id(ctx, args)
        name = re.sub(r'\s*--channel\s+\d+', '', args).strip()

        if not name:
            await ctx.send("❌ Provide a club name: `!club_create <name> [--channel <id>]`")
            return
        if not await _can_manage_clubs(ctx, channel_id):
            await ctx.send("❌ You need to be a club admin or owner to use this command.")
            return
        try:
            # Resolve or create the caller's member record so we can pass
            # them as the first member in the club payload — the backend
            # promotes index-0 to owner automatically.
            existing = bot.api.get_member_by_discord_id(str(ctx.author.id))
            if existing:
                caller = {"id": existing["id"], "name": existing["name"]}
            else:
                created = bot.api.create_member({
                    "name": ctx.author.display_name,
                    "discord_id": str(ctx.author.id),
                })
                member_data = created.get("member", created)
                caller = {"id": member_data["id"], "name": member_data["name"]}

            bot.api.create_club(
                {"name": name, "discord_channel": channel_id, "members": [caller]},
                str(ctx.guild.id)
            )
            embed = create_embed(
                title="✅ Club Created",
                description=f"Book club **{name}** created in <#{channel_id}>. You are the owner.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to create club: {e}")

    @bot.command(name="club_update", help="Update the club name or discord channel")
    async def club_update(ctx: commands.Context, *, args: str):
        """
        Updates club details. Use --channel to target a club from another channel.
        Usage: !club_update [--name <name>] [--new-channel <channel_id>] [--channel <channel_id>]
        """
        channel_id = _resolve_channel_id(ctx, args)
        if not await _can_manage_clubs(ctx, channel_id):
            await ctx.send("❌ You need to be a club admin or owner to use this command.")
            return
        guild_id = str(ctx.guild.id)
        club_data = bot.api.find_club_in_channel(channel_id, guild_id)
        if not club_data:
            await ctx.send("❌ No book club found in that channel.")
            return
        update = {}
        name_match = re.search(r'--name\s+(.+?)(?:\s+--|$)', args)
        new_channel_match = re.search(r'--new-channel\s+(\d+)', args)
        if name_match:
            update["name"] = name_match.group(1).strip()
        if new_channel_match:
            update["discord_channel"] = new_channel_match.group(1).strip()
        if not update:
            await ctx.send(
                "❌ Provide at least `--name <name>` or `--new-channel <channel_id>`."
            )
            return
        try:
            bot.api.update_club(club_data["id"], update, guild_id)
            embed = create_embed(
                title="✅ Club Updated",
                description="Club details updated successfully.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to update club: {e}")

    @bot.command(name="club_delete", help="Delete the book club in a channel")
    async def club_delete(ctx: commands.Context, *, args: str = ""):
        """
        Deletes a book club and all its data.
        Usage: !club_delete [--channel <channel_id>]
        """
        channel_id = _resolve_channel_id(ctx, args)
        if not await _can_manage_clubs(ctx, channel_id):
            await ctx.send("❌ You need to be a club admin or owner to use this command.")
            return
        guild_id = str(ctx.guild.id)
        club_data = bot.api.find_club_in_channel(channel_id, guild_id)
        if not club_data:
            await ctx.send("❌ No book club found in that channel.")
            return
        confirmed = await _confirm(
            ctx,
            f"⚠️ This will delete **{club_data['name']}** and all its data. "
            "Type `y` to confirm or anything else to cancel."
        )
        if not confirmed:
            await ctx.send("Action cancelled.")
            return
        try:
            bot.api.delete_club(club_data["id"], guild_id)
            embed = create_embed(
                title="✅ Club Deleted",
                description=f"**{club_data['name']}** has been deleted.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to delete club: {e}")

    # ── Member commands (club admin+) ─────────────────────────────────────────

    @bot.command(name="member_add", help="Add a Discord user to a book club")
    async def member_add(ctx: commands.Context, member: discord.Member, *, args: str = ""):
        """
        Adds a mentioned Discord user to a club. Creates member record if needed.
        Usage: !member_add @User [--channel <channel_id>]
        """
        channel_id = _resolve_channel_id(ctx, args)
        if not await _can_manage_clubs(ctx, channel_id):
            await ctx.send("❌ You need to be a club admin or owner to use this command.")
            return
        club_data = bot.api.find_club_in_channel(channel_id, str(ctx.guild.id))
        if not club_data:
            await ctx.send("❌ No book club found in that channel.")
            return
        try:
            existing = bot.api.get_member_by_discord_id(str(member.id))
            if existing:
                current_club_ids = [c["id"] for c in existing.get("clubs", [])]
                if club_data["id"] in current_club_ids:
                    await ctx.send(f"**{member.display_name}** is already a member of this club.")
                    return
                bot.api.update_member(existing["id"], {"clubs": current_club_ids + [club_data["id"]]})
            else:
                bot.api.create_member({
                    "name": member.display_name,
                    "discord_id": str(member.id),
                    "clubs": [club_data["id"]]
                })
            embed = create_embed(
                title="✅ Member Added",
                description=f"**{member.display_name}** has been added to the club.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to add member: {e}")

    @bot.command(name="member_remove", help="Remove a member from a book club")
    async def member_remove(ctx: commands.Context, member_id: int, *, args: str = ""):
        """
        Removes a member by their ID.
        Usage: !member_remove <member_id> [--channel <channel_id>]
        """
        channel_id = _resolve_channel_id(ctx, args)
        if not await _can_manage_clubs(ctx, channel_id):
            await ctx.send("❌ You need to be a club admin or owner to use this command.")
            return
        confirmed = await _confirm(
            ctx,
            f"⚠️ Remove member `{member_id}` from the club? "
            "Type `y` to confirm or anything else to cancel."
        )
        if not confirmed:
            await ctx.send("Action cancelled.")
            return
        try:
            bot.api.delete_member(member_id)
            embed = create_embed(
                title="✅ Member Removed",
                description=f"Member `{member_id}` has been removed.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to remove member: {e}")

    @bot.command(name="member_role", help="Update a member's role in a club")
    async def member_role(ctx: commands.Context, member_id: int, role: str, *, args: str = ""):
        """
        Sets a member's role to admin or member.
        Usage: !member_role <member_id> <admin|member> [--channel <channel_id>]
        """
        channel_id = _resolve_channel_id(ctx, args)
        if not await _can_manage_clubs(ctx, channel_id):
            await ctx.send("❌ You need to be a club admin or owner to use this command.")
            return
        if role not in ("admin", "member"):
            await ctx.send("❌ Role must be `admin` or `member`.")
            return
        guild_id = str(ctx.guild.id)
        club_data = bot.api.find_club_in_channel(channel_id, guild_id)
        if not club_data:
            await ctx.send("❌ No book club found in that channel.")
            return
        try:
            bot.api.update_member(member_id, {"club_roles": {club_data["id"]: role}})
            embed = create_embed(
                title="✅ Role Updated",
                description=f"Member `{member_id}` is now **{role}**.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to update role: {e}")

    # ── Session commands (club admin+) ────────────────────────────────────────

    @bot.command(name="session_create", help="Create a new reading session")
    async def session_create(ctx: commands.Context, book_title: str, *, author: str):
        """
        Creates a reading session for a club.
        Usage: !session_create "<book title>" <author> [--channel <channel_id>]
        """
        channel_id = _resolve_channel_id(ctx, author)
        author = re.sub(r'\s*--channel\s+\d+', '', author).strip()

        if not await _can_manage_clubs(ctx, channel_id):
            await ctx.send("❌ You need to be a club admin or owner to use this command.")
            return
        club_data = bot.api.find_club_in_channel(channel_id, str(ctx.guild.id))
        if not club_data:
            await ctx.send("❌ No book club found in that channel.")
            return
        try:
            bot.api.create_session({
                "club_id": club_data["id"],
                "book": {"title": book_title, "author": author}
            })
            embed = create_embed(
                title="✅ Session Created",
                description=f"Now reading **{book_title}** by {author}.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to create session: {e}")

    @bot.command(name="session_update", help="Update the active reading session")
    async def session_update(ctx: commands.Context, *, args: str):
        """
        Updates the active session. Provide at least one flag.
        Usage: !session_update [--due-date YYYY-MM-DD] [--book "<title>|<author>"] [--channel <channel_id>]
        """
        channel_id = _resolve_channel_id(ctx, args)
        if not await _can_manage_clubs(ctx, channel_id):
            await ctx.send("❌ You need to be a club admin or owner to use this command.")
            return
        guild_id = str(ctx.guild.id)
        club_data = bot.api.find_club_in_channel(channel_id, guild_id)
        if not club_data or not club_data.get("active_session"):
            await ctx.send("❌ No active session found in that channel.")
            return
        session_id = club_data["active_session"]["id"]
        update = {}
        due_date_match = re.search(r'--due-date\s+(\S+)', args)
        book_match = re.search(r'--book\s+"([^|"]+)\|([^"]+)"', args)
        if due_date_match:
            update["due_date"] = due_date_match.group(1)
        if book_match:
            update["book"] = {
                "title": book_match.group(1).strip(),
                "author": book_match.group(2).strip()
            }
        if not update:
            await ctx.send(
                "❌ Provide at least `--due-date YYYY-MM-DD` or `--book \"<title>|<author>\"`."
            )
            return
        try:
            bot.api.update_session(session_id, update)
            embed = create_embed(
                title="✅ Session Updated",
                description="Session details updated successfully.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to update session: {e}")

    @bot.command(name="session_delete", help="Delete the active reading session")
    async def session_delete(ctx: commands.Context, *, args: str = ""):
        """
        Deletes the active session for a club.
        Usage: !session_delete [--channel <channel_id>]
        """
        channel_id = _resolve_channel_id(ctx, args)
        if not await _can_manage_clubs(ctx, channel_id):
            await ctx.send("❌ You need to be a club admin or owner to use this command.")
            return
        guild_id = str(ctx.guild.id)
        club_data = bot.api.find_club_in_channel(channel_id, guild_id)
        if not club_data or not club_data.get("active_session"):
            await ctx.send("❌ No active session found in that channel.")
            return
        session_id = club_data["active_session"]["id"]
        confirmed = await _confirm(
            ctx,
            "⚠️ This will permanently delete the active reading session. "
            "Type `y` to confirm or anything else to cancel."
        )
        if not confirmed:
            await ctx.send("Action cancelled.")
            return
        try:
            bot.api.delete_session(session_id)
            embed = create_embed(
                title="✅ Session Deleted",
                description="The active reading session has been deleted.",
                color_key="success"
            )
            await ctx.send(embed=embed)
        except APIError as e:
            await ctx.send(f"❌ Failed to delete session: {e}")
