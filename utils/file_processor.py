import pandas as pd
from docx import Document

def process_csv(file) -> str:
    df = pd.read_csv(file)
    return df.to_json()

def process_docx(file) -> str:
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])