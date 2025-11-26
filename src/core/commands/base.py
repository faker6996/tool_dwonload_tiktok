from abc import ABC, abstractmethod

class Command(ABC):
    """
    Abstract base class for all commands (Undo/Redo).
    """
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass
