# Transcript Processor Script

This script processes transcript text files by removing timecodes, replacing specified words or phrases, formatting dialogue, and generating summaries using the OpenAI API. The script is designed to be flexible, allowing users to add or remove hosts dynamically through a graphical user interface (GUI).

## Features

- **Timecode Removal**: Automatically removes timecodes from the transcript.
- **Word Replacement**: Find and replace specified words or phrases.
- **Host Formatting**: Formats the dialogue with host names and ensures proper line breaks.
- **Summary Generation**: Uses the OpenAI API to generate both short and detailed summaries of the transcript.
- **GUI Interface**: A user-friendly interface for selecting files, setting API keys, managing hosts, and starting the processing.

## Requirements

- Python 3.x
- `openai`
- `tkinter` (usually included with Python)
- `requests` (if needed for additional web-related tasks)

## Installation

To run this script, you need to install the required Python packages. Below are the commands to install each package:

```bash
pip install openai
pip install requests  # Install this only if you need to handle additional HTTP requests
