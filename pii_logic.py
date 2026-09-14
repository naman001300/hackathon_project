import re

def redact_pii(text: str) -> str:
    # Email hatane ka logic
    cleaned_text = re.sub(r'\S+@\S+', '[EMAIL REDACTED]', text)
    
    # Phone number hatane ka logic (10 digits)
    cleaned_text = re.sub(r'\b\d{10}\b', '[PHONE REDACTED]', cleaned_text)
    
    # NOTE: Priyanshu apna Hugging Face ka logic yahan add karega taaki Names bhi hat jayein.
    
    return cleaned_text
