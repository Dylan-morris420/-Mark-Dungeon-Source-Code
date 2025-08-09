import os, time, json, pygame, msvcrt, shutil, colorama, re	#Import necessary modules
from termcolor import colored
from colorama import Fore, Back, Style, init
init(autoreset=True)
colorama.init()
pygame.mixer.pre_init(44100, -8, 2, 256)
pygame.mixer.init()
pygame.init()
print('test')
select = pygame.mixer.Sound("blipSelect.wav")
dialogue = pygame.mixer.Sound("dialogue.wav")
hurt = pygame.mixer.Sound("explosion.wav")
heart = pygame.mixer.Sound("powerUp.wav")
no = pygame.mixer.Sound("hitHurt.wav")
pygame.mixer.music.load("dungeon.ogg")


#===SYSTEM/ENGINE CMDS===#

def inputm(target_key):	#checks if a key has been pressed
	if msvcrt.kbhit():
		key = msvcrt.getch()
		# msvcrt returns bytes, so decode to string
		try:
			key = key.decode('utf-8').lower()
		except:
			return False
		if key == target_key.lower():
			return True
	return False

def clear():	#Clears the terminal screen.
	try:	#Trys to clear with 'cls' but if on linux it uses 'clear'
		os.system('cls')
	except Exception as e:
		os.system('clear')

def clear_previous_lines(n):
	for _ in range(n):
		print("\033[A", end='')
		print("\033[M", end='') 

def dialogueanim(string, color=None, on_color=None, attrs=None, flush=False, mul=2):
	"""
	Prints string with animation, supporting:
	- termcolor coloring via color/on_color/attrs for uncolored strings
	- embedded ANSI codes parsed and printed properly if no color args given
	- plays sound every cooldown seconds
	- respects speed multiplier `mul`
	- can be interrupted by pressing ESC (via inputm)
	"""
	cooldown = 0.075

	if not hasattr(dialogueanim, "last_played_time"):
		dialogueanim.last_played_time = 0

	# Check if coloring is requested or if string contains ANSI codes
	has_ansi = bool(re.search(r'\033\[[0-9;]*m', string))
	use_termcolor = any(x is not None for x in (color, on_color, attrs))
	chars = 0


	if use_termcolor:
		# Print each letter colored using termcolor.colored()
		for letter in string:
			if inputm('\x1b'):  # ESC key pressed? skip animation
				print(colored(string[chars:], color=color, on_color=on_color, attrs=attrs), flush=True)
				break
			print(colored(letter, color=color, on_color=on_color, attrs=attrs), end='', flush=True)
			chars += 1
			now = time.time()
			if now - dialogueanim.last_played_time > cooldown:
				dialogue.play()
				dialogueanim.last_played_time = now
			if len(string) == 1:
				time.sleep(1 / (len(string) * 2 * mul))
			else:
				time.sleep(1 / (len(string) * mul))
		if not flush:
			print()

	elif has_ansi:
		color_code = ""
		tokens = re.findall(r'(\033\[[0-9;]*m|.)', string)
		for i, token in enumerate(tokens):
			if inputm('\x1b'):  # ESC key pressed? skip animation
				# Print the rest of the tokens from this point onward
				for t in tokens[i:]:
					if t.startswith("\033["):
						color_code = t
					else:
						print(f"{color_code}{t}\033[0m", end='', flush=True)
				break

			if token.startswith("\033["):
				color_code = token
			else:
				print(f"{color_code}{token}\033[0m", end='', flush=True)
				chars += 1

				now = time.time()
				if now - dialogueanim.last_played_time > cooldown:
					dialogue.play()
					dialogueanim.last_played_time = now

				if len(string) / 10 == 1:
					time.sleep(1 / (len(string) / 10 * 2 * mul))
				else:
					time.sleep(1 / (len(string) / 10 * mul))
		if not flush:
			print()



	else:
		# Plain print with animation
		for letter in string:
			if inputm('\x1b'):
				print(string[chars:], flush=True)
				break
			print(letter, end='', flush=True)
			chars += 1
			now = time.time()
			if now - dialogueanim.last_played_time > cooldown:
				dialogue.play()
				dialogueanim.last_played_time = now
			if len(string) == 1:
				time.sleep(1 / (len(string) * 2 * mul))
			else:
				time.sleep(1 / (len(string) * mul))
		if not flush:
			print()

def error(msg):	#Prints an error without crashing to warn the user
	clear()
	dialogueanim('ERROR: ' + msg, 'red')
	time.sleep(1)
	clear()

