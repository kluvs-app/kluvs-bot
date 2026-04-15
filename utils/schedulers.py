"""
Task scheduling utilities
"""
import random
from datetime import datetime
import pytz
from discord.ext import tasks

from utils.constants import READING_REMINDERS, SCHEDULED_MESSAGE_HOUR, SCHEDULED_MESSAGE_PERCENTAGE
from utils.embeds import create_embed

def setup_scheduled_tasks(bot):
    """Setup all scheduled tasks for the bot"""
    
    @tasks.loop(hours=1)
    async def send_reminder_message():
        """Send daily reading reminders."""
        sf_timezone = pytz.timezone('US/Pacific')
        now_pacific = datetime.now(tz=sf_timezone)
        
        # if it is 5PM Pacific time, send a reminder with a given percentage chance
        if now_pacific.hour == SCHEDULED_MESSAGE_HOUR and random.random() < SCHEDULED_MESSAGE_PERCENTAGE:
            for guild in bot.guilds:
                try:
                    clubs = bot.api.get_server_clubs(str(guild.id))
                    for club in clubs:
                        discord_channel_id = club.get('discord_channel')
                        if not discord_channel_id:
                            continue
                        channel = bot.get_channel(int(discord_channel_id))
                        if channel:
                            embed = create_embed(
                                title="📚 Daily Reading Reminder",
                                description=random.choice(READING_REMINDERS),
                                color_key="purp"
                            )
                            await channel.send(embed=embed)
                            print(f"Reminder message sent to guild {guild.id}, club {club.get('id')}.")
                except Exception as e:
                    print(f"[ERROR] Failed to send reminder for guild {guild.id}: {e}")
    
    # Start the scheduled tasks
    send_reminder_message.start()
    
    # Return the task so it can be stopped if needed
    return send_reminder_message