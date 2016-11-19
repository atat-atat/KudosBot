import pip
import importlib
import os
import json
import datetime

def module_checkup(modules):
	"""Makes sure all modules are installed."""
	for k, v in modules.items():
		try:
			importlib.__import__(k)
		except ImportError:
			print("You do not have {} installed. Would you like me to install it for you?".format(k))
			choice = input("> ")

			if choice.lower().startswith("y"):
				try:
					pip.main(["install", v])
					print("Done!")
				except:
					print("Failed to install {}, from {}.".format(k, v))
			else:
				print("Skipping installation...")
	return

def create_json_ifno(directory, file_data, **kwargs):
	"""Creates a JSON file with default values if it doesn't exist."""
	if not os.path.isfile(directory):
		d_write_mode = kwargs.get("d_access_mode", "w+")
		with open(directory, d_write_mode) as f:
			json.dump(file_data, f)

	return

def jsonIO(directory, file_data=None, access_type=None, **kwargs):
	"""A json file manager."""
	default_data = kwargs.get("default_data", None)

	if default_data != None:
		if not os.path.isfile(directory):
			d_write_mode = kwargs.get("d_access_mode", "w+")
			with open(directory, d_write_mode) as f:
				json.dump(default_data, f)

	if access_type is None and file_data is not None:
		access_type = "write"
	elif access_type is None and file_data is None:
		access_type = "read"

	if access_type == "read":
		read_mode = kwargs.get("access_mode", "r")
		with open(directory, read_mode) as f:
			return json.load(f)
	elif access_type == "write":
		write_mode = kwargs.get("access_mode", "w")
		with open(directory, write_mode) as f:
			json.dump(file_data, f)
		return

default_config = {
	"username": "Kudos",
	"token": "",
	"prefix": "$",
	"data": {}
}

create_json_ifno("./config.json", default_config)
module_checkup({"discord": "discord.py"}) #make sure all necessary modules are installed, I expect the user is dumb and doesn't know much about installing third-party modules on their own.

import discord
from discord.ext import commands
import asyncio

def has_permissions(**perms):
	"""A wrapper that checks if the command executor has the permissions needed."""
	def predicate(ctx):
		member = perms.get("member", ctx.message.author)
		if is_server_owner(member, ctx):
			return True
		if is_administrator(member):
			return True
			
		channel = ctx.message.channel
		resolved = channel.permissions_for(member)
		return all(getattr(resolved, name, None) == value for name, value in perms.items())

	return commands.check(predicate)

def is_server_owner(member, ctx):
	"""Checks if the member is the server owner."""
	if not ctx.message.channel.is_private:
		return member == ctx.message.server.owner
	else:
		return True

def is_administrator(member):
	"""Checks if the member is an administrator."""
	try:
		for role in member.roles:
			if role.permissions.administrator:
				return True
	except AttributeError:
		return True

config = jsonIO("./config.json")

if config["token"] == "": #if the token is basically nothing...
	token = input("Please input your bot account token here: ")
	config["token"] = token
	jsonIO("./config.json", config)
config = jsonIO("./config.json")

client = commands.Bot(command_prefix=config["prefix"], description="KudosBot - A statistic-managing freak.", pm_help=True)

def member_exists(member_id):
	"""Checks if a member exists."""
	return member_id in jsonIO("./config.json")["data"]

def add_member_ifno(*member_ids):
	"""Add a new member if it doesn't exist."""
	c_json = jsonIO("./config.json")
	for member_id in member_ids:
		if not member_exists(member_id):
			c_json["data"][member_id] = {}
			c_json["data"][member_id]["zimb_points"] = 0
			c_json["data"][member_id]["giveable_zimb_points"] = c_json["default_giveable_points"]
			c_json["data"][member_id]["kudos_points"] = 0

	jsonIO("./config.json", c_json)
	return

perms = discord.Permissions.none()
perms.read_messages = True
perms.send_messages = True
perms.manage_roles = True
perms.ban_members = True
perms.kick_members = True
perms.manage_messages = True
perms.embed_links = True
perms.read_message_history = True
perms.attach_files = True