def inputb(string):	#input but cooler
	inp = input(string)
	select.play()
	return inp



#===GAME CMDS===#
def get_item_def(name):	#Gets the dictionary definition of an item (effect, name, etc)
	for entry in items:
		if entry["name"].lower() == name.lower():
			return entry
	return None  # not found
def get_item_defh(name):	#Gets the dictionary definition of an item in readable form (Utility)
	clear()
	entry = get_item_def(name)
	if entry:
		dialogueanim(f"Name: {entry['name']}")
		dialogueanim(f"Effect: {entry['effect']}")
	else:
		error("Item not found.")
	inputb("\nPress Enter to return.")
	clear()

def heal(amnt):	#Heals the player by a specified amount, can use negative values temporarily to damage the player
	global hp #use the global hp, since we are in a function.
	clear()

	if amnt == 0:
		no.play()
		error("Nothing happened.")
		clear()
		return True
	elif hp == 100 and amnt > 0:
		no.play()
		error("You are already fully healed.")
		clear()
		return False
	else:
		if amnt > 0:
			if amnt <= 10:
				heart.play()
				dialogueanim("You feel a little better.")
			elif amnt <= 25:
				heart.play()
				dialogueanim("You feel better.")
			elif amnt <= 50:
				heart.play()
				dialogueanim("You feel a lot better.")
			elif amnt <= 100:
				heart.play()
				dialogueanim("What kind of drugs did you just take??")
		elif amnt < 0:
			hurt.play()
			dialogueanim(f"A mysterious force caused you to take {-amnt} damage.")
		hp += amnt
		if hp > 100:
			hp = 100
			heart.play()
			dialogueanim("You are fully healed!")
		elif hp <= 0:
			hp = 0
			hurt.play()
			dialogueanim("You have taken fatal damage...")

	time.sleep(2)
	clear()
	return True

def dmg(amnt, cause):	#Damages the player ^^^
	global hp
	clear()
	if amnt == 0:
		no.play()
		error(f"{cause} tried to damage you! Nothing happened.")
		clear()
		return True
	elif hp == 100 and amnt < 0:
		no.play()
		error("You are already fully healed.")
		clear()
		return False
	else:
		if amnt > 0:
			if amnt <= 10:
				hurt.play()
				dialogueanim(f"You have been wounded by {cause}, -{amnt} HP!")
			elif amnt <= 25:
				hurt.play()
				dialogueanim(f"You have been injured by {cause}, -{amnt} HP!")
			elif amnt <= 50:
				hurt.play()
				dialogueanim(f"You have been heavily injured by {cause}, -{amnt} HP!")
			elif amnt <= 100:
				hurt.play()
				dialogueanim(f"You have been fatally injured by {cause}, -{amnt} HP!")
		elif amnt < 0:
			heart.play()
			dialogueanim(f"A {cause} caused you to heal {-amnt} HP.")
		hp -= amnt
		print()
		if hp > 100:
			hp = 100
			hurt.play()
			dialogueanim("You are fully healed!")
		elif hp <= 0:
			hp = 0
			hurt.play()
			dialogueanim("You have taken fatal damage...")
	time.sleep(2)
	clear()
	return True

def savegame():	#Saves the current player data and inventory data to file
	dat[0] = str(lvl)
	dat[1] = str(hp)
	dat[2] = str(df)
	with open('inv.json', 'w') as file:
		with open('inv.json', 'w') as f:
			json.dump(inv, f)
	with open('data.txt', 'w') as file:
		for item in dat:
			file.write(item + '\n')

def manageitem(item, action, info=False):
	try:
		global inv
		if action == 'delete':
			clear()
			inv.remove(item)
			if info == True:
				dialogueanim(f'Deleted {item}.')
				time.sleep(1)
		elif action == 'drop':
			clear()
			inv.remove(item)
			dialogueanim(f'Dropped {item}.')
			time.sleep(1)
			#code to put dropped item at coordinate as loot
		elif action == 'use':
			clear()
			defn = get_item_def(item)
			remove = True  # assume item should be removed

			if defn:
				if defn.get("effect", "") == None:
					remove = False
				else:
					effect = defn.get("effect", "")
				try:
					# Attempt to evaluate the effect and get the return value
					result = eval(effect, {"heal": heal})
					if isinstance(result, bool):
						remove = result
				except Exception as e:
					remove = False
					error(f'Error using item: {e}')
					time.sleep(1)
			else:
				dialogueanim(f'You used the {item}. Nothing happened')
				time.sleep(1)

			if remove:
				inv.remove(item)
		elif action == 'duplicate':
			clear()
			inv.append(item)
			if info == True:
				dialogueanim(f'Duplicated {item}.')
				time.sleep(1)
	except Exception as e:
		error(e)

