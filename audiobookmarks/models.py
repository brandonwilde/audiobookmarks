import os

class LibbyBookDataTree:
    def __init__(self, root_dir: str, book_name: str):
        self.root = root_dir
        self.title = book_name
        self.file_name = book_name.replace(' ', '_').lower()
        self.dir = os.path.join(self.root, self.file_name)
        self.audio_dir = os.path.join(self.dir, "audio")
        self.file = os.path.join(self.dir, self.file_name + '.json')
        self.updated_file = self.file.replace(".json", "_updated.json")

class HooplaBookDataTree:
    def __init__(self, root_dir: str, book_name: str):
        self.root = root_dir
        self.title = book_name
        self.file_name = book_name.replace(' ', '_').lower()
        self.dir = os.path.join(self.root, self.file_name)
        self.title_file = os.path.join(self.dir, f"{self.file_name}_title.json")
        self.bookmarks_file = os.path.join(self.dir, f"{self.file_name}_bookmarks.json")