import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.timeline.track import MagneticTrack
from src.core.timeline.clip import Clip
from src.core.commands.timeline_commands import AddClipCommand, RemoveClipCommand
from src.core.history import history_manager

class TestTimeline(unittest.TestCase):
    def setUp(self):
        self.track = MagneticTrack("Test Track")
        self.clip1 = Clip("c1", "Clip 1", duration=5.0)
        self.clip2 = Clip("c2", "Clip 2", duration=3.0)
        
        # Reset history
        history_manager.undo_stack.clear()
        history_manager.redo_stack.clear()

    def test_magnetic_append(self):
        # Add Clip 1
        cmd1 = AddClipCommand(self.track, self.clip1)
        history_manager.execute(cmd1)
        
        self.assertEqual(len(self.track.clips), 1)
        self.assertEqual(self.track.clips[0].start_time, 0.0)
        
        # Add Clip 2 (should append)
        cmd2 = AddClipCommand(self.track, self.clip2)
        history_manager.execute(cmd2)
        
        self.assertEqual(len(self.track.clips), 2)
        self.assertEqual(self.track.clips[1].start_time, 5.0) # Should start after Clip 1

    def test_ripple_delete(self):
        # Setup: [Clip 1 (0-5)] [Clip 2 (5-8)]
        self.track.add_clip(self.clip1)
        self.track.add_clip(self.clip2)
        
        # Remove Clip 1
        cmd = RemoveClipCommand(self.track, self.clip1.id)
        history_manager.execute(cmd)
        
        # Check if Clip 2 shifted back to 0
        self.assertEqual(len(self.track.clips), 1)
        self.assertEqual(self.track.clips[0].id, self.clip2.id)
        self.assertEqual(self.track.clips[0].start_time, 0.0)

    def test_undo_redo(self):
        # Add Clip 1
        cmd = AddClipCommand(self.track, self.clip1)
        history_manager.execute(cmd)
        self.assertEqual(len(self.track.clips), 1)
        
        # Undo
        history_manager.undo()
        self.assertEqual(len(self.track.clips), 0)
        
        # Redo
        history_manager.redo()
        self.assertEqual(len(self.track.clips), 1)

if __name__ == '__main__':
    unittest.main()
