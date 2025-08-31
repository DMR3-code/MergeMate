import os
import chardet
from typing import Tuple, List
from pathlib import Path

SUPPORTED_EXTENSIONS = {
    '.txt', '.xml', '.java', '.py', '.js', '.html', '.css', '.json',
    '.md', '.yml', '.yaml', '.ini', '.cfg', '.conf', '.log', '.sql',
    '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs',
    '.sh', '.bat', '.ps1', '.r', '.scala', '.kt', '.swift', '.dart',
    '.tsx', '.jsx', '.vue', '.svelte', '.ts', '.coffee', '.less',
    '.scss', '.sass', '.styl', '.pug', '.ejs', '.hbs', '.mustache'
}


def detect_encoding(file_path: str) -> str:
    """Detect the encoding of a file."""
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            return result['encoding'] if result['encoding'] else 'utf-8'
    except:
        return 'utf-8'


def read_file_content(file_path: str) -> Tuple[str, bool]:
    """Read file content with proper encoding detection."""
    try:
        encoding = detect_encoding(file_path)

        with open(file_path, 'r', encoding=encoding) as file:
            content = file.read()
            return content, True
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                return content, True
        except:
            return f"[Error: Could not read file {file_path}]", False
    except Exception as e:
        return f"[Error reading {file_path}: {str(e)}]", False


def is_text_file(file_path: str) -> bool:
    """Check if a file is likely a text file based on extension."""
    return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS


def save_content_to_file(content: str, output_path: str) -> bool:
    """Save content to a file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True
    except Exception as e:
        raise Exception(f"Error saving file: {str(e)}")


def get_file_info(file_path: str) -> dict:
    """Get file information (name, size, etc.)."""
    if not os.path.exists(file_path):
        return {"name": os.path.basename(file_path), "size": 0, "exists": False}

    return {
        "name": os.path.basename(file_path),
        "size": os.path.getsize(file_path),
        "exists": True
    }