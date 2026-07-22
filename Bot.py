import discord
from discord.ext import commands, tasks
import yt_dlp as youtube_dl
import asyncio
import random
import os
import json
from datetime import datetime, timedelta

# ============ CONFIG ============
# Your Discord Server: https://discord.gg/48wfDUXF8J
# Bot Invite: https://discord.com/oauth2/authorize?client_id=1529335602355638383&permissions=8&scope=bot%20applications.commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=":", intents=intents, help_command=None)

# FFmpeg options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'extractaudio': True,
    'audioformat': 'mp3',
}

queues = {}
loop_status = {}
stay_active = {}

def get_queue(ctx):
    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []
    return queues[ctx.guild.id]

# ============ EVENTS ============

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="🎵 :help | Turki's Bot"))
    print(f"✅ {bot.user} is online!")
    print(f"📡 Connected to {len(bot.guilds)} servers")
    print(f"👤 Username: {bot.user.name}")
    print(f"🆔 Bot ID: {bot.user.id}")
    auto_stay.start()

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel:
        embed = discord.Embed(
            title="👋 Welcome!",
            description=f"Welcome {member.mention} to the server!",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing arguments! Type `:help` for usage.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found! Type `:help` for all commands.")
    else:
        await ctx.send(f"❌ Error: {str(error)[:100]}")

# ============ AUTO-STAY (ALWAYS ACTIVE) ============

@tasks.loop(minutes=5)
async def auto_stay():
    for guild in bot.guilds:
        vc = guild.voice_client
        if vc and vc.is_connected():
            # Keep the connection alive
            if not vc.is_playing() and not vc.is_paused():
                # Stay connected even when idle
                pass
    print("🔄 Auto-stay pinged all VCs")

@auto_stay.before_loop
async def before_auto_stay():
    await bot.wait_until_ready()

# ============ MUSIC COMMANDS ============

@bot.command()
async def play(ctx, *, search):
    """🎵 Play a song from YouTube"""
    if not ctx.author.voice:
        await ctx.send("❌ You're not in a voice channel!")
        return
    
    voice_channel = ctx.author.voice.channel
    
    if not ctx.voice_client:
        await voice_channel.connect()
    
    queue = get_queue(ctx)
    
    async with ctx.typing():
        try:
            with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(search, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url = info['url']
                title = info.get('title', 'Unknown Title')
                duration = info.get('duration', 0)
                thumbnail = info.get('thumbnail', '')
                
                queue.append({
                    'url': url,
                    'title': title,
                    'duration': duration,
                    'thumbnail': thumbnail,
                    'requester': ctx.author.display_name
                })
                
                if not ctx.voice_client.is_playing():
                    await play_next(ctx)
                    embed = discord.Embed(
                        title="▶️ Now Playing",
                        description=f"**{title}**",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Requested by", value=ctx.author.mention)
                    if duration:
                        mins = duration // 60
                        secs = duration % 60
                        embed.add_field(name="Duration", value=f"{mins}:{secs:02d}")
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"⏺️ Added **{title}** to queue (Position {len(queue)})")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)[:100]}")

@bot.command()
async def skip(ctx):
    """⏭️ Skip the current song"""
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("❌ Nothing is playing!")
        return
    ctx.voice_client.stop()
    await ctx.send("⏭️ Skipped!")

@bot.command()
async def stop(ctx):
    """⏹️ Stop music and clear queue (stays in VC)"""
    if ctx.voice_client:
        ctx.voice_client.stop()
        queues[ctx.guild.id] = []
        await ctx.send("⏹️ Stopped and cleared queue!")

