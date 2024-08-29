import re
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import openai
import threading
import json

# Configurable Hosts List
hosts = ['AJ', 'Harrison']  # Default hosts, more can be added through the GUI

# Path to the JSON file for storing settings
settings_file = 'transcript_processor_settings.json'

def generate_summary(text, summary_type="short"):
    prompt = "Summarize the following transcript."
    if summary_type == "detailed":
        prompt = "Provide a detailed five-paragraph summary of the following transcript."
    elif summary_type == "short":
        prompt = "Summarize the following transcript in three sentences."

    # Flip the max tokens for detailed and standard summaries
    max_tokens = 10000 if summary_type == "detailed" else 16384

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        max_tokens=max_tokens
    )
    summary = response.choices[0].message['content'].strip()
    return summary

def process_transcript(file_path):
    status_label.config(text="Processing... Please wait.", fg="red")
    start_button.config(state=tk.DISABLED)  # Disable the start button
    window.update_idletasks()

    with open(file_path, 'r', encoding='utf-8') as file:
        transcript = file.read()

    # Step 1: Remove timecodes
    transcript = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{2}|\d{2}:\d{2}\.\d{2}', '', transcript)

    # Step 2: Find and replace words based on user input
    for find_entry, replace_entry in find_replace_entries:
        find_word = find_entry.get().strip()
        replace_word = replace_entry.get().strip()
        if find_word:
            transcript = transcript.replace(find_word, replace_word)

    # Step 3: Replace host names with formatted versions
    for host in hosts:
        formatted_host = f"'''{host}''':   "
        transcript = transcript.replace(host, formatted_host)

    # Step 4: Move <br> before each instance of the formatted host names
    for host in hosts:
        formatted_host = f"'''{host}''':   "
        transcript = re.sub(rf"\n<br>{re.escape(formatted_host)}", f"<br>\n{formatted_host}", transcript)

    # Step 5: Speaker Formatting
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

    # Step 6: Remove any lingering <br> after host names
    for host in hosts:
        formatted_host = f"'''{host}''':   "
        transcript = re.sub(rf"({re.escape(formatted_host)})\n<br>", r"\1", transcript)

    # Step 7: Generate summaries using ChatGPT API
    short_summary = generate_summary(transcript, summary_type="short")
    detailed_summary = generate_summary(transcript, summary_type="detailed")
    
    # Step 8: Wikimedia Page Preparation with summaries
    transcript = (f"=TLDR=\n\n{short_summary}\n\n"
                  f"=Links=\n\n"
                  f"=Summary=\n\n{detailed_summary}\n\n"
                  f"=Transcript=\n\n" + transcript)

    # Output the processed transcript
    output_file_path = file_path.replace('.txt', '_processed.txt')
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(transcript)

    status_label.config(text="Processing complete. File saved.", fg="green")
    window.update_idletasks()

    messagebox.showinfo("Success", f"Processed transcript saved to {output_file_path}")
    start_button.config(state=tk.NORMAL)  # Re-enable the start button

    # Step 9: Open the processed file in the default text editor
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
        api_key_status_label.config(text="API Key Set", fg="green")
        window.update_idletasks()
        messagebox.showinfo("API Key Set", "Your OpenAI API key has been set.")

def add_find_replace():
    find_label = tk.Label(find_replace_frame, text="Find:")
    find_label.pack(side=tk.LEFT, padx=5)
    find_entry = tk.Entry(find_replace_frame)
    find_entry.pack(side=tk.LEFT, padx=5)

    replace_label = tk.Label(find_replace_frame, text="Replace with:")
    replace_label.pack(side=tk.LEFT, padx=5)
    replace_entry = tk.Entry(find_replace_frame)
    replace_entry.pack(side=tk.LEFT, padx=5)

    find_replace_entries.append((find_entry, replace_entry))

def save_settings():
    settings = {
        "hosts": hosts,
        "api_key": api_key_entry.get().strip(),
        "find_replace": [
            {"find": find_entry.get().strip(), "replace": replace_entry.get().strip()}
            for find_entry, replace_entry in find_replace_entries
        ]
    }
    with open(settings_file, 'w') as f:
        json.dump(settings, f)
    messagebox.showinfo("Settings Saved", "Settings have been saved to the JSON file.")

def load_settings():
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            settings = json.load(f)
            # Load hosts
            global hosts
            hosts = settings.get("hosts", hosts)
            host_list_label.config(text="Hosts: " + ", ".join(hosts))

            # Load API key
            api_key_entry.insert(0, settings.get("api_key", ""))

            # Load find/replace pairs
            for pair in settings.get("find_replace", []):
                add_find_replace()
                find_replace_entries[-1][0].insert(0, pair["find"])
                find_replace_entries[-1][1].insert(0, pair["replace"])

def start_processing():
    status_label.config(text="Starting processing...", fg="blue")
    window.update_idletasks()
    threading.Thread(target=process_transcript_thread).start()

def process_transcript_thread():
    file_path = start_button.file_path
    if file_path:
        process_transcript(file_path)

def create_gui():
    global window, find_replace_frame, find_replace_entries, api_key_entry, host_list_label
    window = tk.Tk()
    window.title("Transcript Processor")

    find_replace_entries = []

    # Load settings from JSON file
    load_settings()

    # Create a label for file selection
    label = tk.Label(window, text="Select a text file to process:")
    label.pack(pady=10)

    # Create a button to select a file
    select_button = tk.Button(window, text="Select File", command=select_file)
    select_button.pack(pady=5)

    # Create a file label to show the selected file
    global file_label
    file_label = tk.Label(window, text="No file loaded")
    file_label.pack(pady=5)

    # Create a frame to hold the find and replace widgets
    find_replace_frame = tk.Frame(window)
    find_replace_frame.pack(pady=10)

    # Create a button to add more find/replace pairs
    add_find_replace_button = tk.Button(window, text="Add Find/Replace", command=add_find_replace)
    add_find_replace_button.pack(pady=10)

    # Create a label to display the list of hosts
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

    # Create a button to save settings to a JSON file
    save_settings_button = tk.Button(window, text="Save Settings", command=save_settings)
    save_settings_button.pack(pady=10)

    # Create a label to show API key status
    global api_key_status_label
    api_key_status_label = tk.Label(window, text="")
    api_key_status_label.pack(pady=5)

    # Create a label to show the processing status
    global status_label
    status_label = tk.Label(window, text="")
    status_label.pack(pady=10)

    # Create a large "Start" button at the bottom
    global start_button
    start_button = tk.Button(window, text="Start", command=start_processing, state=tk.DISABLED, font=("Arial", 16), height=2, width=20)
    start_button.pack(pady=20)

    # Run the GUI loop
    window.mainloop()

# Start the GUI
create_gui()
