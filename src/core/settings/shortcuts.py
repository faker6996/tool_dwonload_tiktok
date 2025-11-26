import json
import os
from dataclasses import dataclass, asdict
from typing import Dict

@dataclass
class Shortcut:
    action_id: str
    name: str
    key_sequence: str # e.g., "Ctrl+S", "Space"

class ShortcutManager:
    def __init__(self):
        self.shortcuts: Dict[str, Shortcut] = {}
        self.defaults = {
            "play_pause": Shortcut("play_pause", "Play/Pause", "Space"),
            "undo": Shortcut("undo", "Undo", "Ctrl+Z"),
            "redo": Shortcut("redo", "Redo", "Ctrl+Shift+Z"),
            "cut": Shortcut("cut", "Cut Clip", "C"),
            "delete": Shortcut("delete", "Delete", "Delete"),
            "save": Shortcut("save", "Save Project", "Ctrl+S"),
            "import": Shortcut("import", "Import Media", "Ctrl+I"),
        }
        self.load_shortcuts()

    def load_shortcuts(self):
        # For MVP, just use defaults. 
        # In real app, load from user config file.
        self.shortcuts = self.defaults.copy()

    def get_shortcut(self, action_id: str) -> str:
        if action_id in self.shortcuts:
            return self.shortcuts[action_id].key_sequence
        return ""

    def set_shortcut(self, action_id: str, key_sequence: str):
        if action_id in self.shortcuts:
            self.shortcuts[action_id].key_sequence = key_sequence
            # Save to config file here

# Global instance
shortcut_manager = ShortcutManager()