@bot.command()
async def pause(ctx):
    """⏸️ Pause the current song"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Paused")

@bot.command()
async def resume(ctx):
    """▶️ Resume the paused song"""
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed")

@bot.command()
async def queue(ctx):
    """📋 Show the current queue"""
    queue = get_queue(ctx)
    if not queue:
        await ctx.send("📭 Queue is empty!")
        return
    
    msg = "**📋 Queue:**\n"
    total_duration = 0
    for i, song in enumerate(queue[:10], 1):
        duration = song.get('duration', 0)
        total_duration += duration
        mins = duration // 60
        secs = duration % 60
        msg += f"{i}. {song['title']} `({mins}:{secs:02d})` - {song['requester']}\n"
    
    total_mins = total_duration // 60
    total_secs = total_duration % 60
    msg += f"\n**Total queue length:** {total_mins}:{total_secs:02d}"
    await ctx.send(msg)

@bot.command()
async def now(ctx):
    """🎵 Show currently playing song"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        queue = get_queue(ctx)
        if queue:
            song = queue[0]
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{song['title']}**",
                color=discord.Color.blue()
            )
            embed.add_field(name="Requested by", value=song['requester'])
            await ctx.send(embed=embed)
        else:
            await ctx.send("🎵 Currently playing something!")
    else:
        await ctx.send("❌ Nothing is playing!")

@bot.command()
async def loop(ctx):
    """🔄 Loop the current song"""
    if ctx.guild.id not in loop_status:
        loop_status[ctx.guild.id] = False
    loop_status[ctx.guild.id] = not loop_status[ctx.guild.id]
    status = "enabled" if loop_status[ctx.guild.id] else "disabled"
    await ctx.send(f"🔄 Loop **{status}**!")

@bot.command()
async def shuffle(ctx):
    """🔀 Shuffle the queue"""
    queue = get_queue(ctx)
    if len(queue) > 1:
        random.shuffle(queue)
        await ctx.send("🔀 Queue shuffled!")
    else:
        await ctx.send("❌ Not enough songs to shuffle!")

@bot.command()
async def volume(ctx, vol: int = None):
    """🔊 Show or change volume"""
    if vol is None:
        if ctx.voice_client and ctx.voice_client.source:
            current_vol = ctx.voice_client.source.volume * 100
            await ctx.send(f"🔊 Current volume: **{int(current_vol)}%**")
        else:
            await ctx.send("🔊 Volume: 100% (default)")
        return
    
    if 1 <= vol <= 100:
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = vol / 100
            await ctx.send(f"🔊 Volume set to {vol}%")
        else:
            await ctx.send("❌ Nothing is playing!")
    else:
        await ctx.send("❌ Volume must be between 1-100")

@bot.command()
async def remove(ctx, position: int):
    """❌ Remove a song from the queue by position"""
    queue = get_queue(ctx)
    if 1 <= position <= len(queue):
        removed = queue.pop(position - 1)
        await ctx.send(f"❌ Removed **{removed['title']}** from queue!")
    else:
        await ctx.send(f"❌ Invalid position! Queue has {len(queue)} songs.")

@bot.command()
async def clearqueue(ctx):
    """🗑️ Clear the entire queue (without stopping music)"""
    queue = get_queue(ctx)
    queue.clear()
    await ctx.send("🗑️ Queue cleared!")

@bot.command()
async def jump(ctx, position: int):
    """⏩ Jump to a specific song in the queue"""
    queue = get_queue(ctx)
    if 1 <= position <= len(queue):
        # Remove all songs before the target
        del queue[:position-1]
        ctx.voice_client.stop()
        await ctx.send(f"⏩ Jumped to position {position}!")
    else:
        await ctx.send(f"❌ Invalid position! Queue has {len(queue)} songs.")

# ============ VC COMMANDS ============

