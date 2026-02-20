import os
from datetime import datetime

def original_name(path, ext=".zip"):
    return os.path.basename(path.rstrip(os.sep)) + ext

def numeric_name(index, ext=".zip"):
    return f"{index:03d}{ext}"

def chronos_name(index, ext=".zip"):
    date = datetime.now().strftime("%Y-%m-%d")
    return f"{date}_{index:03d}{ext}"
