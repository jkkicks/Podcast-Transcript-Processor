import re
import os
import openai
import json
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox

# Configurable Hosts List
hosts = []  # No hard-coded hosts, more can be added through the GUI

# Path to the JSON file for storing settings
settings_file = 'transcript_processor_settings.json'

def generate_summary(text, summary_type="short"):
    prompt = "Summarize the following transcript."
    if summary_type == "detailed":
        prompt = "Provide a detailed five-paragraph summary of the following transcript."
    elif summary_type == "short":
        prompt = "Summarize the following transcript in three sentences."

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
    with open(file_path, 'r', encoding='utf-8') as file:
        transcript = file.read()

    # Step 1: Remove timecodes
    transcript = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{2}|\d{2}:\d{2}\.\d{2}', '', transcript)

    # Step 2: Find and replace words based on user input
    for find_entry, replace_entry, _ in find_replace_entries:
        find_word = find_entry.text.strip()
        replace_word = replace_entry.text.strip()
        if find_word:
            transcript = transcript.replace(find_word, replace_word)

    # Step 3: Replace host names with formatted versions
    for host in hosts:
        formatted_host = f"'''{host}''':   "
        transcript = re.sub(rf"\b{host}\b", formatted_host, transcript)

    # Step 4: Ensure the host names are followed by their dialogue on the same line
    for host in hosts:
        formatted_host = f"'''{host}''':   "
        transcript = re.sub(rf"{re.escape(formatted_host)}\s*\n+", f"{formatted_host} ", transcript)

    # Step 5: Add <br> at the beginning of each line that starts with a host's name
    for host in hosts:
        formatted_host = f"'''{host}''':   "
        transcript = re.sub(rf"(?<!<br>)({re.escape(formatted_host)})", r"<br>\1", transcript)

    # Step 6: Remove any extra newlines between host sections
    transcript = re.sub(r"\n{2,}", "\n", transcript)

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

    return output_file_path

class TranscriptProcessorApp(App):
    def build(self):
        self.settings = self.load_settings()
        self.find_replace_entries = []

        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # File Selection
        file_chooser = FileChooserListView(filters=['*.txt'])
        main_layout.add_widget(file_chooser)

        self.file_label = Label(text="No files loaded")
        main_layout.add_widget(self.file_label)

        select_files_button = Button(text="Select Files")
        select_files_button.bind(on_press=lambda x: self.select_files(file_chooser))
        main_layout.add_widget(select_files_button)

        # API Key Entry
        api_key_label = Label(text="Enter your OpenAI API Key:")
        main_layout.add_widget(api_key_label)

        self.api_key_entry = TextInput(text=self.settings.get('api_key', ''), password=True)
        main_layout.add_widget(self.api_key_entry)

        set_api_key_button = Button(text="Set API Key")
        set_api_key_button.bind(on_press=self.set_api_key)
        main_layout.add_widget(set_api_key_button)

        # Hosts Management
        self.host_list_label = Label(text="Hosts: " + ", ".join(hosts))
        main_layout.add_widget(self.host_list_label)

        host_entry = TextInput(hint_text="Enter host name")
        main_layout.add_widget(host_entry)

        add_host_button = Button(text="Add Host")
        add_host_button.bind(on_press=lambda x: self.add_host(host_entry))
        main_layout.add_widget(add_host_button)

        remove_host_spinner = Spinner(text='Select host to remove', values=hosts)
        main_layout.add_widget(remove_host_spinner)

        remove_host_button = Button(text="Remove Host")
        remove_host_button.bind(on_press=lambda x: self.remove_host(remove_host_spinner.text))
        main_layout.add_widget(remove_host_button)

        # Find and Replace
        find_replace_scrollview = ScrollView()
        find_replace_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        find_replace_scrollview.add_widget(find_replace_layout)

        add_find_replace_button = Button(text="Add Find/Replace")
        add_find_replace_button.bind(on_press=lambda x: self.add_find_replace(find_replace_layout))
        main_layout.add_widget(add_find_replace_button)

        main_layout.add_widget(find_replace_scrollview)

        # Actions
        save_settings_button = Button(text="Save Settings")
        save_settings_button.bind(on_press=self.save_settings)
        main_layout.add_widget(save_settings_button)

        load_json_button = Button(text="Load from JSON")
        load_json_button.bind(on_press=self.reload_settings)
        main_layout.add_widget(load_json_button)

        start_button = Button(text="Start Processing", size_hint=(None, None), size=(200, 50))
        start_button.bind(on_press=lambda x: self.process_transcripts(file_chooser.selection))
        main_layout.add_widget(start_button)

        return main_layout

    def select_files(self, file_chooser):
        selected_files = file_chooser.selection
        if selected_files:
            self.file_label.text = f"{len(selected_files)} files loaded"

    def set_api_key(self, instance):
        openai.api_key = self.api_key_entry.text
        display_key = self.api_key_entry.text[:5] + '*' * (len(self.api_key_entry.text) - 5)
        self.api_key_entry.hint_text = f"API Key Set: {display_key}"

    def add_host(self, host_entry):
        new_host = host_entry.text.strip()
        if new_host and new_host not in hosts:
            hosts.append(new_host)
            self.host_list_label.text = "Hosts: " + ", ".join(hosts)
            host_entry.text = ''

    def remove_host(self, host_name):
        if host_name in hosts:
            hosts.remove(host_name)
            self.host_list_label.text = "Hosts: " + ", ".join(hosts)

    def add_find_replace(self, parent_layout):
        find_replace_box = BoxLayout(size_hint_y=None, height=30, spacing=10)
        
        find_input = TextInput(hint_text="Find")
        find_replace_box.add_widget(find_input)
        
        replace_input = TextInput(hint_text="Replace with")
        find_replace_box.add_widget(replace_input)
        
        remove_button = Button(text="Remove")
        remove_button.bind(on_press=lambda x: parent_layout.remove_widget(find_replace_box))
        find_replace_box.add_widget(remove_button)
        
        parent_layout.add_widget(find_replace_box)
        self.find_replace_entries.append((find_input, replace_input, find_replace_box))

    def process_transcripts(self, file_paths):
        if not file_paths:
            return

        for file_path in file_paths:
            processed_file = process_transcript(file_path)
            self.open_file(processed_file)

    def open_file(self, file_path):
        if os.name == 'nt':  # For Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # For MacOS and Linux
            os.system(f"open '{file_path}'")

    def save_settings(self, instance):
        settings = {
            "hosts": hosts,
            "api_key": self.api_key_entry.text.strip(),
            "find_replace": [
                {"find": find_entry.text.strip(), "replace": replace_entry.text.strip()}
                for find_entry, replace_entry, _ in self.find_replace_entries
            ]
        }
        with open(settings_file, 'w') as f:
            json.dump(settings, f)
        self.show_popup("Settings Saved", "Settings have been saved to the JSON file.")

    def reload_settings(self, instance):
        self.settings = self.load_settings()
        self.show_popup("Settings Loaded", "Settings have been reloaded from the JSON file.")

    def load_settings(self):
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                return json.load(f)
        return {}

    def show_popup(self, title, content):
        popup_layout = BoxLayout(orientation='vertical', padding=10)
        popup_label = Label(text=content)
        popup_layout.add_widget(popup_label)
        close_button = Button(text="Close")
        popup_layout.add_widget(close_button)
        popup = Popup(title=title, content=popup_layout, size_hint=(None, None), size=(400, 200))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    TranscriptProcessorApp().run()
