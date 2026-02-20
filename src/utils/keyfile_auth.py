"""
Keyfile authentication module for generating, storing, and using keyfiles
"""

import os
import secrets
import hashlib
import hmac
from pathlib import Path

def generate_keyfile(file_path, size=64):
    """
    Generate a random keyfile with the specified size in bytes.
    
    Args:
        file_path (str): Path where the keyfile will be saved (.diophantus extension recommended)
        size (int): Size of the key in bytes (default 64 bytes = 512 bits)
    """
    # Generate cryptographically secure random bytes
    key_data = secrets.token_bytes(size)
    
    # Write the key data to the file
    with open(file_path, 'wb') as f:
        f.write(key_data)
    
    # Set restrictive file permissions (read/write for owner only)
    os.chmod(file_path, 0o600)
    
    return file_path

def load_keyfile(file_path):
    """
    Load and return the content of a keyfile.
    
    Args:
        file_path (str): Path to the keyfile
    
    Returns:
        bytes: Content of the keyfile
    """
    with open(file_path, 'rb') as f:
        return f.read()

def validate_keyfile(file_path):
    """
    Validate that a file is a proper keyfile.
    
    Args:
        file_path (str): Path to the keyfile
    
    Returns:
        bool: True if the file is a valid keyfile, False otherwise
    """
    try:
        if not os.path.exists(file_path):
            return False
        
        # Check file size (reasonable range for a keyfile)
        file_size = os.path.getsize(file_path)
        if file_size < 16 or file_size > 1024:  # Between 128 and 8192 bits
            return False
        
        # Try to read the file to make sure it's accessible
        with open(file_path, 'rb') as f:
            key_data = f.read()
        
        # Basic check: key should be non-empty
        if len(key_data) == 0:
            return False
        
        return True
    except:
        return False

def combine_keyfile_and_password(keyfile_path, password):
    """
    Combine a keyfile and password to create a stronger encryption key.
    
    Args:
        keyfile_path (str): Path to the keyfile
        password (str): User-provided password
    
    Returns:
        str: Combined key derived from both inputs
    """
    # Load the keyfile data
    keyfile_data = load_keyfile(keyfile_path)
    
    # Combine the password and keyfile data using HMAC
    # This creates a derived key that requires both the keyfile AND password
    password_bytes = password.encode('utf-8')
    
    # Use the keyfile as the key and password as the message for HMAC
    # Or vice versa - both approaches provide two-factor authentication
    combined_key = hmac.new(keyfile_data, password_bytes, hashlib.sha256).hexdigest()
    
    return combined_key

def get_removable_drives():
    """
    Get a list of removable drives on the system.
    
    Returns:
        list: List of paths to removable drives
    """
    import platform
    system = platform.system()
    
    removable_drives = []
    
    if system == "Windows":
        import string
        import ctypes
        from ctypes import wintypes
        
        # Get logical drives
        drives = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drive_path = f"{letter}:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
                # DRIVE_REMOVABLE = 2
                if drive_type == 2:
                    removable_drives.append(drive_path)
            bitmask >>= 1
    elif system in ["Linux", "Darwin"]:  # Linux or macOS
        # Common mount points for removable media
        common_mount_points = [
            "/media/*",           # Standard Linux mount point
            "/mnt/*",             # Alternative mount point
            "/Volumes/*",         # macOS external drives
            "/run/media/$USER/*"  # Systemd-based mount points
        ]
        
        import glob
        for mount_pattern in common_mount_points:
            mounts = glob.glob(os.path.expandvars(mount_pattern))
            for mount in mounts:
                if os.path.ismount(mount) or 'usb' in mount.lower() or 'removable' in mount.lower():
                    removable_drives.append(mount)
    
    return removable_drives