import discord
from discord.ext import commands
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Setup
TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load memory
MEMORY_FILE = "memory.json"
if not os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, 'w') as f:
        json.dump({}, f)

def load_memory():
    with open(MEMORY_FILE, 'r') as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

def get_memory_for_user(memory, user_id):
    return memory.get(str(user_id), [])

# Prompt builder
def build_prompt(message, memory_list):
    facts = "\n".join(f"- {fact}" for fact in memory_list)
    return f"""
You are Galobalist JR., a chill, sarcastic Discord bot that roasts users gently and replies like you're one of the Global Galobalists. Here's what you know about this group:
{facts if facts else '- You don\'t know much yet. Make up for it with spicy sarcasm.'}

User said: "{message}"

Reply with a short, clever, slightly roasty or witty response. Don't explain yourself.
"""

# Commands
@bot.command(name='talk')
async def talk(ctx, *, message):
    memory = load_memory()
    user_memory = get_memory_for_user(memory, ctx.author.id)
    prompt = build_prompt(message, user_memory)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response.choices[0].message.content.strip()
        await ctx.send(reply)
    except Exception as e:
        await ctx.send("Galobalist JR. had a minor existential crisis.")
        print(f"OpenAI error: {e}")

@bot.command(name='remember')
async def remember(ctx, user: discord.Member, *, fact):
    memory = load_memory()
    uid = str(user.id)
    if uid not in memory:
        memory[uid] = []
    memory[uid].append(fact)
    save_memory(memory)
    await ctx.send(f"Got it. I will forever associate @**{user.display_name}** with: \"{fact}\"")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Respond when bot is mentioned
    if bot.user.mentioned_in(message):
        memory = load_memory()
        user_memory = get_memory_for_user(memory, message.author.id)
        prompt = build_prompt(message.content, user_memory)

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            reply = response.choices[0].message.content.strip()
            await message.channel.send(reply)
        except Exception as e:
            await message.channel.send("Even I can't process what you just said.")
            print(f"Mention error: {e}")

    await bot.process_commands(message)

# Run the bot
bot.run(TOKEN)