def collect(item, num):	#adds item(s) to the inventory (attempts to)
	clear()
	if num <= 0:
		error("Invalid item count.")
		return
	dialogueanim(f'You found {num} {item}s!')
	time.sleep(1)
	clear()
	#repeat how much items the player recieved of such type
	for _ in range(num):
			inv.append(item)
	#sync
	with open('items.txt', 'w') as file:
		for item in inv:
			file.write(item + '\n')

def resetValues():
    global lvl, hp, df, inv, dat

    # Reset variables
    lvl = 0
    hp = 100
    df = 0
    inv = []

    # Initialize dat to hold the default values
    dat = [str(lvl), str(hp), str(df)]

    # Clear items.txt
    with open('inv.json', 'w') as f:
        json.dump('[]', f, indent=2)

    # Write base data to data.txt
    with open('data.txt', 'w') as file:
        for item in dat:
            file.write(item + '\n')

    # Write default items to items.json
    items_data = [
        {"name": "Potion", "effect": "heal(10)"},
        {"name": "GreaterPotion", "effect": "heal(50)"},
        {"name": "Drugs", "effect": "heal(100)"}
    ]
    with open('items.json', 'w') as f:
        json.dump(items_data, f, indent=2)

    # Write default enemies to enemies.json
    enemies_data = [
        {"name": "Goblin", "hp": 30, "min_level": 1, "damage": 5},
        {"name": "Orc", "hp": 50, "min_level": 3, "damage": 10},
        {"name": "Dragon", "hp": 200, "min_level": 10, "damage": 30}
    ]
    with open('enemies.json', 'w') as f:
        json.dump(enemies_data, f, indent=2)

#===OLD STUFF===#

def viewinventory():	#old viewinventory()
	clear()
	if not inv:
		error('No items in inventory')
		return '0'
	for i, item in enumerate(inv):
		print(f'{i + 1}. {item}')
	print("0. Back")
	response = input(':')
	if response == '0':
		clear()
		return '0'
	elif response.isdigit():
		index = int(response) - 1
		if 0 <= index < len(inv):
			manageitem(inv[index], 'use')
			return '2'
		else:
			error('Invalid selection')
			return '2'
	else:
		error('Please enter a valid input.')
		return '2'

def viewstats():	#old viewstats()
	clear()
	print("NAME: Mark Fischbach")
	print(f"LEVEL: {lvl}")
	print(f"HP: {hp}")
	print(f"DEF: {df}")
	print("0. Back")
	response = input(": ")
	if response == '0':
		clear()
		return '0'
	else:
		error('Invalid selection')
		return '3'

def gameover():	#old gameover()
	global lvl, hp, df, inv
	clear()
	print('Game Over!')
	print(f'You died on level {lvl} with a total of {df} defense and {len(inv)} item(s).')
	time.sleep(2)
	resetValues()
	# Reset stats and inventory
	
	quit()

def helpbase():	#old helpbase()
	clear()
	print('''=== HELP MENU ===

Main Menu Options:

	1 - Explore the dungeon
	2 - View and use items in your inventory
	3 - View player statistics
	4 - Exit and save the game

Extra Commands (Not Reccomended for Casual Gameplay):

	d - Take 50 damage instantly (debug/test)
	r - Reset all stats and inventory
	e - View all enemies from enemies.json
	i - View all items and their effects from items.json
	cmd - Run  raw Python code (advanced/debug)

	-Try 'helpcmd()' in the cmd prompt if unsure.
''')
	input('Press Enter to return.')
	clear()




#===LOAD DATA===#

#		-Loads the saved game in the form of lists or dicts,
#		then sets the usr stats.

def loaddata():
	global lvl, hp, df, dat, inv, enemies, items
	try:
		with open('inv.json') as file:
			inv = json.load(file)
		with open('data.txt') as file:
			dat = [line.strip() for line in file if line.strip()]
		with open('enemies.json') as file:
			enemies = json.load(file)
		with open('items.json') as file:
			items = json.load(file)
	except Exception as e:
		createfiles()
def createfiles():
	error('One or more files doesnt exist or is damaged, resetting.')
	with open('inv.json', 'w') as f:
		pass
	with open('data.txt', 'w') as f:
		pass
	with open('enemies.json', 'w') as f:
		pass
	with open('items.json', 'w') as f:
		pass
	resetValues()
	loaddata()
loaddata()
lvl = int(dat[0])
hp = int(dat[1])
df = int(dat[2])



