import os
from pathlib import Path

class BookDataTree:
    def __init__(self, root_dir: str, book_name: str):
        self.root = root_dir
        self.title = book_name
        self.file_name = book_name.replace(' ', '_').lower()
        self.dir = os.path.join(self.root, self.file_name)
        self.audio_dir = os.path.join(self.file_dir, "audio")
        self.file = os.path.join(self.file_dir, self.file_name + '.json')
        self.updated_file = self.file.replace(".json", "_updated.json")