#Client event listeners
@client.event
async def on_ready():
	"""
	When the bot is ready.
	"""
	if not hasattr(client, 'uptime'):
		client.uptime = datetime.datetime.utcnow()

	client.app_info = await client.application_info()
	client.client_id = client.app_info.id
	client.invite_url = discord.utils.oauth_url(client.client_id, perms)

	if client.user.name != config["username"]:
		await client.edit_profile(username=config["username"])

	print("I'm ready for use!\n\nUse {} to invite me to your server.\n----------------\nName: {}\nID: {}\n----------------".format(client.invite_url, client.user.name, client.user.id))

@client.event
async def on_command(cmd, ctx):
	print("{}: {} executed command: {}".format(ctx.message.timestamp, format(ctx.message.author).encode('utf-8'), ctx.message.content))

@client.event
async def on_command_error(error, ctx):
	"""
	When something goes wrong with a command.
	"""
	if isinstance(error, commands.MissingRequiredArgument):
		await client.send_message(ctx.message.channel, "There is a missing argument. Type `$help <command>` to view information about that command.")
	elif isinstance(error, commands.errors.CheckFailure):
		await client.send_message(ctx.message.channel, "You do not have permission to use this command.")
	elif isinstance(error, commands.errors.CommandNotFound):
		pass #ignore command not found errors
	elif isinstance(error, discord.errors.Forbidden):
		await client.send_message(ctx.message.channel, "I don't have the permission to do that.")
	elif isinstance(error, commands.errors.BadArgument):
		await client.send_message(ctx.message.channel, "Something went wrong.\n```xl\n{}: {}\n```".format(type(error).__name__, error))
	else:
		print("{}: {}".format(type(error).__name__, error))

#Commands
@client.command(name="kudo", aliases=["kudos"], pass_context=True)
@has_permissions(manage_messages=True)
async def add_kudos(ctx, member : discord.Member, points : int=1):
	"""Add Kudos points to members."""
	msg = ctx.message
	add_member_ifno(member.id)

	c_json = jsonIO("./config.json")

	c_json["data"][member.id]["kudos_points"] += points
	jsonIO("./config.json", c_json)
	await client.say("{} has been awarded {} kudos points by {}".format(member, points, msg.author))
	return

@client.command(name="kudodestroy", aliases=["kudosdestroy"], pass_context=True)
async def remove_kudos(ctx, member : discord.Member, points : int=1):
	"""Remove Kudos points from members."""
	msg = ctx.message

	if not member_exists(member.id):
		await client.say("That member does not have any points.")
		return

	c_json = jsonIO("./config.json")
	c_json["data"][member.id]["kudos_points"] -= points
	jsonIO("./config.json", c_json)
	await client.say("{} of {}'s Kudos points have been destroyed by {}".format(points, member, msg.author))
	return

@client.command(name="zimb", pass_context=True)
async def add_zimb(ctx, member : discord.Member, points : int=1):
	"""Add Zimbabwe Points to your favorite members."""

	if member == ctx.message.author:
		await client.say("Nice try.")
		return

	msg = ctx.message

	add_member_ifno(msg.author.id, member.id)

	c_json = jsonIO("./config.json")

	if points > c_json["data"][msg.author.id]["giveable_zimb_points"]:
		await client.say("You do not have enough points.")
		return

	c_json["data"][member.id]["zimb_points"] += points
	c_json["data"][msg.author.id]["giveable_zimb_points"] -= points

	jsonIO("./config.json", c_json)

	await client.say("{} has been given {} *Zimbabwe points* by {}".format(member, points, msg.author))
	return

@client.command(name="zimbdestroy", pass_context=True)
@has_permissions(manage_messages=True)
async def remove_zimb(ctx, member : discord.Member, points : int=1):
	"""Decreases the amount of Zimbabwe points for a member."""
	msg = ctx.message

	if not member_exists(member.id):
		await client.say("That member does not have any Zimbabwe points.")
		return

	c_json = jsonIO("./config.json")

	c_json["data"][member.id]["zimb_points"] -= points
	c_json["data"][msg.author.id]["giveable_zimb_points"] += points
	jsonIO("./config.json", c_json)
	await client.say("{} of {}'s Zimbabwe points have been removed by {}".format(points, member, msg.author))
	return