@bot.command()
async def join(ctx):
    """📞 Join your voice channel"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send("✅ Joined! I'll stay here as long as you need. 😎")
    else:
        await ctx.send("❌ You're not in a voice channel!")

@bot.command()
async def stay(ctx):
    """🏠 Stay in VC forever even with 0 listeners"""
    if ctx.voice_client:
        stay_active[ctx.guild.id] = True
        await ctx.send("✅ I'll stay here forever! Even if everyone leaves, I won't go anywhere. 😎")
    else:
        await ctx.send("❌ I'm not in a voice channel! Use `:join` first.")

@bot.command()
async def leave(ctx):
    """👋 Leave the voice channel"""
    if ctx.voice_client:
        queues[ctx.guild.id] = []
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left the voice channel!")
    else:
        await ctx.send("❌ I'm not in a voice channel!")

# ============ FUN COMMANDS ============

@bot.command()
async def ping(ctx):
    """🏓 Check bot latency"""
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

@bot.command()
async def hello(ctx):
    """👋 Get a random greeting"""
    greetings = [
        "Hey! 👋", "Sup!", "Hello! 🌟", "Yo! 😎", 
        "What's up?", "Hola! 🇪🇸", "Howdy! 🤠", 
        "Greetings! 🎵", "Salutations!", "Hey there! ✨"
    ]
    await ctx.send(random.choice(greetings))

@bot.command()
async def roll(ctx):
    """🎲 Roll a dice (1-6)"""
    await ctx.send(f"🎲 You rolled: **{random.randint(1, 6)}**")

@bot.command()
async def flip(ctx):
    """🪙 Flip a coin"""
    await ctx.send(f"🪙 **{random.choice(['Heads', 'Tails'])}**!")

@bot.command()
async def user(ctx, member: discord.Member = None):
    """👤 Show user information"""
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 {member}", color=member.color)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%b %d, %Y"))
    embed.add_field(name="Account Created", value=member.created_at.strftime("%b %d, %Y"))
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def server(ctx):
    """📊 Show server information"""
    server = ctx.guild
    embed = discord.Embed(title=f"📊 {server.name}", color=discord.Color.blue())
    embed.add_field(name="Owner", value=server.owner)
    embed.add_field(name="Members", value=server.member_count)
    embed.add_field(name="Channels", value=len(server.channels))
    embed.add_field(name="Created", value=server.created_at.strftime("%b %d, %Y"))
    embed.set_thumbnail(url=server.icon.url if server.icon else None)
    await ctx.send(embed=embed)

@bot.command()
async def eightball(ctx, *, question):
    """🎱 Ask the magic 8-ball a question"""
    responses = [
        "Yes!", "No!", "Maybe 🤔", "Definitely!", "Nope!", 
        "For sure!", "Ask again later", "Absolutely!", "Not a chance", 
        "Without a doubt!", "Cannot predict now", "Outlook good!",
        "Very doubtful!", "Signs point to yes!", "Reply hazy, try again"
    ]
    embed = discord.Embed(
        title="🎱 Magic 8-Ball",
        description=f"Question: {question}\nAnswer: **{random.choice(responses)}**",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    """🖼️ Show a user's avatar"""
    member = member or ctx.author
    embed = discord.Embed(title=f"🖼️ {member}'s Avatar", color=discord.Color.blue())
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def say(ctx, *, message):
    """💬 Make the bot say something"""
    await ctx.send(message)

@bot.command()
async def status(ctx, *, activity):
    """🎮 Change the bot's status"""
    await bot.change_presence(activity=discord.Game(name=activity))
    await ctx.send(f"✅ Status updated to: Playing **{activity}**")

@bot.command()
async def whois(ctx, member: discord.Member = None):
    """🔍 Show detailed user information"""
    member = member or ctx.author
    embed = discord.Embed(title=f"🔍 {member}", color=member.color)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Status", value=member.status)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%b %d, %Y"))
    roles = [r.name for r in member.roles if r.name != "@everyone"]
    embed.add_field(name="Roles", value=", ".join(roles) if roles else "None")
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def inspire(ctx):
    """💡 Get an inspiring quote"""
    quotes = [
        "The best way to predict the future is to create it.",
        "Code is poetry in motion.",
        "Keep calm and code on.",
        "Made by Turki (the best)!",
        "Bots are friends, not food.",
        "Success is not final, failure is not fatal.",
        "Believe you can and you're halfway there.",
        "The only way to do great work is to love what you do.",
        "In the middle of difficulty lies opportunity.",
        "You are the author of your own story."
    ]
    await ctx.send(f"💡 *{random.choice(quotes)}*")

@bot.command()
async def joke(ctx):
    """😂 Get a random joke"""
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "What do you call a fake noodle? An impasta!",
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "I told my computer I needed a break... now it won't stop sending me Kit-Kats.",
        "Why don't scientists trust atoms? Because they make up everything!",
        "What do you call a bear with no teeth? A gummy bear!",
    ]
    await ctx.send(f"😂 {random.choice(jokes)}")

