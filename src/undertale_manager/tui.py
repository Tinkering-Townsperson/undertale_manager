"""Textual TUI for UNDERTALE Manager.

## NOTE:
This file has quite a bit of AI-generated code. I used GitHub Copilot to help speed up the development and fix bugs.
"""

###########
# IMPORTS #
###########

from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Footer, Header, Input, Label, ListItem, ListView, Static, Rule

from undertale_manager import GAME_SAVE_DIR, Save, __version__, backup_save, list_backups, load_config, load_save, save_config # noqa


#############
# APP CLASS #
#############

class UndertaleManagerApp(App):
	CSS_PATH = "undertale_manager.tcss"
	TITLE = f"UNDERTALE Manager v{__version__}"

	def __init__(self, backup_dir: Optional[PathLike] = None):
		super().__init__()
		if backup_dir:
			self.backup_dir = Path(backup_dir).resolve()
		else:
			config = load_config()
			if "backup_dir" in config:
				self.backup_dir = Path(config["backup_dir"]).resolve()
			else:
				self.backup_dir = None

	def compose(self) -> ComposeResult:
		yield Header()
		if self.backup_dir:
			yield SaveListView(self.backup_dir)
		yield Rule()
		yield Horizontal(
			Button("Quit", id="quit", variant="error"),
			Button("Refresh", id="refresh", variant="primary"),
			Button("Change Directory", id="change-dir", variant="primary"),
			Button("Backup Current Save", id="backup", variant="success"),
			id="main-buttons",
		)
		yield Footer()

	async def on_mount(self) -> None:
		"""Show directory chooser if no backup_dir set."""
		if not self.backup_dir:
			self.run_worker(self.choose_directory())

	async def choose_directory(self) -> None:
		"""Show directory chooser and update backup_dir."""
		default = self.backup_dir or Path.home()
		result = await self.push_screen_wait(BackupDirectoryScreen(default))
		if result:
			self.backup_dir = result
			# Save to config
			config = load_config()
			config["backup_dir"] = str(self.backup_dir)
			save_config(config)
			self.notify(f"Backup directory: {self.backup_dir.name}", severity="information")
			self.refresh_save_list()
		elif not self.backup_dir:
			# No directory selected and none set, exit
			self.exit()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "quit":
			self.exit()
		elif event.button.id == "backup":
			if not self.backup_dir:
				self.notify("Select a backup directory first.", severity="warning")
				return
			current_save = Save(GAME_SAVE_DIR)
			if not current_save.is_valid():
				self.notify("Current save is empty; nothing to back up.", severity="warning")
				return  # Don't backup empty saves
			self.push_screen(BackupNameScreen(current_save, rm=False))
		elif event.button.id == "refresh":
			if not self.backup_dir:
				return
			self.refresh_save_list()
			self.notify("Refreshed save list.", severity="information")
		elif event.button.id == "change-dir":
			self.run_worker(self.choose_directory())

	def refresh_save_list(self) -> None:
		if not self.backup_dir:
			return
		try:
			save_list_view = self.query_one(SaveListView)
			save_list_view.clear()
		except Exception:
			# No SaveListView yet, mount it
			self.mount(SaveListView(self.backup_dir), before="#main-buttons")
			return
		for save in list_backups(self.backup_dir):
			save_list_view.append(SaveWidget(Save(save)))


#############################
# EXTRA SCREENS AND WIDGETS #
#############################

class BackupDirectoryScreen(ModalScreen[Path]):
	"""Screen to choose the backup directory."""

	BINDINGS = [("escape", "dismiss", "Cancel")]

	def __init__(self, default_path: Path | None = None):
		super().__init__()
		self.default_path = default_path or Path.home()

	def compose(self) -> ComposeResult:
		yield Header()
		yield Vertical(
			Label("Select backup directory:", id="directory-label"),
			Input(placeholder="Enter directory path", id="directory-input", value=str(self.default_path)),
			DirectoryTree(str(self.default_path), id="directory-tree"),
			Horizontal(
				Button("Cancel", id="cancel", variant="error"),
				Button("Select", id="select", variant="success"),
				id="directory-actions",
			),
			id="directory-body",
		)
		yield Footer()

	def on_directory_tree_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
		"""Update input when directory is clicked."""
		self.query_one("#directory-input", Input).value = str(event.path)

	def action_dismiss(self) -> None:
		self.dismiss(None)

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "cancel":
			self.dismiss(None)
		elif event.button.id == "select":
			dir_input = self.query_one("#directory-input", Input).value.strip()
			if dir_input:
				selected_path = Path(dir_input).resolve()
				if selected_path.exists() and selected_path.is_dir():
					self.dismiss(selected_path)
				else:
					# Create directory if it doesn't exist
					try:
						selected_path.mkdir(parents=True, exist_ok=True)
						self.dismiss(selected_path)
					except Exception:
						pass  # Stay on screen if creation fails


