import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import random
import os
import json
from datetime import datetime

# Discord Server: https://discord.gg/48wfDUXF8J
# Bot Invite: https://discord.com/oauth2/authorize?client_id=1529335602355638383&permissions=8&scope=bot%20applications.commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=":", intents=intents)

# FFmpeg options for music
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

def get_queue(ctx):
    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []
    return queues[ctx.guild.id]

# ============ EVENTS ============

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="🎵 Made by Turki (the best)"))
    print(f"✅ {bot.user} is online!")
    print(f"📡 Connected to {len(bot.guilds)} servers")
    print(f"👤 Username: {bot.user.name}")
    print(f"🆔 Bot ID: {bot.user.id}")

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel:
        await channel.send(f"👋 Welcome {member.mention} to the server! Enjoy your stay!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing arguments! Type `:help` for usage.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found! Type `:help` for commands.")
    else:
        await ctx.send(f"❌ Error: {str(error)}")

# ============ MUSIC COMMANDS ============

@bot.command()
async def play(ctx, *, search):
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
                    await ctx.send(f"▶️ Now playing: **{title}**")
                else:
                    await ctx.send(f"⏺️ Added to queue: **{title}** (Position {len(queue)})")
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

@bot.command()
async def skip(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("❌ Nothing is playing!")
        return
    ctx.voice_client.stop()
    await ctx.send("⏭️ Skipped!")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        queues[ctx.guild.id] = []
        await ctx.send("⏹️ Stopped and cleared queue!")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Paused")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Resumed")

@bot.command()
async def queue(ctx):
    queue = get_queue(ctx)
    if not queue:
        await ctx.send("📭 Queue is empty!")
        return
    
    msg = "**📋 Queue:**\n"
    total_duration = 0
    for i, song in enumerate(queue[:10], 1):
        duration = song.get('duration', 0)
        total_duration += duration
        min_dur = duration // 60
        sec_dur = duration % 60
        msg += f"{i}. {song['title']} `({min_dur}:{sec_dur:02d})` - {song['requester']}\n"
    
    total_min = total_duration // 60
    total_sec = total_duration % 60
    msg += f"\n**Total queue length:** {total_min}:{total_sec:02d}"
    await ctx.send(msg)

