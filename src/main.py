from textual.app import App, ComposeResult, SystemCommand
from textual.containers import Grid, HorizontalGroup, VerticalGroup, VerticalScroll
from textual.command import CommandPalette
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.content import Content
from textual.widgets import (
	Static,
	TextArea,
	Input,
	Select,
	SelectionList,
	TabbedContent,
	TabPane,
	Button,
	Label,
	RichLog,
	Footer
)
from haxelib import *
from haxe import *
import re
import json
from pathlib import Path
import sys
from testworkspace import TestWorkspace
from cmdproviders import ExampleProvider
from resources import resource_path
import uuid


TARGETS = ("Eval", "Javascript", "Neko", "Hashlink", "CPPIA", "Lua", "Python", "C++")
MODULE_TYPES = ("Haxe Module", "Json Resource", "Plain Resource")

Application = None
CustomHxmlList = []
HaxeTestWorkspace = None

def random_id():
	return "U" + str(uuid.uuid4().int)

def to_snake_case(s):
	s = re.sub(r'[^a-zA-Z0-9]', '_', s)
	s = re.sub(r'_+', '_', s)
	return s.strip('_').lower()

LastTarget = to_snake_case(TARGETS[0])

def create_ws_params(main_class, target, haxelibs, custom_hxml_flags, modules) -> TestWorkspace | None:
	global HaxeTestWorkspace
	if HaxeTestWorkspace is not None:
		return None
	
	HaxeTestWorkspace = TestWorkspace(main_class, target, haxelibs, custom_hxml_flags, modules)
	return HaxeTestWorkspace

def create_ws() -> TestWorkspace | None:
	global HaxeTestWorkspace
	if HaxeTestWorkspace is not None:
		return None
	
	main_class = Application.query_one("#mainClassInput", Input).value
	target = Application.query_one("#targetSelect", Select).value
	haxelibs_selection = Application.query_one("#haxelibsSelectionList", SelectionList)
	haxelibs = [str(haxelibs_selection.get_option_at_index(i).prompt) for i in haxelibs_selection.selected]

	moduleTabsContent = Application.query_one("#moduleTabsContent", TabbedContent)
	modules = []
	for tab in moduleTabsContent.query(TabPane):
		pane = tab.query_one(ModuleFileTabPane)
		if pane is not None:
			modules.append({
				"path": pane.moduleNameInput.value,
				"type": pane.fileTypeSelect.value,
				"content": pane.inputArea.text
			})

	return create_ws_params(main_class, target, haxelibs, CustomHxmlList, modules)

insertCount = 1