class SaveDetailScreen(ModalScreen[None]):
	"""Modal popup that shows the details of a selected save."""

	BINDINGS = [("escape", "dismiss", "Close")]

	def __init__(self, save: Save):
		super().__init__()
		self.save = save

	def compose(self) -> ComposeResult:
		match self.save.room_area.lower():
			case "ruins":
				room_color = "magenta"
			case "waterfall":
				room_color = "blue"
			case "snowdin":
				room_color = "white"
			case "hotland":
				room_color = "grey"
			case "core":
				room_color = "cyan"
			case "new home":
				room_color = "tan"
			case "true lab":
				room_color = "green"
			case "error":
				room_color = "red"
			case _:
				room_color = "black"

		yield Header()
		yield Vertical(
			Label(f"[b]{self.save.TITLE}[/b]", id="detail-title"),
			Container(
				Static(f"[b]Name[/b]: {'[red]' if self.save.genocide else ''}{self.save.NAME}{'[/red]' if self.save.genocide else ''}"),
				Static(f"[b]LOVE:[/b] {self.save.LOVE}"),
				Static(f"[b]EXP:[/b] {self.save.EXP}"),
				Static(f"[b]GOLD:[/b] {self.save.GOLD}"),
				Static(f"[b]HP:[/b] {self.save.HP}"),
				Static(f"[b]FUN:[/b] {self.save.FUN}"),
				Static(f"[b]Kills:[/b] {self.save.kills}"),
				Static(f"[b]Playtime:[/b] {self.save.playtime}"),
				Static(f"[b]Room:[/b] [{room_color}]{self.save.room_area}[/{room_color}]/{self.save.room_name} (#{self.save.room_id})"),
				id="detail-stats"
			),
			Rule(),
			Horizontal(
				Button("Close", id="close", variant="primary"),
				Button("Load Save", id="load", variant="success"),
				id="detail-actions",
			),
			id="detail-body",
		)
		yield Footer()

	def action_dismiss(self) -> None:
		self.dismiss()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "close":
			self.dismiss()
		elif event.button.id == "load":
			if not self.save.is_valid():
				self.app.notify("Cannot load an empty save.", severity="warning")
				return  # Don't load empty saves
			if Save(GAME_SAVE_DIR).is_valid():
				self.app.push_screen(BackupNameScreen(self.save, rm=True))

			load_save(self.save.path, rm=True)
			self.app.notify(f"Loaded save: {self.save.TITLE}", severity="success")
			self.dismiss()


class BackupNameScreen(ModalScreen[None]):
	"""Prompt for a backup name before loading a save."""

	BINDINGS = [("escape", "dismiss", "Close")]

	def __init__(self, save: Save, rm: bool = False):
		super().__init__()
		self.save = save
		self.rm = rm

	def compose(self) -> ComposeResult:
		default_name = datetime.now().strftime("Backup_%Y%m%d_%H%M%S")
		yield Header()
		yield Vertical(
			Label("Name this backup", id="backup-title"),
			Input(placeholder="Backup name", id="backup-name", value=default_name),
			Rule(),
			Horizontal(
				Button("Cancel", id="cancel", variant="primary"),
				Button("Save & Load", id="confirm", variant="success"),
				id="backup-actions",
			),
			id="backup-body",
		)
		yield Footer()

	def action_dismiss(self) -> None:
		self.dismiss()

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "cancel":
			self.dismiss()
		elif event.button.id == "confirm":
			backup_input = self.query_one("#backup-name", Input).value.strip()
			if backup_input:
				backup_save(name=backup_input, backup_dir=self.app.backup_dir, rm=self.rm)
				action = "Saved current game and backed up" if self.rm else "Backed up"
			else:
				self.rm = True
				action = "No name given; Proceeding to load"

			# Refresh list so the new backup shows up immediately
			self.app.refresh_save_list()
			self.app.notify(f"{action} save: {backup_input}", severity="success")
			self.dismiss()


class SaveListView(ListView):
	def __init__(self, backup_dir: PathLike):
		super().__init__()
		self.backup_dir = Path(backup_dir).resolve()

	def compose(self):
		for save in list_backups(self.backup_dir):
			yield SaveWidget(Save(save))

	def on_list_view_selected(self, event: ListView.Selected) -> None:
		if isinstance(event.item, SaveWidget):
			self.app.push_screen(SaveDetailScreen(event.item.save))


class SaveWidget(ListItem):
	def __init__(self, save: Save):
		super().__init__()
		self.save = save

	def compose(self) -> ComposeResult:
		yield Label(self.save.TITLE, id="name")


def main():
	"""Entry point for application. Bundled with poetry (hope it works)
	"""
	print(f"Undertale Manager v{__version__}")
	app = UndertaleManagerApp()
	app.run()


if __name__ == "__main__":
	main()
