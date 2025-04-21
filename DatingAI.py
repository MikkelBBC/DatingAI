import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, simpledialog, filedialog
import requests
import json
import pyautogui
import time
import os
import pickle
from PIL import Image, ImageTk, ImageGrab
import pytesseract

# Tesseract path - you may need to adjust this for your system
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class Conversation:
    def __init__(self, name, context="", last_message=""):
        self.name = name
        self.context = context
        self.last_message = last_message

class CombinedDatingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dating Assistant Pro")
        self.root.geometry("800x900")  # Increased height to accommodate additional features
        
        # API key - REMEMBER TO REPLACE WITH YOUR OWN
        self.api_key = "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"
        
        # Variables to store data
        self.suggestions = []
        self.conversations = {}  # Dict to store multiple conversations
        self.current_conversation = None
        
        # Image scanning variables
        self.current_image = None
        self.full_screenshot = None
        self.area_window = None
        
        # Folder to save conversations
        self.data_dir = "samtaler"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Different tone options and descriptions
        self.tone_options = {
            "Almindelig": "Giv mig 5 almindelige og naturlige svarmuligheder.",
            "Flirtende": "Giv mig 5 flirtende og charmerende svarmuligheder der viser interesse.",
            "Sjov/Humoristisk": "Giv mig 5 sjove og humoristiske svarmuligheder der kan få hende til at grine.",
            "Drillende": "Giv mig 5 let drillende svarmuligheder der er spøgefulde uden at være for meget.",
            "Dybere samtale": "Giv mig 5 svarmuligheder der kan lede samtalen i en dybere retning med mere substans.",
            "Nyt emne": "Giv mig 5 svarmuligheder der introducerer et helt nyt samtaleemne på en naturlig måde.",
            "Kortfattet": "Giv mig 5 korte og præcise svarmuligheder, der ikke virker for ivrige.",
            "Spørgende": "Giv mig 5 svarmuligheder med interessante spørgsmål der kan holde samtalen i gang."
        }
        
        # Load saved conversations
        self.load_conversations()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create tabs
        self.suggestions_tab = ttk.Frame(self.notebook)
        self.scanner_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.suggestions_tab, text="Svarforslag")
        self.notebook.add(self.scanner_tab, text="Samtale Scanner")
        
        # Create GUI elements for each tab
        self.create_suggestions_widgets()
        self.create_scanner_widgets()
        
        # Create a new conversation if there are none
        if not self.conversations:
            self.new_conversation()
        else:
            # Select the first conversation as default
            first_key = list(self.conversations.keys())[0]
            self.current_conversation = self.conversations[first_key]
            self.update_conversation_display()
            self.update_conversation_dropdown()
            
        # Status bar at bottom of main window
        self.lbl_status = tk.Label(self.root, text="Klar...", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.lbl_status.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_suggestions_widgets(self):
        """Create widgets for the suggestions tab"""
        # Menu for conversations
        menu_frame = tk.Frame(self.suggestions_tab)
        menu_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        tk.Label(menu_frame, text="Aktiv samtale:").grid(row=0, column=0, sticky="w")
        
        self.conversation_var = tk.StringVar()
        self.conversation_dropdown = ttk.Combobox(menu_frame, textvariable=self.conversation_var, width=25)
        self.conversation_dropdown.grid(row=0, column=1, padx=10)
        self.conversation_dropdown.bind("<<ComboboxSelected>>", self.on_conversation_selected)
        
        conversation_buttons = tk.Frame(menu_frame)
        conversation_buttons.grid(row=0, column=2, padx=5)
        
        self.btn_new = tk.Button(conversation_buttons, text="Ny", command=self.new_conversation, width=8)
        self.btn_new.grid(row=0, column=0, padx=2)
        
        self.btn_save = tk.Button(conversation_buttons, text="Gem", command=self.save_current_conversation, width=8)
        self.btn_save.grid(row=0, column=1, padx=2)
        
        self.btn_delete = tk.Button(conversation_buttons, text="Slet", command=self.delete_conversation, width=8)
        self.btn_delete.grid(row=0, column=2, padx=2)
        
        # Conversation history
        tk.Label(self.suggestions_tab, text="Samtalehistorik:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.txt_context = scrolledtext.ScrolledText(self.suggestions_tab, width=75, height=10)
        self.txt_context.grid(row=2, column=0, padx=10, pady=5)
        
        # Her last message
        tk.Label(self.suggestions_tab, text="Hendes seneste besked:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.txt_last_message = scrolledtext.ScrolledText(self.suggestions_tab, width=75, height=3)
        self.txt_last_message.grid(row=4, column=0, padx=10, pady=5)
        
        # Extra instructions
        tk.Label(self.suggestions_tab, text="Ekstra instrukser (valgfrit):").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.txt_extra_instructions = scrolledtext.ScrolledText(self.suggestions_tab, width=75, height=2)
        self.txt_extra_instructions.grid(row=6, column=0, padx=10, pady=5)
        
        # Select tone
        tone_frame = tk.Frame(self.suggestions_tab)
        tone_frame.grid(row=7, column=0, padx=10, pady=5, sticky="w")
        
        tk.Label(tone_frame, text="Vælg tone:").grid(row=0, column=0, sticky="w")
        
        self.tone_var = tk.StringVar()
        self.tone_var.set(list(self.tone_options.keys())[0])  # Default tone
        
        self.tone_dropdown = ttk.Combobox(tone_frame, textvariable=self.tone_var, values=list(self.tone_options.keys()), width=25)
        self.tone_dropdown.grid(row=0, column=1, padx=10)
        
        # Buttons to generate suggestions and add messages
        button_frame = tk.Frame(self.suggestions_tab)
        button_frame.grid(row=8, column=0, padx=10, pady=10)
        
        self.btn_generate = tk.Button(button_frame, text="Generer Svarforslag", command=self.generate_suggestions, width=20)
        self.btn_generate.grid(row=0, column=0, padx=5)
        
        self.btn_add_message = tk.Button(button_frame, text="Tilføj hendes besked", command=self.add_received_message, width=20)
        self.btn_add_message.grid(row=0, column=1, padx=5)
        
        # Import from scanner button - NEW: Link to scanner
        self.btn_import_from_scanner = tk.Button(button_frame, text="Importer fra scanner", command=self.import_from_scanner, width=20)
        self.btn_import_from_scanner.grid(row=0, column=2, padx=5)
        
        # Suggestions list
        tk.Label(self.suggestions_tab, text="Svarforslag (vælg eller tryk på tal):").grid(row=9, column=0, sticky="w", padx=10, pady=5)
        
        self.listbox_suggestions = tk.Listbox(self.suggestions_tab, width=75, height=10)
        self.listbox_suggestions.grid(row=10, column=0, padx=10, pady=5)
        self.listbox_suggestions.bind("<Key>", self.key_pressed)
        self.listbox_suggestions.bind("<Double-Button-1>", lambda e: self.send_to_messenger())
        
        # Send and Print buttons
        button_frame2 = tk.Frame(self.suggestions_tab)
        button_frame2.grid(row=11, column=0, padx=10, pady=10)
        
        self.btn_send = tk.Button(button_frame2, text="Send til Messenger", command=self.send_to_messenger, width=20, height=2)
        self.btn_send.grid(row=0, column=0, padx=5)
        
        self.btn_type = tk.Button(button_frame2, text="Udskriv Tekst", command=self.type_message, width=20, height=2)
        self.btn_type.grid(row=0, column=1, padx=5)
    
    def create_scanner_widgets(self):
        """Create widgets for the scanner tab"""
        # Control panel
        control_panel = tk.Frame(self.scanner_tab)
        control_panel.pack(fill=tk.X, pady=5)
        
        # Buttons
        upload_btn = tk.Button(control_panel, text="Upload billede", command=self.upload_image)
        upload_btn.pack(side=tk.LEFT, padx=5)
        
        screenshot_btn = tk.Button(control_panel, text="Tag skærmbillede", command=self.select_area)
        screenshot_btn.pack(side=tk.LEFT, padx=5)
        
        scan_btn = tk.Button(control_panel, text="Scan samtale", command=self.scan_conversation)
        scan_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(control_panel, text="Slet billede", command=self.clear_image)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # Send to suggestions button - NEW: Link to suggestions
        send_to_suggestions_btn = tk.Button(control_panel, text="Send til Svarforslag", command=self.send_to_suggestions)
        send_to_suggestions_btn.pack(side=tk.LEFT, padx=5)
        
        # Image area
        image_frame = tk.LabelFrame(self.scanner_tab, text="Billede")
        image_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.image_label = tk.Label(image_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Result area
        result_frame = tk.LabelFrame(self.scanner_tab, text="Samtaleresultat")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=10)
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    # INTEGRATION METHODS
    
    def import_from_scanner(self):
        """Import conversation from the scanner to the suggestions tab"""
        # Switch to scanner tab
        self.notebook.select(self.scanner_tab)
        messagebox.showinfo("Information", "Tag et skærmbillede eller upload et billede af samtalen, og klik derefter på 'Send til Svarforslag' efter scanning.")
    
    def send_to_suggestions(self):
        """Send scanned conversation to suggestions tab"""
        # Check if we have scanned text
        scanned_text = self.result_text.get("1.0", tk.END).strip()
        if not scanned_text:
            messagebox.showinfo("Information", "Scan et billede først")
            return
            
        # Process the scanned text
        processed_text = self.process_for_suggestions(scanned_text)
        
        # Update the conversation history in suggestions tab
        current_context = self.txt_context.get("1.0", tk.END).strip()
        
        # Either update existing or create new
        if current_context:
            # Add to existing conversation
            self.txt_context.delete("1.0", tk.END)
            self.txt_context.insert("1.0", current_context + "\n" + processed_text)
        else:
            # New conversation
            self.txt_context.insert("1.0", processed_text)
        
        # Switch to suggestions tab
        self.notebook.select(self.suggestions_tab)
        
        # Save the updated conversation
        self.save_current_conversation_state()
        self.save_current_conversation()
        
        self.lbl_status.config(text="Samtale importeret fra scanner!")
    
    def process_for_suggestions(self, scanned_text):
        """Process scanned text into suggestion-friendly format"""
        processed_lines = []
        lines = scanned_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("DIG (højre):"):
                # Extract just the message content
                message = line.replace("DIG (højre):", "").strip()
                processed_lines.append(f"Dig: {message}")
            elif line.startswith("DEM (venstre):"):
                # Extract just the message content
                message = line.replace("DEM (venstre):", "").strip()
                processed_lines.append(f"Hende: {message}")
                # Also update the last message field with her latest message
                self.txt_last_message.delete("1.0", tk.END)
                self.txt_last_message.insert("1.0", message)
            elif line.startswith("UKENDT:"):
                # For unknown, try to guess based on content
                message = line.replace("UKENDT:", "").strip()
                processed_lines.append(f"Ukendt: {message}")
        
        return "\n".join(processed_lines)
    
    # SUGGESTIONS TAB METHODS
    
    def load_conversations(self):
        """Load saved conversations"""
        try:
            files = [f for f in os.listdir(self.data_dir) if f.endswith('.conv')]
            for file in files:
                file_path = os.path.join(self.data_dir, file)
                with open(file_path, 'rb') as f:
                    conversation = pickle.load(f)
                    self.conversations[conversation.name] = conversation
        except Exception as e:
            messagebox.showwarning("Advarsel", f"Kunne ikke indlæse samtaler: {str(e)}")
    
    def save_conversations(self):
        """Save all conversations"""
        for name, conversation in self.conversations.items():
            try:
                file_path = os.path.join(self.data_dir, f"{name}.conv")
                with open(file_path, 'wb') as f:
                    pickle.dump(conversation, f)
            except Exception as e:
                messagebox.showwarning("Advarsel", f"Kunne ikke gemme samtale '{name}': {str(e)}")
    
    def update_conversation_dropdown(self):
        """Update dropdown with conversation names"""
        self.conversation_dropdown['values'] = list(self.conversations.keys())
        if self.current_conversation:
            self.conversation_var.set(self.current_conversation.name)
    
    def update_conversation_display(self):
        """Update GUI with the selected conversation"""
        if self.current_conversation:
            self.txt_context.delete("1.0", tk.END)
            self.txt_context.insert("1.0", self.current_conversation.context)
            
            self.txt_last_message.delete("1.0", tk.END)
            self.txt_last_message.insert("1.0", self.current_conversation.last_message)
    
    def save_current_conversation_state(self):
        """Save the current state of the conversation"""
        if self.current_conversation:
            self.current_conversation.context = self.txt_context.get("1.0", tk.END).strip()
            self.current_conversation.last_message = self.txt_last_message.get("1.0", tk.END).strip()
    
    def new_conversation(self):
        """Create a new conversation"""
        name = simpledialog.askstring("Ny samtale", "Indtast navn på den nye samtale:")
        if name and name.strip():
            name = name.strip()
            if name in self.conversations:
                messagebox.showwarning("Advarsel", f"En samtale med navnet '{name}' findes allerede.")
                return
            
            self.save_current_conversation_state()  # Save the current conversation first
            
            # Create new conversation
            self.conversations[name] = Conversation(name)
            self.current_conversation = self.conversations[name]
            
            # Update GUI
            self.update_conversation_dropdown()
            self.txt_context.delete("1.0", tk.END)
            self.txt_last_message.delete("1.0", tk.END)
            self.listbox_suggestions.delete(0, tk.END)
            self.suggestions = []
            
            self.save_conversations()  # Save all conversations
            self.lbl_status.config(text=f"Ny samtale '{name}' oprettet.")
    
    def on_conversation_selected(self, event):
        """Handle selection of conversation from dropdown"""
        selected_name = self.conversation_var.get()
        if selected_name in self.conversations:
            # Save the current conversation first
            self.save_current_conversation_state()
            
            # Switch to the selected conversation
            self.current_conversation = self.conversations[selected_name]
            self.update_conversation_display()
            self.listbox_suggestions.delete(0, tk.END)
            self.suggestions = []
            
            self.lbl_status.config(text=f"Skiftede til samtale: '{selected_name}'")
    
    def save_current_conversation(self):
        """Save the current conversation"""
        if self.current_conversation:
            self.save_current_conversation_state()
            try:
                file_path = os.path.join(self.data_dir, f"{self.current_conversation.name}.conv")
                with open(file_path, 'wb') as f:
                    pickle.dump(self.current_conversation, f)
                self.lbl_status.config(text=f"Samtale '{self.current_conversation.name}' gemt.")
            except Exception as e:
                messagebox.showwarning("Advarsel", f"Kunne ikke gemme samtale: {str(e)}")
    
    def delete_conversation(self):
        """Delete the current conversation"""
        if self.current_conversation:
            name = self.current_conversation.name
            confirm = messagebox.askyesno("Bekræft sletning", f"Er du sikker på, at du vil slette samtalen '{name}'?")
            if confirm:
                try:
                    # Delete file
                    file_path = os.path.join(self.data_dir, f"{name}.conv")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    # Remove from dictionary
                    del self.conversations[name]
                    
                    # Switch to another conversation if possible
                    if self.conversations:
                        self.current_conversation = list(self.conversations.values())[0]
                    else:
                        self.conversations["Standard"] = Conversation("Standard")
                        self.current_conversation = self.conversations["Standard"]
                    
                    self.update_conversation_dropdown()
                    self.update_conversation_display()
                    self.lbl_status.config(text=f"Samtale '{name}' slettet.")
                except Exception as e:
                    messagebox.showwarning("Advarsel", f"Kunne ikke slette samtale: {str(e)}")
    
    def generate_suggestions(self):
        """Generate response suggestions using ChatGPT API"""
        try:
            self.lbl_status.config(text="Genererer forslag...")
            self.root.update()
            
            # Clear previous suggestions
            self.listbox_suggestions.delete(0, tk.END)
            self.suggestions = []
            
            # Get data from input fields
            context = self.txt_context.get("1.0", tk.END).strip()
            last_message = self.txt_last_message.get("1.0", tk.END).strip()
            extra_instructions = self.txt_extra_instructions.get("1.0", tk.END).strip()
            selected_tone = self.tone_var.get()
            tone_instruction = self.tone_options[selected_tone]
            
            # Save the current state of the conversation
            self.save_current_conversation_state()
            
            # Prepare system message based on tone and extra instructions
            system_message = ("Du er en assistent der skal hjælpe med at generere gode, naturlige " 
                             "og varierede svar til en samtale med en pige. ")
            
            if extra_instructions:
                system_message += f"Følg disse specifikke instrukser: {extra_instructions}. "
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Samtalehistorik: {context}\n\nHun skrev sidst: {last_message}\n\n{tone_instruction}"}
                ],
                "max_tokens": 500
            }
            
            # Send request to API
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(data))
            response_json = response.json()
            
            # Process response
            if "choices" in response_json and len(response_json["choices"]) > 0:
                assistant_response = response_json["choices"][0]["message"]["content"]
                
                # Unpack response suggestions and remove all quotation marks
                lines = assistant_response.split("\n")
                for line in lines:
                    line = line.strip().replace('"', '')
                    if line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.") or line.startswith("5."):
                        # Remove the number and keep only the answer itself
                        suggestion = line[line.index(".")+1:].strip()
                        
                        # Save the clean suggestion (without number and without quotation marks)
                        self.suggestions.append(suggestion)
                        
                        # Insert in listbox without quotation marks
                        current_index = len(self.suggestions)
                        self.listbox_suggestions.insert(tk.END, f"{current_index}. {suggestion}")
                
                self.lbl_status.config(text=f"Forslag genereret i tone: {selected_tone}!")
            else:
                error_message = response_json.get("error", {}).get("message", "Ukendt fejl")
                self.lbl_status.config(text=f"Fejl: {error_message}")
                messagebox.showerror("API Fejl", f"Kunne ikke generere forslag: {error_message}")
                
        except Exception as e:
            self.lbl_status.config(text=f"Fejl: {str(e)}")
            messagebox.showerror("Fejl", f"En fejl opstod: {str(e)}")
    
    def send_to_messenger(self):
        """Send the selected response to Messenger with Enter"""
        selected_index = self.listbox_suggestions.curselection()
        
        if selected_index:
            selected_index = int(selected_index[0])
            if 0 <= selected_index < len(self.suggestions):
                selected_suggestion = self.suggestions[selected_index]
                
                # Give the user time to switch to the right window
                self._perform_text_action(selected_suggestion, press_enter=True)
                
                self.lbl_status.config(text="Besked sendt!")
            else:
                messagebox.showinfo("Information", "Ugyldigt valg.")
        else:
            messagebox.showinfo("Information", "Vælg et forslag først.")
    
    def type_message(self):
        """Type the text without pressing Enter"""
        selected_index = self.listbox_suggestions.curselection()
        
        if selected_index:
            selected_index = int(selected_index[0])
            if 0 <= selected_index < len(self.suggestions):
                selected_suggestion = self.suggestions[selected_index]
                
                # Give the user time to switch to the right window
                self._perform_text_action(selected_suggestion, press_enter=False)
                
                self.lbl_status.config(text="Tekst udskrevet!")
            else:
                messagebox.showinfo("Information", "Ugyldigt valg.")
        else:
            messagebox.showinfo("Information", "Vælg et forslag først.")
    
    def _perform_text_action(self, text, press_enter=True):
        """Common function to write text with or without Enter"""
        # Give the user time to switch to the right window
        countdown_time = 5
        
        for i in range(countdown_time, 0, -1):
            self.lbl_status.config(text=f"Skift til det rette vindue nu ({i} sekunder)...")
            self.root.update()
            time.sleep(1)
        
        # Remove all quotation marks from the text
        output_text = text.replace('"', '')
        
        # Simulate keyboard input
        pyautogui.typewrite(output_text)
        
        if press_enter:
            pyautogui.press('enter')
        
        # Update conversation history
        context = self.txt_context.get("1.0", tk.END).strip()
        context += f"\nDig: {output_text}"
        self.txt_context.delete("1.0", tk.END)
        self.txt_context.insert("1.0", context)
        
        # Clear last message field
        self.txt_last_message.delete("1.0", tk.END)
        
        # Save conversation
        self.save_current_conversation_state()
        self.save_current_conversation()
    
    def add_received_message(self):
        """Add recipient's response to conversation history"""
        last_message = self.txt_last_message.get("1.0", tk.END).strip()
        
        if last_message:
            # Update conversation history
            context = self.txt_context.get("1.0", tk.END).strip()
            context += f"\nHende: {last_message}"
            self.txt_context.delete("1.0", tk.END)
            self.txt_context.insert("1.0", context)
            
            # Clear last message field
            self.txt_last_message.delete("1.0", tk.END)
            
            # Save conversation
            self.save_current_conversation_state()
            self.save_current_conversation()
            
            self.lbl_status.config(text="Hendes besked tilføjet til historikken.")
        else:
            messagebox.showinfo("Information", "Indtast hendes besked først.")
    
    def key_pressed(self, event):
        """Handle key press in listbox"""
        if event.char.isdigit():
            digit = int(event.char)
            if 1 <= digit <= len(self.suggestions):
                self.listbox_suggestions.selection_clear(0, tk.END)
                self.listbox_suggestions.selection_set(digit-1)
                self.listbox_suggestions.see(digit-1)
                self.send_to_messenger()
    
    # SCANNER TAB METHODS
    
    def upload_image(self):
        """Upload an image from file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Billedfiler", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        
        if file_path:
            try:
                self.current_image = Image.open(file_path)
                self.display_image(self.current_image)
                self.lbl_status.config(text=f"Billede indlæst: {os.path.basename(file_path)}")
            except Exception as e:
                self.lbl_status.config(text=f"Fejl ved indlæsning: {str(e)}")
    
    def select_area(self):
        """New method: First take a full screenshot and then select the area"""
        # Take a complete screenshot
        try:
            self.lbl_status.config(text="Tager fuldt skærmbillede...")
            self.full_screenshot = ImageGrab.grab(all_screens=True)
            
            # Hide main window
            self.root.withdraw()
            
            # Create a window to show the full screenshot
            self.area_window = tk.Toplevel(self.root)
            self.area_window.attributes('-fullscreen', True)
            self.area_window.title("Vælg område")
            
            # Convert image to PhotoImage
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Adjust image to screen size if necessary
            if self.full_screenshot.width > screen_width or self.full_screenshot.height > screen_height:
                self.full_screenshot = self.full_screenshot.resize((screen_width, screen_height), Image.LANCZOS)
            
            # Convert to PhotoImage
            self.tk_image = ImageTk.PhotoImage(self.full_screenshot)
            
            # Create canvas with the image
            self.canvas = tk.Canvas(self.area_window, width=screen_width, height=screen_height)
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
            
            # Variables for selection
            self.start_x = 0
            self.start_y = 0
            self.rect = None
            
            # Instruction text (displayed on top of the image)
            self.canvas.create_text(
                screen_width // 2, 30, 
                text="Træk for at vælge område - ESC/Q for at annullere", 
                fill="red", font=("Arial", 16, "bold")
            )
            
            # Bind events
            self.canvas.bind("<ButtonPress-1>", self.on_area_start)
            self.canvas.bind("<B1-Motion>", self.on_area_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_area_release)
            self.area_window.bind("<Escape>", self.cancel_area_selection)
            self.area_window.bind("q", self.cancel_area_selection)
            self.area_window.bind("Q", self.cancel_area_selection)
            
            # Focus on the window
            self.area_window.focus_force()
            
        except Exception as e:
            self.root.deiconify()
            self.lbl_status.config(text=f"Fejl ved skærmbillede: {str(e)}")
    
    def on_area_start(self, event):
        """Mouse button down - start area"""
        self.start_x = event.x
        self.start_y = event.y
        
        # Delete existing rectangle
        if self.rect:
            self.canvas.delete(self.rect)
        
        # Create new rectangle
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )
    
    def on_area_drag(self, event):
        """Mouse is dragged - update area"""
        if self.rect:
            # Update rectangle
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    
    def on_area_release(self, event):
        """Mouse button up - finish area"""
        if not self.rect:
            return
            
        # Calculate coordinates (ensure that x1 < x2 and y1 < y2)
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        
        # Check area size
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            # Area too small
            self.lbl_status.config(text="Området er for lille. Prøv igen.")
            return
        
        try:
            # Crop the full screenshot to the selected area
            self.current_image = self.full_screenshot.crop((x1, y1, x2, y2))
            
            # Close area window
            self.area_window.destroy()
            self.area_window = None
            
            # Show main window again
            self.root.deiconify()
            
            # Show the cropped image
            self.display_image(self.current_image)
            
            # Update status
            self.lbl_status.config(text=f"Område valgt: {x2-x1}x{y2-y1} pixels")
            
        except Exception as e:
            if self.area_window:
                self.area_window.destroy()
                self.area_window = None
            self.root.deiconify()
            self.lbl_status.config(text=f"Fejl ved beskæring: {str(e)}")
    
    def cancel_area_selection(self, event=None):
        """Cancel area selection"""
        if self.area_window:
            self.area_window.destroy()
            self.area_window = None
        
        self.root.deiconify()
        self.lbl_status.config(text="Områdevalg annulleret")
    
    def display_image(self, img):
        """Display image in the interface"""
        if img is None:
            return
            
        # Make a copy of the image
        display_img = img.copy()
        
        # Get label dimensions
        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()
        
        # Use default dimensions if label is not visible yet
        if label_width <= 1:
            label_width = 600
        if label_height <= 1:
            label_height = 300
        
        # Adjust image to label size
        img_width, img_height = display_img.size
        ratio = min(label_width/img_width, label_height/img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        display_img = display_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Display image
        tk_img = ImageTk.PhotoImage(display_img)
        self.image_label.config(image=tk_img)
        self.image_label.image = tk_img  # Keep reference
    
    def clear_image(self):
        """Remove the current image"""
        self.current_image = None
        self.image_label.config(image='')
        self.result_text.delete(1.0, tk.END)
        self.lbl_status.config(text="Billede slettet")
    
    def scan_conversation(self):
        """Scan the image for text"""
        if self.current_image is None:
            self.lbl_status.config(text="Intet billede at scanne")
            return
        
        try:
            self.lbl_status.config(text="Scanner billede...")
            self.root.update()
            
            # Try to scan with Danish language, fall back to English
            try:
                text = pytesseract.image_to_string(self.current_image, lang='dan')
            except:
                text = pytesseract.image_to_string(self.current_image)
            
            # Process the text
            result = self.process_conversation(text)
            
            # Show the result
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result)
            
            self.lbl_status.config(text="Scanning fuldført")
        except Exception as e:
            self.lbl_status.config(text=f"Fejl ved scanning: {str(e)}")
    
    def process_conversation(self, text):
        """Process text to identify message types"""
        lines = text.split('\n')
        result_lines = []
        
        # Keywords to identify message types - these can be improved with machine learning in future versions
        # The keywords below are examples and might need to be adjusted based on typical conversations
        your_message_keywords = ["Jep", "Får", "Bare kom", "Sådan ik", "længt væk", "bor", "hvor du bor", 
                               "Jeg", "Tak", "Super", "Fedt", "Hvad med dig", "Skal vi", "Send", 
                               "Smiler", "Hvornår", "Jeg synes", "Helt sikkert"]
        
        their_message_keywords = ["Er det i dag", "Fuck måske", "Hvor er det", "Fair okay", "Men kommer", 
                               "arbejdstøj", "Mårslev", "Hej", "Hvad så", "Hvordan", "Jeg er", 
                               "Måske", "Har du", "Kan du", "Skal vi", "Ved ikke", "Hvad laver du"]
        
        # Detect if text is on the right side based on indentation (specific to Messenger layout)
        def is_right_side(text):
            # If text starts with multiple spaces, it's likely on the right side
            if text.startswith("    ") or text.startswith("\t") or "      " in text:
                return True
            return False
        
        # Process each line
        last_position = None
        current_message = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                # Save any current message before continuing
                if current_message and last_position is not None:
                    if last_position == "right":
                        result_lines.append(f"DIG (højre): {current_message.strip()}")
                    else:
                        result_lines.append(f"DEM (venstre): {current_message.strip()}")
                    current_message = ""
                continue
            
            # Try to determine if this line is yours or theirs based on position and keywords
            position_guess = "right" if is_right_side(line) else "left"
            
            # Additional check based on keywords
            if any(keyword in line for keyword in your_message_keywords):
                position_guess = "right"
            elif any(keyword in line for keyword in their_message_keywords):
                position_guess = "left"
                
            # If we're switching sides, save the current message
            if last_position is not None and position_guess != last_position and current_message:
                if last_position == "right":
                    result_lines.append(f"DIG (højre): {current_message.strip()}")
                else:
                    result_lines.append(f"DEM (venstre): {current_message.strip()}")
                current_message = ""
            
            # Add current line to the message
            current_message += line + " "
            last_position = position_guess
        
        # Save the last message if there is one
        if current_message and last_position is not None:
            if last_position == "right":
                result_lines.append(f"DIG (højre): {current_message.strip()}")
            else:
                result_lines.append(f"DEM (venstre): {current_message.strip()}")
        
        # If we couldn't determine any messages, just return the raw text
        if not result_lines:
            return "Kunne ikke genkende beskedmønster. Rå tekst:\n\n" + text
            
        return '\n'.join(result_lines)

# Main function to start the application
def main():
    root = tk.Tk()
    app = CombinedDatingApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()