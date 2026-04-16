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
        
        # TODO: Re-enable once clubs/servers have notification/reminder settings.
        # Reminder delivery requires per-club opt-in data to avoid blasting all servers.
        pass
    
    # Start the scheduled tasks
    send_reminder_message.start()
    
    # Return the task so it can be stopped if needed
    return send_reminder_message