#===HELP STUFF===#
def debughelp():
	clear()
	dialogueanim("""
=== DEBUG/DEV HELP ===
These are callable from the 'cmd' prompt (advanced users only):

=== SOUNDS/AUDIO NAMES ===

select, dialogue, hurt, heart, no
  → just add .play()/.stop() to play or stop these (e.g. select.play())

pygame.mixer.music.load("dungeon.ogg")
  → This ones different, it loads at the beginning of the game, so to load another song replace the path to a new one. to play/stop the music, do pygame.mixer.music.play/stop() and if you want it to play forever until stopped, do pygame.mixer.music.play(-1)

=== SYSTEM CMDS ===

clear()
  → Clears the terminal screen.

clear_previous_lines()
  → Clears the previous lines generated by dialogueanim

dialogueanim(string, color, on_color, attrs, mul)
  → prints things but cooler, also supports every variation of color/attributes (research termcolor for more info) mul is how fast it goes, default is 2.

error(msg)
  → prints out an error message of your choice in red text.

inputb()
  → Same as input() except it makes the select sound after the user presses enter.

inputm()
  → checks for keypresses, util

loaddata()
  → Attempts to load file data, if failed, it calls createfiles()

createfiles()
  → creates all necessary data files and resets them, then calls loaddata() to load it.

=== IN GAME CMDS ===

heal(amount)
  → Heals the player by given amount. Returns False if already at 100 HP.

dmg(amount, cause)
  → Damages the player with a cause, if negative then it heals the player.

collect(item, number)
  → Adds [number] of [item] to your inventory.

use_item(item)
  → Uses the given item name manually, like the inventory system would.

resetValues()
  → Resets all stats, inventory, and game state to default.

savegame()
  → Saves current HP, level, defense, and inventory to disk.

get_item_def(name)
  → Looks up an item’s definition from items.json (UTIL)

get_item_defh(name)
  → Looks up an item’s definition from items.json by name.

=== VARIABLES ===
These arent really commands, but are still cheating.

state = string
  → Sets the game state

hp, lvl, df = integer
  → Health, Level, Defense

dat, inv = list
  → Save data

enemies, items = dictionary/json
  → A dictionary of all the in game enemies/items you can encounter.

=== DEPRECATED STUFF ===

viewinventory()
  → Loads the old inventory screen, i believe it only works if you type 'state = viewinventory()'

viewstats()
  → Same as viewinventory(), but for stats. only works if you type 'state = viewstats()'

gameover()
  → The old gameover screen, closes the game afterwards.

helpbase()
  → Shows the old help screen

Note:
- Integers (numbers) should be entered without quotes, e.g. 10
	*if you are trying to set the game state (e.g. state = gamestate) set it to a string, not an integer.
- Strings (text) must be entered with quotes, e.g. 'Potion'
	* Item names are case sensitive! Dont use "potion" use "Potion"
- Lists are should be entered like this: ['item', 10, variable]
- Booleans have the first letter capitalized (False, True)
""", 'green')
	inputb("Press Enter to return.")
	clear()
#print("\033[91mYou took damage!\033[0m")  # red text

colors = [31, 32, 33, 34, 35, 36]
text = "--MARKDUNGEON----MARKDUNGEON----MARKDUNGEON----MARKDUNGEON--"
s = ""

for i, char in enumerate(text):
    s += f"\033[{colors[i % len(colors)]}m{char}\033[0m"

dialogueanim(s)


#===START GAME===#
def startgame():
	global state
	state = '0'
	dialogueanim('Welcome to the dungeon...')
	time.sleep(2)
	print()
	dialogueanim('Good luck!')
	#dialogueanim('this is animated red text!', 'red', attrs=['underline', 'bold'])
	time.sleep(1)
	clear()

clear()

startgame()

