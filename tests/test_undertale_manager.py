"""Unit tests for UNDERTALE Save Manager."""

import json
from pathlib import Path
from unittest.mock import patch

from undertale_manager import (
	ROOM_IDS,
	Save,
	backup_save,
	list_backups,
	load_config,
	load_save,
	save_config,
)
from undertale_manager import __version__


def test_version():
	"""Test that version is correctly set."""
	assert __version__ == "1.0.0"


# Config Tests

def test_load_config_existing_file(tmp_path):
	"""Test loading config from existing file."""
	config_file = tmp_path / "config.json"
	test_config = {"backup_dir": "/test/path"}
	config_file.write_text(json.dumps(test_config))

	with patch("undertale_manager.CONFIG_FILE", config_file):
		result = load_config()
		assert result == test_config


def test_load_config_missing_file():
	"""Test loading config when file doesn't exist."""
	with patch("undertale_manager.CONFIG_FILE", Path("/nonexistent/config.json")):
		result = load_config()
		assert result == {}


def test_load_config_invalid_json(tmp_path):
	"""Test loading config with invalid JSON."""
	config_file = tmp_path / "config.json"
	config_file.write_text("invalid json{")

	with patch("undertale_manager.CONFIG_FILE", config_file):
		result = load_config()
		assert result == {}


def test_save_config(tmp_path):
	"""Test saving config to file."""
	config_file = tmp_path / "config.json"
	test_config = {"backup_dir": "/test/path", "setting": "value"}

	with patch("undertale_manager.CONFIG_FILE", config_file):
		save_config(test_config)

		assert config_file.exists()
		loaded = json.loads(config_file.read_text())
		assert loaded == test_config


def test_save_config_creates_directory(tmp_path):
	"""Test that save_config creates parent directory."""
	config_file = tmp_path / "nested" / "dirs" / "config.json"
	test_config = {"key": "value"}

	with patch("undertale_manager.CONFIG_FILE", config_file):
		save_config(test_config)

		assert config_file.parent.exists()
		assert config_file.exists()


# Save Class Tests

def test_save_invalid_empty_save(tmp_path):
	"""Test Save object with empty/missing save file."""
	empty_dir = tmp_path / "empty_save"
	empty_dir.mkdir()

	save = Save(empty_dir)

	assert save.TITLE == "empty_save"
	assert save.NAME == "(Empty Save)"
	assert save.FUN == "N/A"
	assert save.LOVE == "N/A"
	assert save.HP == "N/A"
	assert save.GOLD == "N/A"
	assert save.EXP == "N/A"
	assert save.kills == "N/A"
	assert save.room_id == "N/A"
	assert save.is_valid() is False


def test_save_valid_save_file(tmp_path):
	"""Test Save object with valid save file."""
	save_dir = tmp_path / "valid_save"
	save_dir.mkdir()

	# Create mock save data (548+ lines)
	save_data = ["Frisk"] + ["0"] * 600
	save_data[1] = "5"  # LOVE
	save_data[2] = "20"  # HP
	save_data[9] = "100"  # EXP
	save_data[10] = "500"  # GOLD
	save_data[11] = "10"  # kills
	save_data[35] = "50"  # FUN
	save_data[251] = "0"  # genocide_ruins
	save_data[252] = "0"  # genocide_snowdin
	save_data[253] = "0"  # genocide_waterfall
	save_data[254] = "0"  # genocide_hotland
	save_data[510] = "0"  # genocide flag
	save_data[547] = "4"  # room_id (Beginning in RUINS)
	save_data[548] = "900"  # playtime (30 seconds)

	file0 = save_dir / "file0"
	file0.write_text("\n".join(save_data))

	save = Save(save_dir)

	assert save.TITLE == "valid_save"
	assert save.NAME == "Frisk"
	assert save.LOVE == "5"
	assert save.HP == "20"
	assert save.GOLD == "500"
	assert save.EXP == "100"
	assert save.kills == "10"
	assert save.FUN == "50"
	assert save.room_id == "4"
	assert save.room_name == "Beginning"
	assert save.room_area == "RUINS"
	assert save.is_valid() is True