@bot.command()
async def poll(ctx, *, question):
    """📊 Create a yes/no poll"""
    embed = discord.Embed(
        title="📊 Poll",
        description=question,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Poll by {ctx.author.display_name}")
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👎")
    await msg.add_reaction("🤷")

@bot.command()
async def invite(ctx):
    """🔗 Get the bot invite link"""
    embed = discord.Embed(
        title="🔗 Invite VCBotY",
        description="Add me to your server!",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Bot Invite",
        value="https://discord.com/oauth2/authorize?client_id=1529335602355638383&permissions=8&scope=bot%20applications.commands",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command()
async def uptime(ctx):
    """⏱️ Show how long the bot has been online"""
    if hasattr(bot, 'start_time'):
        delta = datetime.now() - bot.start_time
        hours = delta.seconds // 3600
        minutes = (delta.seconds // 60) % 60
        await ctx.send(f"⏱️ Uptime: **{hours}h {minutes}m**")
    else:
        await ctx.send("⏱️ Just started!")

# ============ ADMIN COMMANDS ============

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    """🗑️ Delete messages (admin only)"""
    if amount > 100:
        amount = 100
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🗑️ Deleted {amount} messages!")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason given"):
    """👢 Kick a member (admin only)"""
    await member.kick(reason=reason)
    await ctx.send(f"👢 Kicked {member.mention} Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason given"):
    """🔨 Ban a member (admin only)"""
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Banned {member.mention} Reason: {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    """🔇 Mute a member in voice (admin only)"""
    if member.voice and member.voice.channel:
        await member.edit(mute=True)
        await ctx.send(f"🔇 Muted {member.mention} in voice!")
    else:
        await ctx.send("❌ That user is not in a voice channel!")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    """🔊 Unmute a member in voice (admin only)"""
    if member.voice:
        await member.edit(mute=False)
        await ctx.send(f"🔊 Unmuted {member.mention} in voice!")
    else:
        await ctx.send("❌ That user is not in a voice channel!")

# ============ HELP COMMAND ============

@bot.command()
async def help(ctx):
    """📖 Show all commands"""
    embed = discord.Embed(
        title="🎵 VCBotY Music - Commands",
        description="Made by Turki (the best) ✨",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="🎵 Music",
        value="`:play` `:skip` `:stop` `:pause` `:resume` `:queue` `:now` `:loop` `:shuffle` `:volume` `:remove` `:clearqueue` `:jump`",
        inline=False
    )
    
    embed.add_field(
        name="📞 Voice",
        value="`:join` `:stay` `:leave`",
        inline=False
    )
    
    embed.add_field(
        name="🎮 Fun",
        value="`:ping` `:hello` `:roll` `:flip` `:user` `:server` `:8ball` `:avatar` `:say` `:status` `:whois` `:inspire` `:joke` `:poll` `:invite` `:uptime`",
        inline=False
    )
    
    embed.add_field(
        name="🛡️ Admin",
        value="`:clear` `:kick` `:ban` `:mute` `:unmute`",
        inline=False
    )
    
    embed.set_footer(text="💡 Type :help <command> for more info")
    await ctx.send(embed=embed)

# ============ PLAY NEXT FUNCTION ============

async def play_next(ctx):
    queue = get_queue(ctx)
    
    # Check if loop is enabled
    if ctx.guild.id in loop_status and loop_status[ctx.guild.id] and queue:
        # Re-add the current song to the front of the queue
        current_song = queue[0].copy()
        queue.append(current_song)
    
    if queue:
        song = queue.pop(0)
        source = discord.FFmpegPCMAudio(song['url'], **FFMPEG_OPTIONS)
        
        def after_play(error):
            if error:
                print(f"Playback error: {error}")
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        
        ctx.voice_client.play(source, after=after_play)
    else:
        # Stay in VC — don't disconnect!
        if ctx.guild.id not in stay_active:
            stay_active[ctx.guild.id] = True
        # Only disconnect if stay is disabled
        if not stay_active.get(ctx.guild.id, True):
            await ctx.voice_client.disconnect()

# ============ STARTUP ============

@bot.event
async def on_connect():
    bot.start_time = datetime.now()
    print("🔄 Connected to Discord!")

# ============ RUN BOT ============

if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if not token:
        print("❌ ERROR: No token found! Set TOKEN environment variable.")
        print("📌 Get your token at: https://discord.com/developers/applications")
        exit()
    bot.run(token)
