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
            description="Greetings human!  I'm here to help you with all things about our book club.",
            color_key="info"
        )

        embed.add_field(
            name=" How to use ❓",
            value="You can execute `/usage` to see all available commands.\n\nHere's a few more commands to get you started.",
            inline=False
        )

        embed.add_field(
            name="📖 Reading Commands",
            value="• `/session` - Show all session details\n"
                  "• `/book` - Show current book details\n"
                  "• `/duedate` - Show the session's due date\n"
                  "• `/discussions` - Show the session's discussion details",
            inline=False
        )

        embed.set_footer(text=f"Hope this helps! ✌️")
        await interaction.response.send_message(embed=embed)
        print("Sent help command response.")
    
    @bot.tree.command(name="usage", description="Show all available commands")
    async def usage_command(interaction: discord.Interaction):
        embed = create_embed(
            title="📚 Quill's Commands",
            description="Here's everything I can help you with!",
            color_key="info"
        )
        
        embed.add_field(
            name="📖 Reading Commands",
            value="• `/session` - Show all session details\n"
                  "• `/book` - Show current book details\n"
                  "• `/duedate` - Show the session's due date\n"
                  "• `/discussions` - Show the session's discussion details",
            inline=False
        )

        embed.set_footer(text=f"*Use / to access all commands!*")
        await interaction.response.send_message(embed=embed)
        print("Sent usage command response.")