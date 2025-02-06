#import openai
from openai import OpenAI
import os

def extract_text_within_markers(text, marker='---'):
    """
    Extracts the text enclosed between two markers in a given string.

    Parameters:
    text (str): The input text containing the markers.
    marker (str): The marker string that encloses the text to be extracted.

    Returns:
    str: The extracted text within the markers, or an empty string if markers are not found.
    """
    # Split the text by the marker
    parts = text.split(marker)
    
    # Check if there are at least two markers
    if len(parts) < 3:
        return "No text found within markers."
    
    # The text between the first and second markers is what we want
    return parts[1].strip()


def call_openai_new(prompt_val,content,extract_within_marker=True):
    client = OpenAI(api_key=os.getenv('OPAIKEY'))
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{content}\n{prompt_val}"}
        ]
    )
    if extract_within_marker:
        return extract_text_within_markers(completion.choices[0].message.content)
    return completion.choices[0].message.content

