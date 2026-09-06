import os
import uuid
from pathlib import Path
from PyPDF2 import PdfReader
import docx

def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    Extracts plain text from standard document formats.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found.")

    text_content = ""
    file_type = file_type.lower()

    try:
        if file_type == "pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
                
        elif file_type == "docx":
            doc = docx.Document(file_path)
            text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
        elif file_type in ["txt", "md", "markdown"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()
        else:
            raise ValueError(f"Unsupported file format: {file_type}")
            
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from {file_type} file: {e}")

    return text_content.strip()