def test_save_genocide_detection_ruins(tmp_path):
	"""Test genocide route detection in RUINS."""
	save_dir = tmp_path / "genocide_save"
	save_dir.mkdir()

	save_data = ["Chara"] + ["0"] * 600
	save_data[1] = "10"
	save_data[251] = "1"  # genocide_ruins flag
	save_data[510] = "0"
	save_data[547] = "4"  # RUINS
	save_data[548] = "0"

	file0 = save_dir / "file0"
	file0.write_text("\n".join(save_data))

	save = Save(save_dir)

	assert save.genocide is True


def test_save_non_genocide_route(tmp_path):
	"""Test non-genocide (pacifist/neutral) route detection."""
	save_dir = tmp_path / "pacifist_save"
	save_dir.mkdir()

	save_data = ["Frisk"] + ["0"] * 600
	save_data[1] = "1"  # LOVE 1
	save_data[11] = "0"  # No kills
	save_data[251] = "0"
	save_data[510] = "0"
	save_data[547] = "4"
	save_data[548] = "0"

	file0 = save_dir / "file0"
	file0.write_text("\n".join(save_data))

	save = Save(save_dir)

	assert save.genocide is False


def test_save_repr(tmp_path):
	"""Test Save string representation."""
	save_dir = tmp_path / "test_save"
	save_dir.mkdir()

	save_data = ["TestName"] + ["0"] * 600
	save_data[1] = "3"
	save_data[2] = "25"
	save_data[9] = "50"
	save_data[10] = "250"
	save_data[11] = "5"
	save_data[35] = "75"
	save_data[547] = "10"
	save_data[548] = "0"

	file0 = save_dir / "file0"
	file0.write_text("\n".join(save_data))

	save = Save(save_dir)
	repr_str = repr(save)

	assert "TestName" in repr_str
	assert "LOVE: 3" in repr_str
	assert "HP: 25" in repr_str
	assert "GOLD: 250" in repr_str
	assert "EXP: 50" in repr_str
	assert "Kills: 5" in repr_str
	assert "FUN: 75" in repr_str


# Backup Management Tests

def test_list_backups(tmp_path):
	"""Test listing backup directories."""
	backup_dir = tmp_path / "backups"
	backup_dir.mkdir()

	# Create some backup directories
	(backup_dir / "backup1").mkdir()
	(backup_dir / "backup2").mkdir()
	(backup_dir / "backup3").mkdir()

	# Create a file (should be ignored)
	(backup_dir / "not_a_backup.txt").write_text("test")

	backups = list_backups(backup_dir)

	assert len(backups) == 3
	backup_names = [b.name for b in backups]
	assert "backup1" in backup_names
	assert "backup2" in backup_names
	assert "backup3" in backup_names


def test_list_backups_empty_directory(tmp_path):
	"""Test listing backups in empty directory."""
	backup_dir = tmp_path / "empty_backups"
	backup_dir.mkdir()

	backups = list_backups(backup_dir)

	assert len(backups) == 0


def test_backup_save(tmp_path, capsys):
	"""Test creating a backup of game save."""
	game_save_dir = tmp_path / "game_save"
	game_save_dir.mkdir()
	(game_save_dir / "file0").write_text("save data")
	(game_save_dir / "undertale.ini").write_text("config")

	backup_dir = tmp_path / "backups"
	backup_dir.mkdir()

	with patch("undertale_manager.GAME_SAVE_DIR", game_save_dir):
		backup_save("test_backup", backup_dir)

	backup_path = backup_dir / "test_backup"
	assert backup_path.exists()
	assert (backup_path / "file0").exists()
	assert (backup_path / "undertale.ini").exists()

	captured = capsys.readouterr()
	assert "Backup 'test_backup' created" in captured.out


