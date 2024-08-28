import re
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import openai

# Initialize OpenAI API
openai.api_key = 'Your-API-Key-Here'

def generate_summary(text, summary_type="short"):
    prompt = "Summarize the following transcript."
    if summary_type == "detailed":
        prompt = "Provide a detailed five-paragraph summary of the following transcript."
    elif summary_type == "short":
        prompt = "Summarize the following transcript in three sentences."

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        max_tokens=10000 if summary_type == "detailed" else 10000
    )
    summary = response['choices'][0]['message']['content'].strip()
    return summary

def process_transcript(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        transcript = file.read()

    # Step 1: Remove timecodes
    transcript = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{2}', '', transcript)
    transcript = re.sub(r'\d{2}:\d{2}\.\d{2}', '', transcript)

    # Step 2: Replace every instance of "designtheeverything" with "'''AJ'''" and "Harrison" with "'''Harrison'''"
    transcript = transcript.replace("designtheeverything", "'''AJ'''")
    transcript = transcript.replace("Harrison", "'''Harrison'''")

    # Step 3: Add a colon and three spaces after '''AJ''' and '''Harrison'''
    transcript = re.sub(r"'''AJ'''", "'''AJ''':   ", transcript)
    transcript = re.sub(r"'''Harrison'''", "'''Harrison''':   ", transcript)

    # Step 4: Move <br> before each instance of '''AJ''' and '''Harrison'''
    transcript = re.sub(r"\n<br>'''AJ''':", r"<br>\n'''AJ''':", transcript)
    transcript = re.sub(r"\n<br>'''Harrison''':", r"<br>\n'''Harrison''':", transcript)

    # Step 5: Speaker Formatting
    speaker_pattern = re.compile(r"(AJ|Harrison):\n\s*(.+)", re.DOTALL)

    def format_speaker(match):
        speaker = match.group(1)
        dialogue = match.group(2).replace('\n', ' ').strip()
        return f"'''{speaker}''':   {dialogue}"

    transcript = re.sub(speaker_pattern, format_speaker, transcript)

    # Add <br> at the beginning of every line
    lines = transcript.split('\n')
    formatted_lines = []
    for line in lines:
        if line.strip():  # Ignore lines that only contain whitespace
            formatted_lines.append(f"<br>{line}")

    transcript = '\n'.join(formatted_lines)

    # Step 6: Remove any lingering <br> after AJ or Harrison names
    transcript = re.sub(r"('''AJ''':   |'''Harrison''':   )\n<br>", r"\1", transcript)

    # Step 7: Generate summaries using ChatGPT API
    short_summary = generate_summary(transcript, summary_type="short")
    detailed_summary = generate_summary(transcript, summary_type="detailed")
    
    # Step 8: Wikimedia Page Preparation with summaries
    transcript = (f"=TLDR=\n\n{short_summary}\n\n"
                  f"=Links=\n\n"
                  f"=Summary=\n\n{detailed_summary}\n\n"
                  f"=Transcript=\n\n" + transcript)

    # Corrected line to save the processed transcript
    output_file_path = file_path.replace('.txt', '_processed.txt')
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(transcript)

    messagebox.showinfo("Success", f"Processed transcript saved to {output_file_path}")

    # Step 9: Open the processed file in the default text editor
    os.startfile(output_file_path)

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if file_path:
        file_label.config(text=f"File loaded: {file_path}")
        start_button.config(state=tk.NORMAL)
        start_button.file_path = file_path

def start_processing():
    file_path = start_button.file_path
    if file_path:
        process_transcript(file_path)

def create_gui():
    # Create the main window
    window = tk.Tk()
    window.title("Transcript Processor")

    # Create a label
    label = tk.Label(window, text="Select a text file to process:")
    label.pack(pady=10)

    # Create a file label to show the selected file
    global file_label
    file_label = tk.Label(window, text="No file loaded")
    file_label.pack(pady=5)

    # Create a frame to hold the buttons in one row
    button_frame = tk.Frame(window)
    button_frame.pack(pady=10)

    # Create a button to select a file
    select_button = tk.Button(button_frame, text="Select File", command=select_file)
    select_button.pack(side=tk.LEFT, padx=5)

    # Create a start button, initially disabled
    global start_button
    start_button = tk.Button(button_frame, text="Start", command=start_processing, state=tk.DISABLED)
    start_button.pack(side=tk.LEFT, padx=5)

    # Create a quit button
    quit_button = tk.Button(button_frame, text="Quit", command=window.quit)
    quit_button.pack(side=tk.LEFT, padx=5)

    # Run the GUI loop
    window.mainloop()

# Start the GUI
create_gui()
