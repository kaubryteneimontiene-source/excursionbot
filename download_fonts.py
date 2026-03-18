import urllib.request
import tempfile
import os

font_path = os.path.join(tempfile.gettempdir(), "DejaVuSans.ttf")
font_bold_path = os.path.join(tempfile.gettempdir(), "DejaVuSans-Bold.ttf")

print("Downloading fonts...")
urllib.request.urlretrieve(
    "https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans.ttf",
    font_path
)
urllib.request.urlretrieve(
    "https://cdn.jsdelivr.net/npm/dejavu-fonts-ttf@2.37.3/ttf/DejaVuSans-Bold.ttf",
    font_bold_path
)
print("Done! Font exists:", os.path.exists(font_path))