while True:
	if pygame.mixer.music.get_busy() == False:
		pygame.mixer.music.play(-1)
	if hp <= 0:
		state = 'gameover'
	#===GAME STATES===#
	if state == '0':
		dialogueanim('''=== MARK DUNGEON BETA V0.0.3 ===

	1. Explore
	2. Inventory
	3. Statistics

Type 'help' for help.
Type 'exit' to save and quit.
''')
		response = inputb(':')
		if response.lower() in ('1', '2', '3', 'help', 'exit', 'd', 'r', 'e', 'i', 'cmd'):
			state = response
		else:
			error('Please enter a valid input.')
	elif state == '1':	#Explore
		pygame.mixer.music.stop()
		error('This part of the game is unfinished!')
		state = '0'
	elif state == '2':	#Inventory
		clear()
		invstring = ''
		if not inv:
			state = '0'
		invstring = invstring + '''=== Inventory ===
'''
		for i, item in enumerate(inv):
			invstring += f'\n	{i + 1}. {inv.get("amnt")} {item}s'
			invstring += "\n"
		invstring += '''\nPress Enter to go back.
'''
		dialogueanim(invstring)
		response = inputb(': ')
		if response == '':
			clear()
			state = '0'
		elif response == 'drop':
			response = inputb('Item? : ')
			if response.isdigit():
				index = int(response) - 1
				if 0 <= index < len(inv):
					manageitem(inv[index], 'drop')
					state = '2'
		elif response.isdigit():
			index = int(response) - 1
			if 0 <= index < len(inv):
				item(inv[index], 'use')
				state = '2'
			else:
				error('Invalid selection')
				state = '2'
		else:
			error('Please enter a valid input.')
			state = '2'
	elif state == '3':	#Statistics
		clear()
		dialogueanim(f"""=== STATISTICS ===

	NAME: Mark Fischbach

	LEVEL: {lvl}

	HP: {hp}

	DEF: {df}

Press Enter to go back.

""")
		response = inputb(": ")
		if response == '':
			clear()
			state = '0'
		else:
			error('Invalid selection')
			state = '3'
	elif state == 'help':	#Help
		clear()
		dialogueanim('''=== HELP MENU ===

Main Menu Options:

	1 - Explore the dungeon
	2 - View and use items in your inventory
	3 - View player statistics
	4 - Exit and save the game

Extra Commands (Not Reccomended for Casual Gameplay):

	d - Take 50 damage instantly (debug/test)
	r - Reset all stats and inventory
	e - View all enemies from enemies.json
	i - View all items and their effects from items.json
	cmd - Run  raw Python code (advanced/debug)

	-Try 'debughelp()' in the cmd prompt if unsure.
''', 'green')
		inputb('Press Enter to return.')
		clear()
		state = '0'
	elif state == 'exit':	#Exit
		pygame.mixer.music.stop()
		clear()
		print('Saving game...')
		savegame()
		print('Game saved!')
		dialogueanim('Exiting...')
		print()
		time.sleep(3)
		dialogueanim('goodbye.', 'red', attrs=['bold', 'dark'])
		time.sleep(0.5)
		exit()
		
		
		
	#===QUICK CMDS===#
	elif state == 'd':	#Damage (50)
		clear()
		dmg(50, 'Mysterious Force')
		clear()
		state = '0'
	elif state == 'r':	#Reset Values
		clear()
		dialogueanim('Resetting all values...')
		resetValues()
		time.sleep(1)
		dialogueanim('Done!')
		time.sleep(1)
		clear()
		state = '0'
	elif state == 'e':	#View Enemies
		clear()
		for enemy in enemies:
			print(f"Enemy: {enemy['name']}")
			print(f"HP: {enemy['hp']}")
			print(f"Level: {enemy['min_level']}")
			print(f"Damage: {enemy['damage']}")
			print('---')
			time.sleep(0.025)
		inputb('Press Enter to return.')
		clear()
		state = '0'
	elif state == 'i':	#View Items
		clear()
		for item in items:
			print(f"Name: {item['name']}")
			print(f"Effect: {item['effect']}")
			print('---')
			time.sleep(0.025)
		inputb('Press Enter to return.')
		clear()
		state = '0'
	#===REAL CMDS===#
	elif state == 'cmd':	#Execute Python code
		dialogueanim('''Enter your Python code (end with an empty line):''')
		lines = []

		while True:
			line = input()  # Read one line of input from the user
			if line.strip() == '':  # If the line is empty (just whitespace), end input
				break  # Exit the loop since input is finished
			lines.append(line)  # Otherwise, add the line to the list

		code = "\n".join(lines)  # Join all the lines into a single string separated by newlines

		try:
			exec(code)  # Execute the entire block of code as Python code
		except Exception as e:
			error(str(e))  # If there's an error, print it without crashing the game
		clear()  # Clear the screen to keep UI tidy
		state = '0'  # Return to main menu state
	elif state == 'gameover':	#Game over
		clear()
		pygame.mixer.music.stop()
		dialogueanim('Game Over!')
		print()
		dialogueanim(f'You died on level {lvl} with a total of {df} defense and {len(inv)} item(s).')
		time.sleep(2)
		resetValues()	# Reset stats and inventory
		clear()
		startgame()



	#===Auto sync in case force close===#
	savegame()


