import zipfile
import tempfile
import os
from typing import List
from .file_utils import is_text_file


def extract_zip_files(zip_file) -> List[str]:
    """Extract files from uploaded zip and return list of file paths."""
    temp_dir = tempfile.mkdtemp()
    file_paths = []

    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Get all files recursively
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if is_text_file(file_path):
                    file_paths.append(file_path)

        return sorted(file_paths)
    except Exception as e:
        raise Exception(f"Error extracting zip file: {str(e)}")