class ModuleFileTabPane(Static):
	inputArea = None
	moduleNameInput = None
	fileTypeSelect = None

	def __init__(self, initial_content="", initial_path="", initial_type="haxe_module", **kwargs):
		super().__init__(**kwargs)
		self._initial_content = initial_content
		self._initial_path = initial_path
		self._initial_type = initial_type

	def on_mount(self) -> None:
		if self._initial_content:
			self.inputArea.text = self._initial_content
		if self._initial_path:
			self.moduleNameInput.value = self._initial_path
		if self._initial_type:
			self.fileTypeSelect.value = self._initial_type

	_VALID_PATH_RE = re.compile(r'^[a-zA-Z0-9_]+(/[a-zA-Z0-9_]+)*(\.[a-zA-Z0-9_]+)?$')

	def _get_tab_label(self, path: str) -> str:
		if not path or not path.strip() or not self._VALID_PATH_RE.match(path):
			return "<???>"
		name = path.rsplit("/", 1)[-1]
		stem = name.rsplit(".", 1)[0] if "." in name else name
		return stem

	def on_input_changed(self, event: Input.Changed) -> None:
		if event.input is self.moduleNameInput:
			for ancestor in self.ancestors:
				if isinstance(ancestor, TabPane):
					tabs_content = self.app.query_one("#moduleTabsContent", TabbedContent)
					tab = tabs_content.get_tab(ancestor.id)
					label = self._get_tab_label(event.value)
					if label == "<???>":
						tab.label = "[red]<???>[/red]"
					else:
						tab.label = label
					break

	def compose(self) -> ComposeResult:
		self.inputArea = TextArea(placeholder="Write some Haxe code here...", id="codeTextArea")
		self.moduleNameInput = Input(placeholder="(Required) Module path...", classes="module-input")
		self.fileTypeSelect = Select(((modType, to_snake_case(modType)) for modType in MODULE_TYPES), classes="small-select", allow_blank=False)

		yield HorizontalGroup(
			self.moduleNameInput,
			self.fileTypeSelect,
			Button.error("Delete", id="deleteModuleButton"),
			Button("+", variant="primary", classes="res-add-button", id="addModuleButton")
		)
		yield self.inputArea

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "addModuleButton":

			global insertCount
			modName = f"Module{insertCount}"
			insertCount += 1

			moduleTabsContent = self.app.query_one("#moduleTabsContent", TabbedContent)
			newPane = ModuleFileTabPane(
				initial_content="",
				initial_path=modName,
				initial_type="haxe_module",
			)
			tabPane = TabPane(modName, newPane, id=random_id())
			moduleTabsContent.add_pane(tabPane)
			self.call_after_refresh(setattr, moduleTabsContent, "active", tabPane.id)
		elif event.button.id == "deleteModuleButton":
			moduleTabsContent = self.app.query_one("#moduleTabsContent", TabbedContent)
			for ancestor in self.ancestors:
				if isinstance(ancestor, TabPane):
					moduleTabsContent.remove_pane(ancestor.id)
					break

class CodeEditorPanel(Static):
	def compose(self) -> ComposeResult:
		yield Label("Code Editor", classes="panel-title")
		yield TabbedContent(id="moduleTabsContent")

class HaxeOptionsPanel(Static):
	def compose(self) -> ComposeResult:
		haxelibs = getActiveHaxelibs()

		yield Label("Options", classes="panel-title")

		yield Label("Main class:")
		yield Input(value="Main", placeholder="Main", id="mainClassInput", valid_empty=False)

		yield Label("Target:")
		yield Select(((target, to_snake_case(target)) for target in TARGETS), allow_blank=False, id="targetSelect")

		yield Label("Libraries:")
		yield SelectionList[int](
			*( (lib, i) for i, lib in enumerate(haxelibs) ),
			classes="haxelibs-list",
			id="haxelibsSelectionList"
		)

		yield VerticalGroup(
			Label(f"Haxe {getHaxeVersion() or 'not found'}"),
			classes="info-vgroup"
		)

		yield Button("Custom HXML Code", classes="out-button", id="customHxmlButton")

	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "customHxmlButton":
			self.app.push_screen(EditCustomHxmlScreen())

	def on_select_changed(self, event: Select.Changed) -> None:
		if event.select.id == "targetSelect":
			global LastTarget
			target = event.value
			if target == "c":
				self.app.push_screen(ConfirmCppTargetScreen())
			else:
				LastTarget = target


class EditCustomHxmlScreen(ModalScreen):
	def compose(self) -> ComposeResult:
		yield HorizontalGroup(
			Label("Edit Custom HXML", classes="panel-title"),
			Button("_", classes="term-button term-close-button", variant="primary", compact=True, id="closeHxmlScreenButton")
		)
		yield TextArea(placeholder="Enter custom HXML flags here, one per line...", id="customHxmlTextArea", text="\n".join(CustomHxmlList)	or "")

	def on_button_pressed(self, event: Button.Pressed) -> None:
		global CustomHxmlList
		if event.button.id == "closeHxmlScreenButton":
			CustomHxmlList.clear()
			CustomHxmlList = self.query_one("#customHxmlTextArea", TextArea).text.splitlines()
			self.app.pop_screen()

