import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, time
from discord import File
import pytz
import logging

class BossSpawn:
    def __init__(self, name, location, spawn_times):
        self.name = name
        self.location = location
        self.spawn_times = spawn_times

    def get_next_spawn_time(self):
        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        today_index = now.weekday()  # Monday is 0 and Sunday is 6
        days_checked = 0

        while days_checked < 7:  # Check the next 7 days
            day_to_check = (today_index + days_checked) % 7
            day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][day_to_check]
            spawn_time = self.spawn_times.get(day_name)

            if spawn_time is not None:
                # Convert spawn_time to timezone-aware in UTC
                utc_spawn_time = spawn_time.replace(tzinfo=pytz.utc)

                # Combine the date part of now with utc_spawn_time
                next_spawn_datetime = datetime.combine(now.date(), utc_spawn_time)
                # Adjust for the next day(s) if needed
                next_spawn_datetime += timedelta(days=days_checked)
                if next_spawn_datetime > now:
                    return next_spawn_datetime

            days_checked += 1

        return None

    def should_send_reminder(self, now, minutes_before):
        next_spawn_time = self.get_next_spawn_time()
        reminder_time = next_spawn_time - timedelta(minutes=minutes_before)
        
        # Extending the time window to 2 minutes for more reliability
        should_send = now >= reminder_time and now < reminder_time + timedelta(minutes=2)

        # Logging for troubleshooting
        logging.info(f"Checking reminder for {self.name}: now={now}, reminder_time={reminder_time}, should_send={should_send}")
        
        return should_send
    
# Define your bosses
dark_torask = BossSpawn("Dark Torask", "Eienble Cave", {
    "Sunday": time(0, 0),
    "Monday": time(3, 0),
    "Tuesday": time(7, 0),
    "Wednesday": time(10, 0),
    "Thursday": time(14, 30),
    "Friday": time(16, 0),
    "Saturday": time(21, 0),
})
ghidorah = BossSpawn("Ghidorah", "Plain Of Bubble", {
    "Sunday": time(14, 30),
    "Monday": time(16, 0),
    "Tuesday": time(21, 0),
    "Wednesday": time(0, 0),
    "Thursday": time(3, 30),
    "Friday": time(7, 0),
    "Saturday": time(10, 0),
})

def get_earliest_boss_spawn(bosses, now):
    next_spawn = None
    next_boss = None

    for boss in bosses:
        spawn_time = boss.get_next_spawn_time()
        if next_spawn is None or spawn_time < next_spawn:
            next_spawn = spawn_time
            next_boss = boss

    return next_boss, next_spawn

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.guild_messages = True  # Make sure this is enabled
bot = commands.Bot(command_prefix='!',case_insensitive=True ,intents=intents)
bot.remove_command("help")


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    boss_spawn_check.start()

@bot.command(name='nextboss')
async def next_boss(ctx):
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    bosses = [dark_torask, ghidorah]
    next_boss, next_spawn = get_earliest_boss_spawn(bosses, now)

    if next_boss is None:
        await ctx.send("No upcoming boss spawns found.")
        return

    time_until_spawn = next_spawn - now
    hours, remainder = divmod(int(time_until_spawn.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    if next_boss.name == "Ghidorah":
        image_path = "gidorah.jpeg"  #photo gid
    elif next_boss.name == "Dark Torask":
        image_path = "dark_torask.jpeg"  #photo dt
    else:
        image_path = None

    if image_path:
        with open(image_path, "rb") as f:
            await ctx.send(
                f"Next boss ({next_boss.name}) spawns in {hours} hours, {minutes} minutes, and {seconds} seconds at {next_boss.location}!.",
                file=File(f)
            )
    else:
        await ctx.send(f"Next boss ({next_boss.name}) spawns in {hours} hours, {minutes} minutes, and {seconds} seconds at {next_boss.location}!.")

@tasks.loop(minutes=1)
async def boss_spawn_check():
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    for boss in [dark_torask, ghidorah]:
        channel = bot.get_channel(1179773834136657990)  #channel ID

        if boss.should_send_reminder(now, 15):
            if boss.name == "Ghidorah":
                image_path = "ghidorah.jpeg"  #photo gid
            elif boss.name == "Dark Torask":
                image_path = "dark_torask.jpeg"  #photo dt

            with open(image_path, "rb") as f:
                await channel.send(
                    f"<@&1179749808391589989> Boss {boss.name} is spawning in 15 minutes at {boss.location}!",
                    file=File(f),
                    allowed_mentions=discord.AllowedMentions(roles=True)
                )

        elif boss.should_send_reminder(now, 5):
            if boss.name == "Ghidorah":
                image_path = "ghidorah.jpeg"  #photo gid
            elif boss.name == "Dark Torask":
                image_path = "dark_torask.jpeg"  #photo dt

            with open(image_path, "rb") as f:
                await channel.send(
                    f"<@&1179749808391589989> Boss {boss.name} is spawning in 5 minutes at {boss.location}!",
                    file=File(f),
                    allowed_mentions=discord.AllowedMentions(roles=True)
                )

# Start bot
bot.run('token')  #Discord bot token