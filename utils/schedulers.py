"""
Task scheduling utilities
"""
from discord.ext import tasks

# TODO: Re-enable imports once clubs/servers have notification/reminder settings.
# import random
# from datetime import datetime
# import pytz
# from utils.constants import READING_REMINDERS, SCHEDULED_MESSAGE_HOUR, SCHEDULED_MESSAGE_PERCENTAGE
# from utils.embeds import create_embed

def setup_scheduled_tasks(bot):
    """Setup all scheduled tasks for the bot"""

    @tasks.loop(hours=1)
    async def send_reminder_message():
        """Send daily reading reminders."""
        # TODO: Re-enable once clubs/servers have notification/reminder settings.
        # Reminder delivery requires per-club opt-in data to avoid blasting all servers.
        # sf_timezone = pytz.timezone('US/Pacific')
        # now_pacific = datetime.now(tz=sf_timezone)
        # if now_pacific.hour == SCHEDULED_MESSAGE_HOUR and random.random() < SCHEDULED_MESSAGE_PERCENTAGE:
        #     for guild in bot.guilds:
        #         clubs = await asyncio.to_thread(bot.api.get_server_clubs, str(guild.id))
        #         if clubs:
        #             discord_channel_id = clubs[0].get('discord_channel')
        #             if discord_channel_id:
        #                 channel = bot.get_channel(int(discord_channel_id))
        #                 if channel:
        #                     embed = create_embed(
        #                         title="📚 Daily Reading Reminder",
        #                         description=random.choice(READING_REMINDERS),
        #                         color_key="purp"
        #                     )
        #                     await channel.send(embed=embed)
        #                     print("Reminder message sent.")
    
    # Start the scheduled tasks
    send_reminder_message.start()
    
    # Return the task so it can be stopped if needed
    return send_reminder_message