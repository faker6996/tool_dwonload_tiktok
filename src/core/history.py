from typing import List
from .commands.base import Command

class HistoryManager:
    """
    Manages the undo/redo stack.
    """
    def __init__(self, max_history: int = 50):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_history = max_history

    def execute(self, command: Command):
        """
        Execute a command and add it to history.
        """
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear() # Clear redo stack on new action
        
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            return
            
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)

    def redo(self):
        if not self.redo_stack:
            return
            
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)

# Global History Manager
history_manager = HistoryManager()