class ConfirmCppTargetScreen(ModalScreen):
	def compose(self) -> ComposeResult:
		yield Grid(
			Label("The target you have selected (C++) may take a few minutes to compile and run.\n[orange]Are you sure you want to continue with C++?[/orange]", id="question"),
			Button("Revert", variant="primary", id="revertButton"),
			Button("Yes", variant="error", id="yesButton"),
			id="dialog",
		)

	def on_button_pressed(self, event: Button.Pressed) -> None:
		global LastTarget
		targetSelect = self.app.query_one("#targetSelect", Select)
		if event.button.id == "yesButton":
			self.app.pop_screen()
		elif event.button.id == "revertButton":
			self.app.pop_screen()
			with targetSelect.prevent(Select.Changed):
				targetSelect.value = LastTarget

class TerminalButtonsPanel(Static):
	def compose(self) -> ComposeResult:
		yield HorizontalGroup(
			Button("Check", classes="out-button", variant="primary", id="checkWsButton"),
			Button.success("Run", classes="out-button", id="runWsButton"),
			Button.error("Stop", classes="out-button", id="stopWsButton", disabled=True)
		)
		yield Button("Open Output", classes="out-button", id="openTerminalButton")
	
	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "openTerminalButton":
			terminalWindow = self.app.query_one("#terminalWindow", TerminalWindow)
			terminalWindow.display = True
		elif event.button.id == "checkWsButton":
			self.app.check_ws()
		elif event.button.id == "runWsButton":
			self.app.start_test_ws()
		elif event.button.id == "stopWsButton":
			self.app.stop_test_ws()

class TerminalWindow(Static):
	def compose(self) -> ComposeResult:
		self.display = False
		yield HorizontalGroup(
			Label("Terminal Output", classes="panel-title"),
			Button("_", classes="term-button term-close-button", variant="primary", compact=True, id="closeTerminalButton")
		)
		yield RichLog(classes="terminal-log", markup=True)
	
	def on_button_pressed(self, event: Button.Pressed) -> None:
		if event.button.id == "closeTerminalButton":
			self.display = False

