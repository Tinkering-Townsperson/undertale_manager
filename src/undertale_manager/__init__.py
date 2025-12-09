"""UNDERTALE Save Manager - Manage multiple UNDERTALE save files!

This module provides utilities for:
- Loading and parsing UNDERTALE save files
- Creating and managing save backups
- Looking up room information from save data
- Configuration management for backup directory preferences

Classes:
	Save: Represents a single UNDERTALE save file with parsed metadata.

Functions:
	load_config: Load configuration from disk.
	save_config: Save configuration to disk.
	list_backups: List all backup directories.
	backup_save: Create a backup of the current game save.
	load_save: Load a save from a backup.
"""

__version__ = "1.0.0"

###########
# IMPORTS #
###########


import json
import os
import shutil  # noqa
from datetime import timedelta
from pathlib import Path

from undertale_manager.ids import ROOM_IDS  # noqa


#############################
# CONFIG AND SAVE DIR SETUP #
#############################

	GAME_SAVE_DIR = Path(os.getenv("LOCALAPPDATA")) / "UNDERTALE"
	CONFIG_FILE = Path(os.getenv("LOCALAPPDATA")) / "undertale_manager" / "config.json"
else:
	# TODO: Implement config and save dir for non-Windows OSes 😬
	exit("Unsupported OS")


def load_config() -> dict:
	"""Load configuration from file."""
	if CONFIG_FILE.exists():
		try:
			with CONFIG_FILE.open("r") as f:
				return json.load(f)
		except Exception:
			pass
	return {}


def save_config(config: dict) -> None:
	"""Save configuration to file."""
	CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
	try:
		with CONFIG_FILE.open("w") as f:
			json.dump(config, f, indent=2)
	except Exception:
		pass


############################################
# SAVE CLASS AND SAVE MANAGEMENT FUNCTIONS #
############################################

class Save:
	"""Object for save files.
	Try to process the `file0` file that is usually found in the game save folder.
	"""
	def __init__(self, dir_path: os.PathLike):
		self.path = Path(dir_path).resolve()
		self.TITLE = self.path.name

		# Return early if the save file isn't there 🤡
		if not self.is_valid():
			self.NAME = "(Empty Save)"
			self.FUN = "N/A"
			self.LOVE = "N/A"
			self.HP = "N/A"
			self.GOLD = "N/A"
			self.EXP = "N/A"
			self.kills = "N/A"
			self.room_id = "N/A"
			self.room_name = "N/A"
			self.room_area = "N/A"
			self.genocide = "N/A"
			self.data = []
			return

		with (self.path / "file0").open() as save_file:
			data = save_file.readlines()

		self.NAME = data[0].strip()
		self.FUN = data[35].strip()
		self.LOVE = data[1].strip()
		self.HP = data[2].strip()
		self.GOLD = data[10].strip()
		self.EXP = data[9].strip()
		self.kills = data[11].strip()
		self.room_id = data[547].strip()
		self.room_name = ROOM_IDS[int(self.room_id)].get("name", "")
		self.room_area = ROOM_IDS[int(self.room_id)].get("area", "")
		self.playtime = timedelta(seconds=round(int(data[548].strip())/30))
		self.data = data

		match self.room_area.lower():
			case "error":
				current_area = 0
			case "ruins":
				current_area = 1
			case "snowdin":
				current_area = 2
			case "waterfall":
				current_area = 3
			case "hotland":
				current_area = 4
			case "core":
				current_area = 5
			case "new home":
				current_area = 6
			case _:
				current_area = 7

		genocide_areas = []

		if current_area >= 1:
			genocide_areas.append(True if data[251].strip() == "1" else False)
		if current_area >= 2:
			genocide_areas.append(True if data[252].strip() == "1" else False)
		if current_area >= 3:
			genocide_areas.append(True if data[253].strip() == "1" else False)
		if current_area >= 4:
			genocide_areas.append(True if data[254].strip() == "1" or data[255].strip() == "1" else False)
		if current_area >= 6:
			genocide_areas.append(int(self.LOVE) >= 19)

		self.genocide = all(genocide_areas) or data[510].strip() == "1"

	def is_valid(self) -> bool:
		"""Check if this save has valid data (not empty)."""
		return (self.path / "file0").exists()

	def __repr__(self):
		return f"""{self.NAME}
>	LOVE: {self.LOVE}
>	EXP: {self.EXP}
>	GOLD: {self.GOLD}
>	HP: {self.HP}
>	Kills: {self.kills}
>	Room: {self.room_area}/{self.room_name} (#{self.room_id})
>	FUN: {self.FUN}"""


def list_backups(backup_dir: Path):
	"""List all backup directories in the given backup directory."""
	backup_dir = Path(backup_dir)
	return [f for f in backup_dir.iterdir() if f.is_dir()]


def backup_save(name, backup_dir: Path, rm=False):
	"""Create a backup of the current game save."""
	backup_path = Path(backup_dir) / name
	backup_path.mkdir(parents=True, exist_ok=True)

	shutil.copytree(GAME_SAVE_DIR, backup_path, dirs_exist_ok=True)

	if rm:
		for item in GAME_SAVE_DIR.iterdir():
			if item.is_dir():
				shutil.rmtree(item)
			else:
				item.unlink()

	print(f"Backup '{name}' created.")


def load_save(path: os.PathLike, rm=False):
	"""Load a save from a backup directory."""
	path = Path(path).resolve()

	if not path.exists():
		print(f"Backup '{path.name}' does not exist.")
		return

	if (GAME_SAVE_DIR / "file0").exists() or (GAME_SAVE_DIR / "file9").exists() or (GAME_SAVE_DIR / "undertale.ini").exists():
		if rm:
			for item in GAME_SAVE_DIR.iterdir():
				if item.is_dir():
					shutil.rmtree(item)
				else:
					item.unlink()
		else:
			print("Current save exists. Use rm=True to overwrite.")
			return

	for item in path.iterdir():
		if item.is_dir():
			shutil.copytree(item, GAME_SAVE_DIR / item.name, dirs_exist_ok=True)
		else:
			shutil.copy(item, GAME_SAVE_DIR / item.name)

	print(f"Backup '{path.name}' loaded.")


# The following code was used for testing the logic and stuff before I made the TUI using Textual.

"""def mainloop(backup_dir: os.PathLike):
	backs = list_backups(Path(backup_dir).resolve())
	print(f"Found {len(backs)} backups:")

	for (i, backup) in enumerate(backs):
		print(f"{i}. {backup.name}")

	choice = int(input("Select a backup to view: "))

	if choice < 0 or choice >= len(backs):
		print("Invalid choice.")
		return

	selected_backup = backs[choice]
	save = Save(selected_backup)
	print(save)"""
