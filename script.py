from PIL import Image, ImageDraw, ImageFont
import textwrap
import ctypes
import time
import os
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
import winreg


def get_current_wallpaper(script_folder):
    reg_key = r"Control Panel\Desktop"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_key) as key:
            wallpaper_path, _ = winreg.QueryValueEx(key, "Wallpaper")
            if script_folder in wallpaper_path:
                with open('last_wallpaper.txt', 'r') as f:
                    wallpaper_path = f.read()
            else:
                with open('last_wallpaper.txt', 'w') as f:
                    f.write(wallpaper_path)
            return wallpaper_path
    except FileNotFoundError:
        return 0


def create_wallpaper(base_image_path, notes_file_path, output_path):
    
    wallpaper = Image.open(base_image_path)
    wallpaper_width, wallpaper_height = wallpaper.size
    SCALE = wallpaper_width/1920
    fontsize = 15*SCALE  # Adjust font size based on the wallpaper width
    draw = ImageDraw.Draw(wallpaper)

    # Read the notes content from the .txt file
    with open(notes_file_path, 'r') as file:
        notes_content = file.read()

    font = ImageFont.truetype("comic.ttf", fontsize)  # Adjust font size
    text_color = "black"
    max_text_width = 500*SCALE  # Maximum allowable width for the note

    # Split the text into paragraphs and wrap it
    paragraphs = notes_content.splitlines()
    wrapped_lines = []
    for paragraph in paragraphs:
        wrapped_lines.extend(textwrap.fill(paragraph, width=40).splitlines())

    # Calculate the required dimensions for the note
    line_height = font.getbbox("A")[3]  # Height of a single line of text
    note_width = max(font.getbbox(line)[2] for line in wrapped_lines) + (30 * SCALE)  # Add padding
    note_height = len(wrapped_lines) * line_height * (1.275 - fontsize/200) + (30 * wallpaper_height) // 1080  # Add padding

    # Limit the width of the note to the maximum allowable width
    note_width = min(note_width, max_text_width)

    # Define the position of the sticky note
    sticky_note_x, sticky_note_y = 50*SCALE, 50*SCALE  # Top-left corner

    # Draw the sticky note rectangle
    sticky_note_color = (255, 255, 153)
    draw.rectangle(
        [
            (sticky_note_x, sticky_note_y),
            (sticky_note_x + note_width, sticky_note_y + note_height),
        ],
        fill=sticky_note_color,
        outline="black",
    )

    final_text = "\n".join(wrapped_lines)

    text_x = sticky_note_x + 10*SCALE  # Left padding
    text_y = sticky_note_y + 10*SCALE  # Top padding
    draw.multiline_text((text_x, text_y), final_text, fill=text_color, font=font)

    wallpaper.save(output_path)

def set_wallpaper(image_path):
    absolute_path = os.path.abspath(image_path)

    # Set the wallpaper using the Windows API
    ctypes.windll.user32.SystemParametersInfoW(20, 0, absolute_path, 3)

# Event handler class
class NotesFileHandler(FileSystemEventHandler):
    def __init__(self, notes_file, wallpaper_path, output_path):
        self.notes_file = notes_file
        self.wallpaper_path = wallpaper_path
        self.output_path = output_path

    def on_modified(self, event):
        # Check if the updated file is the target notes file
        if event.src_path == os.path.abspath(self.notes_file):
            self.wallpaper_path = get_current_wallpaper(script_folder)
            create_wallpaper(self.wallpaper_path, self.notes_file, self.output_path)
            set_wallpaper(self.output_path)

# Monitoring function with lightweight polling
def monitor_file(notes_file, wallpaper_path, output_path, polling_interval=5):
    event_handler = NotesFileHandler(notes_file, wallpaper_path, output_path)

    # Set up the polling observer with a reduced polling interval
    observer = PollingObserver()
    observer.schedule(event_handler, path=os.path.dirname(os.path.abspath(notes_file)), recursive=False)
    observer.start()

    try:
        # Reduced frequency check (every 'polling_interval' seconds)
        while True:
            time.sleep(polling_interval)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    
script_folder = r"D:\Python\Wallpaper Elements"
base_image_path = get_current_wallpaper(script_folder)
base = script_folder + r"\base.png"
notes_file_path = script_folder + r"\note.txt"
output_image_path = script_folder + r"\updated_wallpaper.png"

if os.path.isfile(base):
    base_image_path = base

if base_image_path == 0:
    pass
else:
    # Start monitoring with a 5-second polling interval
    monitor_file(notes_file_path, base_image_path, output_image_path, polling_interval=5)