class MyApp(App):
	
	CSS_PATH = str(resource_path("style.tcss"))
	BINDINGS = [
		# Binding("ctrl+s", "save_ws", "Save workspace"),
		# Binding("ctrl+o", "open_ws", "Open workspace"),
		Binding("ctrl+f", "toggle_code_focus", "Toggle code focus", tooltip="Toggle focus off the code editor"),
		Binding("ctrl+t", "toggle_terminal", "Toggle terminal", tooltip="Show or hide the terminal window"),
		Binding("f5", "run_stop_ws", "Run/Stop workspace", tooltip="Run or stop the current workspace"),
	]

	def compose(self) -> ComposeResult:
		self._manual_stop = False
		self._action_debounce = False
		self._textarea_edited = False
		yield HorizontalGroup(
			CodeEditorPanel(classes="panel"),
			VerticalScroll(
				HaxeOptionsPanel(classes="panel options-panel"),
				TerminalButtonsPanel(classes="panel"),
				classes="side-panel"
			)
		)
		yield TerminalWindow(classes="panel terminal-window", id="terminalWindow")
		yield Footer()

	def get_system_commands(self, screen):
		yield from super().get_system_commands(screen)  
		yield SystemCommand("Open Example", "Open an example project", self.action_open_example)  

	def action_open_example(self):
		self.push_screen(
			CommandPalette(
				providers=[ExampleProvider],
				placeholder="Search for examples…",
			),
		)

	def on_ready(self) -> None:
		self.loadExampleData("Hello world")
	
	async def on_key(self, event) -> None:
		focused = self.focused
		
		if event.key == "tab" and isinstance(focused, TextArea):
			if self._textarea_edited:
				event.prevent_default()
				event.stop()
				focused.insert("\t")
				return
		
		if event.key == "ctrl+delete" and isinstance(focused, TextArea):
			event.prevent_default()
			event.stop()
			focused.action_delete_word_right()
			return
		
		if event.key == "ctrl+h" and isinstance(focused, TextArea):
			event.prevent_default()
			event.stop()
			focused.action_delete_word_left()
			return
	
	def _set_footer_state_default(self):
		footer = self.query_one(Footer)
		footer.remove_class("footer-preparing", "footer-running", "footer-success", "footer-error")
	
	def _set_footer_state_preparing(self):
		footer = self.query_one(Footer)
		footer.remove_class("footer-running", "footer-success", "footer-error")
		footer.add_class("footer-preparing")
	
	def _set_footer_state_running(self):
		footer = self.query_one(Footer)
		footer.remove_class("footer-preparing", "footer-success", "footer-error")
		footer.add_class("footer-running")
	
	def _set_footer_state_success(self):
		footer = self.query_one(Footer)
		footer.remove_class("footer-preparing", "footer-running", "footer-error")
		footer.add_class("footer-success")
	
	def _set_footer_state_error(self):
		footer = self.query_one(Footer)
		footer.remove_class("footer-preparing", "footer-running", "footer-success")
		footer.add_class("footer-error")

	def loadExampleData(self, exampleName):
		self.loadDataFile(str(resource_path("examples", exampleName + ".json").resolve()))

	def loadDataFile(self, filePath):
		log = self.query_one(RichLog)
		try:
			with open(filePath, "r") as file:
				self.loadData(json.load(file))
		except json.decoder.JSONDecodeError as e:
			log.write(f"[red]Error decoding data: {e}[/red]")
			self.notify(f"Failed to decode data file {Path(filePath).name}.\nOpen the terminal for more information.", severity="error", timeout=10)
		except Exception as e:
			log.write(f"[red]Error loading data: {e}[/red]")
			self.notify(f"Failed to load data file {Path(filePath).name}.\nOpen the terminal for more information.", severity="error", timeout=10)

	def loadData(self, data):
		# Modules
		moduleTabsContent = self.query_one("#moduleTabsContent", TabbedContent)
		moduleTabsContent.clear_panes()
		firstPane = None
		for resource in data["resources"]:
			pane = ModuleFileTabPane(
				initial_content=resource["content"],
				initial_path=resource["path"],
				initial_type=resource["type"],
			)
			tabPane = TabPane(resource["path"], pane, id=random_id())
			if firstPane is None:
				firstPane = tabPane
			moduleTabsContent.add_pane(tabPane)

		self.call_after_refresh(setattr, moduleTabsContent, "active", firstPane.id)

		# Options
		options = data["options"]
		mainClassInput = self.query_one("#mainClassInput", Input)
		targetSelect = self.query_one("#targetSelect", Select)
		haxelibsSelectionList = self.query_one("#haxelibsSelectionList", SelectionList)

		mainClassInput.value = options["mainClass"]
		targetSelect.value = options["target"]

		for i, lib in enumerate(getActiveHaxelibs()):
			if lib in options["libraries"]:
				haxelibsSelectionList.select(haxelibsSelectionList.get_option_at_index(i))
			else:
				haxelibsSelectionList.deselect(haxelibsSelectionList.get_option_at_index(i))

		global CustomHxmlList
		CustomHxmlList = options["customHxmlFlags"]


	def check_ws(self):
		global HaxeTestWorkspace

		self.query_one(CodeEditorPanel).disabled = True
		self.query_one(HaxeOptionsPanel).disabled = True

		self.query_one("#checkWsButton", Button).disabled = True
		self.query_one("#runWsButton", Button).disabled = True
		self.query_one("#stopWsButton", Button).disabled = True

		log = self.query_one(RichLog)
		log.clear()

		self._set_footer_state_preparing()

		CustomHxmlList.append("--define no-compilation")
		create_ws()
		
		if HaxeTestWorkspace is not None:
			
			def on_setup():
				self._set_footer_state_preparing()
			
			def on_start():
				self._set_footer_state_running()
				self.bell()
			
			def on_stdout(line: str):
				log.write(line.rstrip())

			def on_comp_stdout(line: str):
				log.write("[blue]" + line.rstrip() + "[/blue]")
			
			def on_stderr(line: str):
				log.write("[red]" + line.rstrip() + "[/red]")
			
			def on_finish(exit_code: int):
				if self._manual_stop:
					self._set_footer_state_default()
				elif exit_code == 0:
					self._set_footer_state_success()
					self.notify("Check completed successfully! No compile-time errors were found.", severity="information")
				else:
					self._set_footer_state_error()
					self.bell()
					self.notify(f"Check failed! Check the console for more information.", severity="error")
				
				self._cleanup_after_run()
				self._manual_stop = False
			
			HaxeTestWorkspace.on_setup(on_setup)
			HaxeTestWorkspace.on_start(on_start)
			HaxeTestWorkspace.on_comp_stdout(on_comp_stdout)
			HaxeTestWorkspace.on_stdout(on_stdout)
			HaxeTestWorkspace.on_stderr(on_stderr)
			HaxeTestWorkspace.on_finish(on_finish)
			
			HaxeTestWorkspace.setup()
			CustomHxmlList.pop()
			HaxeTestWorkspace._stopped_during_compile = True
			HaxeTestWorkspace.run()

		self.query_one("#stopWsButton", Button).disabled = False

	def start_test_ws(self):
		global HaxeTestWorkspace

		self.query_one(CodeEditorPanel).disabled = True
		self.query_one(HaxeOptionsPanel).disabled = True

		self.query_one("#checkWsButton", Button).disabled = True
		self.query_one("#runWsButton", Button).disabled = True
		self.query_one("#stopWsButton", Button).disabled = True

		log = self.query_one(RichLog)
		log.clear()

		self._set_footer_state_preparing()

		create_ws()
		
		if HaxeTestWorkspace is not None:
			
			def on_setup():
				self._set_footer_state_preparing()
			
			def on_start():
				self._set_footer_state_running()
				self.bell()
			
			def on_stdout(line: str):
				log.write(line.rstrip())

			def on_comp_stdout(line: str):
				log.write("[blue]" + line.rstrip() + "[/blue]")
			
			def on_stderr(line: str):
				log.write("[red]" + line.rstrip() + "[/red]")
			
			def on_finish(exit_code: int):
				if self._manual_stop:
					self._set_footer_state_default()
				elif exit_code == 0:
					self._set_footer_state_success()
					self.notify("Process completed successfully", severity="information")
				else:
					self._set_footer_state_error()
					self.bell()
					self.notify(f"Process failed with exit code: {exit_code}", severity="error")
				
				self._cleanup_after_run()
				self._manual_stop = False
			
			HaxeTestWorkspace.on_setup(on_setup)
			HaxeTestWorkspace.on_start(on_start)
			HaxeTestWorkspace.on_comp_stdout(on_comp_stdout)
			HaxeTestWorkspace.on_stdout(on_stdout)
			HaxeTestWorkspace.on_stderr(on_stderr)
			HaxeTestWorkspace.on_finish(on_finish)
			
			HaxeTestWorkspace.setup()
			HaxeTestWorkspace.run()

		self.query_one("#stopWsButton", Button).disabled = False
	
	def _cleanup_after_run(self):
		global HaxeTestWorkspace
		
		self.query_one(CodeEditorPanel).disabled = False
		self.query_one(HaxeOptionsPanel).disabled = False
		
		self.query_one("#checkWsButton", Button).disabled = False
		self.query_one("#runWsButton", Button).disabled = False
		self.query_one("#stopWsButton", Button).disabled = True
		
		if HaxeTestWorkspace is not None:
			HaxeTestWorkspace.cleanup()
			HaxeTestWorkspace = None
	
	def stop_test_ws(self):
		global HaxeTestWorkspace

		self.query_one("#checkWsButton", Button).disabled = True
		self.query_one("#runWsButton", Button).disabled = True
		self.query_one("#stopWsButton", Button).disabled = True

		if HaxeTestWorkspace is not None:
			self._manual_stop = True
			HaxeTestWorkspace.stop()
		else:
			self._cleanup_after_run()

	def on_text_area_changed(self, event: TextArea.Changed) -> None:
		if event.text_area.id == "codeTextArea":
			self._set_footer_state_default()
			self._textarea_edited = True
	
	def on_focus(self, event) -> None:
		if isinstance(event.widget, TextArea):
			self._textarea_edited = False
	
	def on_input_changed(self, event: Input.Changed) -> None:
		if event.input.id in ("mainClassInput",):
			self._set_footer_state_default()
	
	def on_select_changed(self, event: Select.Changed) -> None:
		if event.select.id == "targetSelect":
			self._set_footer_state_default()
	
	def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged) -> None:
		if event.selection_list.id == "haxelibsSelectionList":
			self._set_footer_state_default()

	# Binding actions

	def action_run_stop_ws(self):
		if self._action_debounce:
			return
		
		self._action_debounce = True
		self.set_timer(0.5, lambda: setattr(self, '_action_debounce', False))
		
		if HaxeTestWorkspace is not None:
			self.stop_test_ws()
		else:
			self.start_test_ws()

	def action_focus_code(self):
		moduleTabsContent = self.query_one("#moduleTabsContent", TabbedContent)
		activeTab = moduleTabsContent.active_pane
		if activeTab and isinstance(activeTab, TabPane):
			activeTab.query_one("#codeTextArea").focus()

	def action_toggle_code_focus(self):
		focused = self.focused
		
		if isinstance(focused, TextArea) and focused.id == "codeTextArea":
			mainClassInput = self.query_one("#mainClassInput", Input)
			mainClassInput.focus()
		else:
			moduleTabsContent = self.query_one("#moduleTabsContent", TabbedContent)
			activeTab = moduleTabsContent.active_pane
			if activeTab and isinstance(activeTab, TabPane):
				codeArea = activeTab.query_one("#codeTextArea", TextArea)
				codeArea.focus()

	def action_toggle_terminal(self):
		terminalWindow = self.query_one("#terminalWindow", TerminalWindow)
		terminalWindow.display = not terminalWindow.display


	# TODO: Opening and saving workspaces
	def action_open_ws(self):
		pass
		"""
		path = filechooser.open_file(
			title="Open Workspace",
			filters=[["Json files", "*.json"], ["All files", "*.*"]]
		)
		if path:
			self.loadDataFile(path[0])
		"""

	def action_save_ws(self):
		"""
		path = filechooser.save_file(
			title="Save Workspace",
			filters=[["Json files", "*.json"], ["All files", "*.*"]]
		)
		"""
		path = None
		if not path:
			return
		
		main_class = Application.query_one("#mainClassInput", Input).value
		target = Application.query_one("#targetSelect", Select).value
		haxelibs_selection = Application.query_one("#haxelibsSelectionList", SelectionList)
		haxelibs = [str(haxelibs_selection.get_option_at_index(i).prompt) for i in haxelibs_selection.selected]

		moduleTabsContent = Application.query_one("#moduleTabsContent", TabbedContent)
		modules = []
		for tab in moduleTabsContent.query(TabPane):
			pane = tab.query_one(ModuleFileTabPane)
			if pane is not None:
				modules.append({
					"path": pane.moduleNameInput.value,
					"type": pane.fileTypeSelect.value,
					"content": pane.inputArea.text
				})
		
		with open(path, 'w', encoding='utf-8') as f:
			json.dump({
				"resources": modules,
				"options": {
					"mainClass": main_class,
					"target": target,
					"libraries": haxelibs,
					"customHxmlFlags": CustomHxmlList
				}
			}, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
	Application = MyApp()
	Application.run()
