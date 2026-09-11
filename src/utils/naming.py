import os
from datetime import datetime, timezone


def original_name(path, ext=".zip"):
    return os.path.basename(path.rstrip(os.sep)) + ext

def numeric_name(index, ext=".zip"):
    return f"{index:03d}{ext}"

def chronos_name(index, ext=".zip"):
    date = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    return f"{date}_{index:03d}{ext}"
