import re
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import openai

# Configurable Hosts List
hosts = ['AJ', 'Harrison']  # Default hosts, more can be added through the GUI

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
        max_tokens=10000 if summary_type == "detailed" else 16384
    )
    summary = response.choices[0].message['content'].strip()
    return summary

def process_transcript(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        transcript = file.read()

    # Step 1: Remove timecodes
    transcript = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{2}', '', transcript)

    # Step 2: Replace host names with formatted versions
    for host in hosts:
        formatted_host = f"'''{host}''':   "
        transcript = transcript.replace(host, formatted_host)

    # Step 3: Move <br> before each instance of the formatted host names
    for host in hosts:
        formatted_host = f"'''{host}''':   "
        transcript = re.sub(rf"\n<br>{re.escape(formatted_host)}", f"<br>\n{formatted_host}", transcript)

    # Step 4: Speaker Formatting
    speaker_pattern = re.compile(r"(" + "|".join(re.escape(host) for host in hosts) + r"):\n\s*(.+)", re.DOTALL)

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

    # Step 5: Remove any lingering <br> after host names
    for host in hosts:
        formatted_host = f"'''{host}''':   "
        transcript = re.sub(rf"({re.escape(formatted_host)})\n<br>", r"\1", transcript)

    # Step 6: Generate summaries using ChatGPT API
    short_summary = generate_summary(transcript, summary_type="short")
    detailed_summary = generate_summary(transcript, summary_type="detailed")
    
    # Step 7: Wikimedia Page Preparation with summaries
    transcript = (f"=TLDR=\n\n{short_summary}\n\n"
                  f"=Links=\n\n"
                  f"=Summary=\n\n{detailed_summary}\n\n"
                  f"=Transcript=\n\n" + transcript)

    # Output the processed transcript
    output_file_path = file_path.replace('.txt', '_processed.txt')
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(transcript)

    messagebox.showinfo("Success", f"Processed transcript saved to {output_file_path}")

    # Step 8: Open the processed file in the default text editor
    os.startfile(output_file_path)

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if file_path:
        file_label.config(text=f"File loaded: {file_path}")
        start_button.config(state=tk.NORMAL)
        start_button.file_path = file_path

def add_host():
    new_host = host_entry.get().strip()
    if new_host and new_host not in hosts:
        hosts.append(new_host)
        host_list_label.config(text="Hosts: " + ", ".join(hosts))
        host_entry.delete(0, tk.END)

def set_api_key():
    api_key = api_key_entry.get().strip()
    if api_key:
        openai.api_key = api_key
        messagebox.showinfo("API Key Set", "Your OpenAI API key has been set.")

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

    # Create a label to display the list of hosts
    global host_list_label
    host_list_label = tk.Label(window, text="Hosts: " + ", ".join(hosts))
    host_list_label.pack(pady=5)

    # Create an entry widget to add new hosts
    global host_entry
    host_entry = tk.Entry(window)
    host_entry.pack(pady=5)

    # Create a button to add a new host
    add_host_button = tk.Button(window, text="Add Host", command=add_host)
    add_host_button.pack(pady=5)

    # Create a label for the API key entry
    api_key_label = tk.Label(window, text="Enter your OpenAI API Key:")
    api_key_label.pack(pady=5)

    # Create an entry widget for the API key
    global api_key_entry
    api_key_entry = tk.Entry(window, show="*")  # Masked entry for API key
    api_key_entry.pack(pady=5)

    # Create a button to set the API key
    set_api_key_button = tk.Button(window, text="Set API Key", command=set_api_key)
    set_api_key_button.pack(pady=5)

    # Run the GUI loop
    window.mainloop()

# Start the GUI
create_gui()