@client.command(name="zimbme", aliases=["view_zimb"], pass_context=True)
async def view_zimbs(ctx, member : discord.Member=None):
	"""View your (or a member's) Zimbabwe points."""
	msg = ctx.message
	if member is None:
		member = msg.author

	if member == msg.author:
		if not member_exists(member.id):
			await client.say("You do not have any Zimbabwe points.")
			return
	else:
		if not member_exists(member.id):
			await client.say("{} does not have any Zimbabwe points.")
			return

	c_json = jsonIO("./config.json")

	if member == msg.author:
		await client.say("You currently have {} Zimbabwe points ({} giveable points.)".format(c_json["data"][member.id]["zimb_points"], c_json["data"][member.id]["giveable_zimb_points"]))
	else:
		await client.say("{} has {} Zimbabwe points ({} giveable points.)".format(member, c_json["data"][member.id]["zimb_points"], c_json["data"][member.id]["giveable_zimb_points"]))
	return

@client.command(name="kudome", aliases=["kudosme", "kudo_view", "kudos_view"], pass_context=True)
async def view_kudos(ctx, member : discord.Member=None):
	"""View your (or a member's) Kudos points."""
	msg = ctx.message

	if member is None:
		member = msg.author

	if member == msg.author:
		if not member_exists(member.id):
			await client.say("You do not have any Kudos points.")
			return
	else:
		if not member_exists(member.id):
			await client.say("{} does not have any Kudos points.".format(member))
			return

	c_json = jsonIO("./config.json")

	if member == msg.author:
		await client.say("You currently have {} Kudos points.".format(c_json["data"][member.id]["kudos_points"]))
	else:
		await client.say("{} has {} Kudos points.".format(member, c_json["data"][member.id]["kudos_points"]))
	return

@client.command(name="info", pass_context=True)
async def view_all(ctx, member : discord.Member=None):
	"""Views Kudos and Zimbabwe points for you, or a member."""
	msg = ctx.message

	if member is None:
		member = msg.author

	if member == msg.author:
		if not member_exists(member.id):
			await client.say("You do not have any points.")
			return
	else:
		if not member_exists(member.id):
			await client.say("{} does not have any points.".format(member))
			return

	c_json = jsonIO("./config.json")

	if member == msg.author:
		await client.say("You currently have {} Kudos points, and {} Zimbabwe points ({} giveable Zimbabwe points.)".format(c_json["data"][member.id]["kudos_points"], c_json["data"][member.id]["zimb_points"], c_json["data"][member.id]["giveable_zimb_points"]))
	else:
		await client.say("{} currently has {} Kudos points, and {} Zimbabwe points ({} giveable Zimbabwe points.)".format(member, c_json["data"][member.id]["kudos_points"], c_json["data"][member.id]["zimb_points"], c_json["data"][member.id]["giveable_zimb_points"]))

async def zimb_loop():
	"""The task that resets giveable Zimbabwe points every 1 hour (3600 seconds.)"""
	await client.wait_until_ready()
	while not client.is_closed:
		c_json = jsonIO("./config.json")
		modified = False
		for member in c_json["data"]:
			if c_json["data"][member]["giveable_zimb_points"] != 20:
				modified = True
				c_json["data"][member]["giveable_zimb_points"] = 20
		if modified:
			jsonIO("./config.json", c_json)

		await asyncio.sleep(3600)

def start(token):
	"""Starts the bot (user accounts are not supported.)"""
	loop = asyncio.get_event_loop()
	loop.create_task(zimb_loop())

	try:
		loop.run_until_complete(client.start(token))
	except KeyboardInterrupt:
		loop.run_until_complete(client.logout())
	finally:
		loop.close()

start(config["token"])