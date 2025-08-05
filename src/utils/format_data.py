import re


def extract_number(value):
    # Remove all non-digit characters (e.g., spaces, commas)
    cleaned_value = re.sub(r'\D', '', value)
    return int(cleaned_value) if cleaned_value else None
