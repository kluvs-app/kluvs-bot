"""
General commands (help, usage)
"""
import discord
from discord import app_commands

from utils.embeds import create_embed

def setup_general_commands(bot):
    """
    Setup general commands for the bot
    
    Args:
        bot: The bot instance
    """
    @bot.tree.command(name="help", description="Show help prompt")
    async def help_command(interaction: discord.Interaction):
        embed = create_embed(
            title="🦉 Quill's Orientation",
            description="Welcome to Kluvs! I'm here to help you with all things about our book club.",
            color_key="info"
        )

        embed.add_field(
            name="👤 New to this server?",
            value="Start with `/join` to join the book club, then check `/session` to see the current book.\n\nUse `/usage` for all available commands.",
            inline=False
        )

        embed.add_field(
            name="👑 Server owner?",
            value="Run `!setup` to initialize your server and create a book club.",
            inline=False
        )

        embed.set_footer(text=f"Happy reading! 📚")
        await interaction.response.send_message(embed=embed)
        print("Sent help command response.")
    
    @bot.tree.command(name="usage", description="Show all available commands")
    async def usage_command(interaction: discord.Interaction):
        embed = create_embed(
            title="📚 Quill's Commands",
            description="Here are all the commands available to you.",
            color_key="info"
        )

        embed.add_field(
            name="📖 Reading Commands",
            value="• `/session` - Show all session details\n"
                  "• `/book` - Show current book details\n"
                  "• `/duedate` - Show the session's due date\n"
                  "• `/discussions` - Show the session's discussion details\n"
                  "• `/book_summary` - AI-generated book summary",
            inline=False
        )

        embed.add_field(
            name="👥 Member Commands",
            value="• `/join` - Join the book club in the current channel\n"
                  "• `/leave` - Leave the book club in the current channel",
            inline=False
        )

        embed.add_field(
            name="⚙️ Admin Commands",
            value="Admins and server owners: type `!admin_help` for admin commands.",
            inline=False
        )

        embed.set_footer(text=f"Use / for slash commands, ! for admin commands")
        await interaction.response.send_message(embed=embed)
        print("Sent usage command response.")
