import unittest
import tkinter as tk
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.gui.components import CodeEditorFrame

class TestEditor(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.geometry("800x600")
        self.colors = {
            "bg": "#282a36",
            "fg": "#f8f8f2",
            "activity_bg": "#21222c",
            "comments": "#6272a4",
            "strings": "#f1fa8c",
            "variables": "#8be9fd"
        }
        self.editor_frame = CodeEditorFrame(self.root, self.colors)
        self.editor_frame.pack(fill=tk.BOTH, expand=True)
        self.root.update()

    def tearDown(self):
        self.root.update()
        self.root.destroy()
        
    def test_line_count(self):
        # Clear default empty line just to make it clean, or just append
        self.editor_frame.text.delete("1.0", tk.END)
        self.editor_frame.text.insert(tk.END, "Line 1\nLine 2\nLine 3")
        self.root.update()
        
        # Check canvas items
        items = self.editor_frame.linenumbers.find_all()
        # "Line 1\nLine 2\nLine 3" makes 3 lines, plus an implicit trailing one if not careful, 
        # actually "Line 1" is line 1, "Line 2" is line 2, "Line 3" is line 3, then "\n" creates an empty 4th line
        # but text.delete("1.0", tk.END) leaves a single empty line so it's 4 lines.
        # Let's count them
        self.assertEqual(len(items), 3, "Should have 3 line numbers rendered")
        
        # Verify current line highlight functionality by checking item fill colors
        self.editor_frame.text.mark_set(tk.INSERT, "2.0")
        self.root.update()
        self.editor_frame.linenumbers.redraw() # Just to be sure although event should handle it
        
        # We find all items and their colors
        colored_items = []
        for item in self.editor_frame.linenumbers.find_all():
            color = self.editor_frame.linenumbers.itemcget(item, "fill")
            if color == self.colors["strings"]:
                colored_items.append(item)
                
        self.assertEqual(len(colored_items), 1, "Only one line should be highlighted")

    def test_sync_scroll(self):
        self.editor_frame.text.delete("1.0", tk.END)
        # Add many lines
        for i in range(100):
            self.editor_frame.text.insert(tk.END, f"Line {i}\n")
            
        self.root.update()
        
        # Scroll down
        self.editor_frame.text.yview_moveto(0.5)
        self.root.update()
        
        # Verify redraw got called and the first visible line number is not "1"
        items = self.editor_frame.linenumbers.find_all()
        if not items:
            self.fail("No items rendered on canvas")
            
        first_item_text = self.editor_frame.linenumbers.itemcget(items[0], "text")
        
        self.assertNotEqual(first_item_text, "1", "First visible line number should not be 1 after scrolling down")

if __name__ == '__main__':
    unittest.main()