def test_backup_save_with_rm(tmp_path, capsys):
	"""Test creating a backup and removing original."""
	game_save_dir = tmp_path / "game_save"
	game_save_dir.mkdir()
	(game_save_dir / "file0").write_text("save data")
	(game_save_dir / "undertale.ini").write_text("config")

	backup_dir = tmp_path / "backups"
	backup_dir.mkdir()

	with patch("undertale_manager.GAME_SAVE_DIR", game_save_dir):
		backup_save("test_backup", backup_dir, rm=True)

	# Backup should exist
	backup_path = backup_dir / "test_backup"
	assert backup_path.exists()
	assert (backup_path / "file0").exists()

	# Original should be empty
	assert not (game_save_dir / "file0").exists()
	assert not (game_save_dir / "undertale.ini").exists()


def test_load_save(tmp_path, capsys):
	"""Test loading a save from backup."""
	backup_path = tmp_path / "backups" / "test_backup"
	backup_path.mkdir(parents=True)
	(backup_path / "file0").write_text("backup save data")
	(backup_path / "file9").write_text("system info")

	game_save_dir = tmp_path / "game_save"
	game_save_dir.mkdir()

	with patch("undertale_manager.GAME_SAVE_DIR", game_save_dir):
		load_save(backup_path)

	assert (game_save_dir / "file0").exists()
	assert (game_save_dir / "file9").exists()
	assert (game_save_dir / "file0").read_text() == "backup save data"

	captured = capsys.readouterr()
	assert "Backup 'test_backup' loaded" in captured.out


def test_load_save_nonexistent(tmp_path, capsys):
	"""Test loading from non-existent backup."""
	backup_path = tmp_path / "backups" / "nonexistent"
	game_save_dir = tmp_path / "game_save"
	game_save_dir.mkdir()

	with patch("undertale_manager.GAME_SAVE_DIR", game_save_dir):
		load_save(backup_path)

	captured = capsys.readouterr()
	assert "does not exist" in captured.out


def test_load_save_existing_save_without_rm(tmp_path, capsys):
	"""Test loading backup when current save exists without rm flag."""
	backup_path = tmp_path / "backups" / "test_backup"
	backup_path.mkdir(parents=True)
	(backup_path / "file0").write_text("backup save data")

	game_save_dir = tmp_path / "game_save"
	game_save_dir.mkdir()
	(game_save_dir / "file0").write_text("current save")

	with patch("undertale_manager.GAME_SAVE_DIR", game_save_dir):
		load_save(backup_path, rm=False)

	# Original should remain unchanged
	assert (game_save_dir / "file0").read_text() == "current save"

	captured = capsys.readouterr()
	assert "Current save exists" in captured.out


def test_load_save_existing_save_with_rm(tmp_path, capsys):
	"""Test loading backup when current save exists with rm flag."""
	backup_path = tmp_path / "backups" / "test_backup"
	backup_path.mkdir(parents=True)
	(backup_path / "file0").write_text("backup save data")

	game_save_dir = tmp_path / "game_save"
	game_save_dir.mkdir()
	(game_save_dir / "file0").write_text("current save")
	(game_save_dir / "old_file").write_text("old data")

	with patch("undertale_manager.GAME_SAVE_DIR", game_save_dir):
		load_save(backup_path, rm=True)

	# Old files should be removed and new ones loaded
	assert (game_save_dir / "file0").read_text() == "backup save data"
	assert not (game_save_dir / "old_file").exists()

	captured = capsys.readouterr()
	assert "Backup 'test_backup' loaded" in captured.out


# Room IDs Tests

def test_room_ids_structure():
	"""Test that ROOM_IDS has expected structure."""
	assert isinstance(ROOM_IDS, list)
	assert len(ROOM_IDS) > 0

	# Check first few entries
	assert ROOM_IDS[0]["id"] == "0"
	assert ROOM_IDS[0]["area"] == "ERROR"
	assert ROOM_IDS[4]["area"] == "RUINS"
	assert ROOM_IDS[4]["name"] == "Beginning"


def test_room_ids_lookup():
	"""Test looking up room information by ID."""
	# Beginning room
	room = ROOM_IDS[4]
	assert room["name"] == "Beginning"
	assert room["area"] == "RUINS"

	# Error room
	room = ROOM_IDS[0]
	assert room["area"] == "ERROR"