@bot.command()
async def now(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        queue = get_queue(ctx)
        if queue:
            song = queue[0]
            await ctx.send(f"🎵 Now playing: **{song['title']}**")
        else:
            await ctx.send("🎵 Currently playing something!")
    else:
        await ctx.send("❌ Nothing is playing!")

@bot.command()
async def loop(ctx):
    if ctx.guild.id not in loop_status:
        loop_status[ctx.guild.id] = False
    loop_status[ctx.guild.id] = not loop_status[ctx.guild.id]
    status = "enabled" if loop_status[ctx.guild.id] else "disabled"
    await ctx.send(f"🔄 Loop **{status}**!")

@bot.command()
async def shuffle(ctx):
    queue = get_queue(ctx)
    if len(queue) > 1:
        random.shuffle(queue)
        await ctx.send("🔀 Queue shuffled!")
    else:
        await ctx.send("❌ Not enough songs to shuffle!")

@bot.command()
async def volume(ctx, vol: int = None):
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
    queue = get_queue(ctx)
    if 1 <= position <= len(queue):
        removed = queue.pop(position - 1)
        await ctx.send(f"❌ Removed **{removed['title']}** from queue!")
    else:
        await ctx.send(f"❌ Invalid position! Queue has {len(queue)} songs.")

# ============ VC COMMANDS ============

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send("Hello! I'm VCBotY Music!!! Turki made me (the best) and yeah! Join my Discord server: https://discord.gg/48wfDUXF8J")
    else:
        await ctx.send("❌ You're not in a voice channel!")

@bot.command()
async def stay(ctx):
    if ctx.voice_client:
        await ctx.send("✅ I'll stay here forever! Even if you leave, I won't go anywhere. 😎")
    else:
        await ctx.send("❌ I'm not in a voice channel! Use `:join` first.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        queues[ctx.guild.id] = []
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left the voice channel!")
    else:
        await ctx.send("❌ I'm not in a voice channel!")

# ============ FUN COMMANDS ============

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)}ms`")

@bot.command()
async def hello(ctx):
    greetings = ["Hey! 👋", "Sup!", "Hello! 🌟", "Yo! 😎", "What's up?", "Hola! 🇪🇸", "Howdy! 🤠", "Greetings! 🎵"]
    await ctx.send(random.choice(greetings))

@bot.command()
async def roll(ctx):
    await ctx.send(f"🎲 You rolled: **{random.randint(1, 6)}**")

@bot.command()
async def flip(ctx):
    await ctx.send(f"🪙 **{random.choice(['Heads', 'Tails'])}**!")

@bot.command()
async def user(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 {member}", color=member.color)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%b %d, %Y"))
    embed.add_field(name="Account Created", value=member.created_at.strftime("%b %d, %Y"))
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def server(ctx):
    server = ctx.guild
    embed = discord.Embed(title=f"📊 {server.name}", color=discord.Color.blue())
    embed.add_field(name="Owner", value=server.owner)
    embed.add_field(name="Members", value=server.member_count)
    embed.add_field(name="Channels", value=len(server.channels))
    embed.add_field(name="Created", value=server.created_at.strftime("%b %d, %Y"))
    await ctx.send(embed=embed)

@bot.command()
async def eightball(ctx, *, question):
    responses = ["Yes!", "No!", "Maybe 🤔", "Definitely!", "Nope!", "For sure!", "Ask again later", "Absolutely!", "Not a chance", "Without a doubt!", "Cannot predict now"]
    await ctx.send(f"🎱 **{random.choice(responses)}**")

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"🖼️ {member}'s Avatar")
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def say(ctx, *, message):
    await ctx.send(message)

@bot.command()
async def status(ctx, *, activity):
    await bot.change_presence(activity=discord.Game(name=activity))
    await ctx.send(f"✅ Status updated to: Playing **{activity}**")

@bot.command()
async def whois(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"🔍 {member}", color=member.color)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Status", value=member.status)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%b %d, %Y"))
    embed.add_field(name="Roles", value=", ".join([r.name for r in member.roles if r.name != "@everyone"]) or "None")
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def inspire(ctx):
    quotes = [
        "The best way to predict the future is to create it.",
        "Code is poetry in motion.",
        "Keep calm and code on.",
        "Made by Turki (the best)!",
        "Bots are friends, not food."
    ]
    await ctx.send(f"💡 *{random.choice(quotes)}*")

# ============ ADMIN COMMANDS ============

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    if amount > 100:
        amount = 100
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🗑️ Deleted {amount} messages!")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason given"):
    await member.kick(reason=reason)
    await ctx.send(f"👢 Kicked {member.mention} Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason given"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Banned {member.mention} Reason: {reason}")

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🎵 VCBotY Music Commands", color=discord.Color.gold())
    embed.add_field(name="🎵 Music", value="`:play` `:skip` `:stop` `:pause` `:resume` `:queue` `:now` `:loop` `:shuffle` `:volume` `:remove`", inline=False)
    embed.add_field(name="📞 VC", value="`:join` `:stay` `:leave`", inline=False)
    embed.add_field(name="🎮 Fun", value="`:ping` `:hello` `:roll` `:flip` `:user` `:server` `:8ball` `:avatar` `:say` `:status` `:whois` `:inspire`", inline=False)
    embed.add_field(name="🛡️ Admin", value="`:clear` `:kick` `:ban`", inline=False)
    embed.add_field(name="📖 Help", value="`:help`", inline=False)
    embed.set_footer(text="Made by Turki (the best) | Join: https://discord.gg/48wfDUXF8J")
    await ctx.send(embed=embed)

# ============ PLAY NEXT FUNCTION ============

async def play_next(ctx):
    queue = get_queue(ctx)
    if queue:
        song = queue.pop(0)
        source = discord.FFmpegPCMAudio(song['url'], **FFMPEG_OPTIONS)
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    else:
        await ctx.send("⏸️ Queue empty. I'll stay here until you play something!")

# ============ RUN BOT ============

if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if not token:
        print("❌ ERROR: No token found! Set TOKEN environment variable.")
        print("📌 Get your token at: https://discord.com/developers/applications")
        exit()
    bot.run(token)
