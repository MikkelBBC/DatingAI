import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, simpledialog, filedialog
import requests
import json
import pyautogui
import time
import os
import pickle

class Conversation:
    def __init__(self, name, context="", last_message=""):
        self.name = name
        self.context = context
        self.last_message = last_message

class ChatGPTMessengerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ChatGPT Messenger Assistent")
        self.root.geometry("600x800")
        
        # API-nøgle - HUSK AT ERSTATTE MED DIN EGEN
        self.api_key = "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"
        
        # Variabler til at gemme data
        self.suggestions = []
        self.conversations = {}  # Dict til at gemme flere samtaler
        self.current_conversation = None
        
        # Mappe til at gemme samtaler
        self.data_dir = "samtaler"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Forskellige tone-muligheder og beskrivelser
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
        
        # Indlæs gemte samtaler
        self.load_conversations()
        
        # GUI elementer
        self.create_widgets()
        
        # Opret en ny samtale hvis der ikke er nogen
        if not self.conversations:
            self.new_conversation()
        else:
            # Vælg den første samtale som standard
            first_key = list(self.conversations.keys())[0]
            self.current_conversation = self.conversations[first_key]
            self.update_conversation_display()
            self.update_conversation_dropdown()
        
    def create_widgets(self):
        # Menu til samtaler
        menu_frame = tk.Frame(self.root)
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
        
        # Samtalehistorik
        tk.Label(self.root, text="Samtalehistorik:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.txt_context = scrolledtext.ScrolledText(self.root, width=65, height=10)
        self.txt_context.grid(row=2, column=0, padx=10, pady=5)
        
        # Hendes sidste besked
        tk.Label(self.root, text="Hendes seneste besked:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.txt_last_message = scrolledtext.ScrolledText(self.root, width=65, height=3)
        self.txt_last_message.grid(row=4, column=0, padx=10, pady=5)
        
        # Ekstra instrukser
        tk.Label(self.root, text="Ekstra instrukser (valgfrit):").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.txt_extra_instructions = scrolledtext.ScrolledText(self.root, width=65, height=2)
        self.txt_extra_instructions.grid(row=6, column=0, padx=10, pady=5)
        
        # Vælg tone
        tone_frame = tk.Frame(self.root)
        tone_frame.grid(row=7, column=0, padx=10, pady=5, sticky="w")
        
        tk.Label(tone_frame, text="Vælg tone:").grid(row=0, column=0, sticky="w")
        
        self.tone_var = tk.StringVar()
        self.tone_var.set(list(self.tone_options.keys())[0])  # Standard tone
        
        self.tone_dropdown = ttk.Combobox(tone_frame, textvariable=self.tone_var, values=list(self.tone_options.keys()), width=25)
        self.tone_dropdown.grid(row=0, column=1, padx=10)
        
        # Citationstegn fjernet helt - vi bruger ikke denne variabel længere
        # self.quote_var = tk.BooleanVar()
        # self.quote_var.set(False)
        # self.quote_check = tk.Checkbutton(tone_frame, text="Inkluder citationstegn i svar", 
        #                                  variable=self.quote_var, command=self.update_quotes_display)
        # self.quote_check.grid(row=0, column=2, padx=10)
        
        # Knapper til at generere forslag og tilføje beskeder
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=8, column=0, padx=10, pady=10)
        
        self.btn_generate = tk.Button(button_frame, text="Generer Svarforslag", command=self.generate_suggestions, width=20)
        self.btn_generate.grid(row=0, column=0, padx=5)
        
        self.btn_add_message = tk.Button(button_frame, text="Tilføj hendes besked", command=self.add_received_message, width=20)
        self.btn_add_message.grid(row=0, column=1, padx=5)
        
        # Import fra screenshot knap
        self.btn_import = tk.Button(button_frame, text="Importer fra screenshot", command=self.import_conversation, width=20)
        self.btn_import.grid(row=0, column=2, padx=5)
        
        # Svarforslag liste
        tk.Label(self.root, text="Svarforslag (vælg eller tryk på tal):").grid(row=9, column=0, sticky="w", padx=10, pady=5)
        
        self.listbox_suggestions = tk.Listbox(self.root, width=65, height=10)
        self.listbox_suggestions.grid(row=10, column=0, padx=10, pady=5)
        self.listbox_suggestions.bind("<Key>", self.key_pressed)
        self.listbox_suggestions.bind("<Double-Button-1>", lambda e: self.send_to_messenger())
        
        # Send og Udskriv knapper
        button_frame2 = tk.Frame(self.root)
        button_frame2.grid(row=11, column=0, padx=10, pady=10)
        
        self.btn_send = tk.Button(button_frame2, text="Send til Messenger", command=self.send_to_messenger, width=20, height=2)
        self.btn_send.grid(row=0, column=0, padx=5)
        
        self.btn_type = tk.Button(button_frame2, text="Udskriv Tekst", command=self.type_message, width=20, height=2)
        self.btn_type.grid(row=0, column=1, padx=5)
        
        # Status label
        self.lbl_status = tk.Label(self.root, text="Klar...")
        self.lbl_status.grid(row=12, column=0, sticky="w", padx=10, pady=5)
    
    def import_conversation(self):
        """Importerer samtale fra et screenshot"""
        import_text = simpledialog.askstring("Importér samtale", 
                                           "Indsæt tekst fra dit samtale-screenshot.\n" + 
                                           "Tekst i venstre side tolkes som 'Hende'\n" + 
                                           "Tekst i højre side tolkes som 'Dig'", 
                                           parent=self.root)
        
        if not import_text:
            return
        
        # Fjern eventuelle citationstegn fra teksten
        import_text = import_text.replace('"', '')
        
        # Nulstil samtalen
        current_context = ""
        
        # Del teksten op i linjer
        lines = import_text.split('\n')
        last_position = None  # venstre eller højre
        current_message = ""
        
        # Funktion til at afgøre om en linje er på venstre eller højre side
        def is_right_side(text):
            # Hvis teksten starter med flere mellemrum er det sandsynligvis højre side
            if text.startswith("    ") or text.startswith("\t") or "      " in text:
                return True
            # Ellers antager vi det er venstre side
            return False
        
        for line in lines:
            if not line.strip():
                # Gem eventuel nuværende besked før vi går videre
                if current_message and last_position is not None:
                    if last_position == "right":
                        current_context += f"Dig: {current_message.strip()}\n"
                    else:
                        current_context += f"Hende: {current_message.strip()}\n"
                    current_message = ""
                continue
            
            # Afgør om linjen er på højre eller venstre side
            current_position = "right" if is_right_side(line) else "left"
            
            # Hvis vi skifter side, gemmer vi den nuværende besked
            if last_position is not None and current_position != last_position and current_message:
                if last_position == "right":
                    current_context += f"Dig: {current_message.strip()}\n"
                else:
                    current_context += f"Hende: {current_message.strip()}\n"
                current_message = ""
            
            # Tilføj den nuværende linje til beskeden
            current_message += line.strip() + " "
            last_position = current_position
        
        # Gem den sidste besked hvis der er en
        if current_message and last_position is not None:
            if last_position == "right":
                current_context += f"Dig: {current_message.strip()}\n"
            else:
                current_context += f"Hende: {current_message.strip()}\n"
        
        # Opdater samtalehistorikken
        if current_context:
            self.txt_context.delete("1.0", tk.END)
            self.txt_context.insert("1.0", current_context.strip())
            
            # Gem opdateringen
            self.save_current_conversation_state()
            self.save_current_conversation()
            
            self.lbl_status.config(text="Samtale importeret!")
        else:
            messagebox.showinfo("Information", "Ingen gyldig samtalehistorik fundet.")
    
    def load_conversations(self):
        """Indlæser gemte samtaler"""
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
        """Gemmer alle samtaler"""
        for name, conversation in self.conversations.items():
            try:
                file_path = os.path.join(self.data_dir, f"{name}.conv")
                with open(file_path, 'wb') as f:
                    pickle.dump(conversation, f)
            except Exception as e:
                messagebox.showwarning("Advarsel", f"Kunne ikke gemme samtale '{name}': {str(e)}")
    
    def update_conversation_dropdown(self):
        """Opdaterer dropdown med samtale-navne"""
        self.conversation_dropdown['values'] = list(self.conversations.keys())
        if self.current_conversation:
            self.conversation_var.set(self.current_conversation.name)
    
    def update_conversation_display(self):
        """Opdaterer GUI med den valgte samtale"""
        if self.current_conversation:
            self.txt_context.delete("1.0", tk.END)
            self.txt_context.insert("1.0", self.current_conversation.context)
            
            self.txt_last_message.delete("1.0", tk.END)
            self.txt_last_message.insert("1.0", self.current_conversation.last_message)
    
    def save_current_conversation_state(self):
        """Gemmer den aktuelle tilstand af samtalen"""
        if self.current_conversation:
            self.current_conversation.context = self.txt_context.get("1.0", tk.END).strip()
            self.current_conversation.last_message = self.txt_last_message.get("1.0", tk.END).strip()
    
    def new_conversation(self):
        """Opretter en ny samtale"""
        name = simpledialog.askstring("Ny samtale", "Indtast navn på den nye samtale:")
        if name and name.strip():
            name = name.strip()
            if name in self.conversations:
                messagebox.showwarning("Advarsel", f"En samtale med navnet '{name}' findes allerede.")
                return
            
            self.save_current_conversation_state()  # Gem den aktuelle samtale først
            
            # Opret ny samtale
            self.conversations[name] = Conversation(name)
            self.current_conversation = self.conversations[name]
            
            # Opdater GUI
            self.update_conversation_dropdown()
            self.txt_context.delete("1.0", tk.END)
            self.txt_last_message.delete("1.0", tk.END)
            self.listbox_suggestions.delete(0, tk.END)
            self.suggestions = []
            
            self.save_conversations()  # Gem alle samtaler
            self.lbl_status.config(text=f"Ny samtale '{name}' oprettet.")
    
    def on_conversation_selected(self, event):
        """Håndterer valg af samtale fra dropdown"""
        selected_name = self.conversation_var.get()
        if selected_name in self.conversations:
            # Gem først den aktuelle samtale
            self.save_current_conversation_state()
            
            # Skift til den valgte samtale
            self.current_conversation = self.conversations[selected_name]
            self.update_conversation_display()
            self.listbox_suggestions.delete(0, tk.END)
            self.suggestions = []
            
            self.lbl_status.config(text=f"Skiftede til samtale: '{selected_name}'")
    
    def save_current_conversation(self):
        """Gemmer den aktuelle samtale"""
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
        """Sletter den aktuelle samtale"""
        if self.current_conversation:
            name = self.current_conversation.name
            confirm = messagebox.askyesno("Bekræft sletning", f"Er du sikker på, at du vil slette samtalen '{name}'?")
            if confirm:
                try:
                    # Slet fil
                    file_path = os.path.join(self.data_dir, f"{name}.conv")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    # Fjern fra dictionary
                    del self.conversations[name]
                    
                    # Skift til en anden samtale hvis muligt
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
    
    def update_quotes_display(self):
        """Opdaterer visningen af svarforslagene - fjernet citationstegn funktionalitet"""
        if not self.suggestions:
            return  # Ingen forslag at opdatere
            
        self.listbox_suggestions.delete(0, tk.END)  # Ryd nuværende liste
        
        for index, suggestion in enumerate(self.suggestions):
            # Ingen citationstegn overhovedet
            self.listbox_suggestions.insert(tk.END, f"{index+1}. {suggestion}")
    
    def generate_suggestions(self):
        """Genererer svarforslag ved hjælp af ChatGPT API"""
        try:
            self.lbl_status.config(text="Genererer forslag...")
            self.root.update()
            
            # Ryd tidligere forslag
            self.listbox_suggestions.delete(0, tk.END)
            self.suggestions = []
            
            # Hent data fra input felter
            context = self.txt_context.get("1.0", tk.END).strip()
            last_message = self.txt_last_message.get("1.0", tk.END).strip()
            extra_instructions = self.txt_extra_instructions.get("1.0", tk.END).strip()
            selected_tone = self.tone_var.get()
            tone_instruction = self.tone_options[selected_tone]
            
            # Gem det aktuelle stadie af samtalen
            self.save_current_conversation_state()
            
            # Forbered system besked baseret på tone og ekstra instrukser
            system_message = ("Du er en assistent der skal hjælpe med at generere gode, naturlige " 
                             "og varierede svar til en samtale med en pige. ")
            
            if extra_instructions:
                system_message += f"Følg disse specifikke instrukser: {extra_instructions}. "
            
            # Forbered API anmodning
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
            
            # Send anmodning til API
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, data=json.dumps(data))
            response_json = response.json()
            
            # Behandl svar
            if "choices" in response_json and len(response_json["choices"]) > 0:
                assistant_response = response_json["choices"][0]["message"]["content"]
                
                # Udpak svarforslag og fjern alle citationstegn
                lines = assistant_response.split("\n")
                for line in lines:
                    line = line.strip().replace('"', '')
                    if line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("4.") or line.startswith("5."):
                        # Fjern nummeret og behold kun selve svaret
                        suggestion = line[line.index(".")+1:].strip()
                        
                        # Gem det rene forslag (uden nummer og uden citationstegn)
                        self.suggestions.append(suggestion)
                        
                        # Indsæt i listbox uden citationstegn
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
        """Sender det valgte svar til Messenger med Enter"""
        selected_index = self.listbox_suggestions.curselection()
        
        if selected_index:
            selected_index = int(selected_index[0])
            if 0 <= selected_index < len(self.suggestions):
                selected_suggestion = self.suggestions[selected_index]
                
                # Giv brugeren tid til at skifte til det rette vindue
                self._perform_text_action(selected_suggestion, press_enter=True)
                
                self.lbl_status.config(text="Besked sendt!")
            else:
                messagebox.showinfo("Information", "Ugyldigt valg.")
        else:
            messagebox.showinfo("Information", "Vælg et forslag først.")
    
    def type_message(self):
        """Skriver teksten uden at trykke Enter"""
        selected_index = self.listbox_suggestions.curselection()
        
        if selected_index:
            selected_index = int(selected_index[0])
            if 0 <= selected_index < len(self.suggestions):
                selected_suggestion = self.suggestions[selected_index]
                
                # Giv brugeren tid til at skifte til det rette vindue
                self._perform_text_action(selected_suggestion, press_enter=False)
                
                self.lbl_status.config(text="Tekst udskrevet!")
            else:
                messagebox.showinfo("Information", "Ugyldigt valg.")
        else:
            messagebox.showinfo("Information", "Vælg et forslag først.")
    
    def _perform_text_action(self, text, press_enter=True):
        """Fælles funktion til at skrive tekst med eller uden Enter"""
        # Giv brugeren tid til at skifte til det rette vindue
        countdown_time = 5
        
        for i in range(countdown_time, 0, -1):
            self.lbl_status.config(text=f"Skift til det rette vindue nu ({i} sekunder)...")
            self.root.update()
            time.sleep(1)
        
        # Fjern alle citationstegn fra teksten
        output_text = text.replace('"', '')
        
        # Simuler tastaturinput
        pyautogui.typewrite(output_text)
        
        if press_enter:
            pyautogui.press('enter')
        
        # Opdater samtalehistorik
        context = self.txt_context.get("1.0", tk.END).strip()
        context += f"\nDig: {output_text}"
        self.txt_context.delete("1.0", tk.END)
        self.txt_context.insert("1.0", context)
        
        # Ryd sidste besked felt
        self.txt_last_message.delete("1.0", tk.END)
        
        # Gem samtalen
        self.save_current_conversation_state()
        self.save_current_conversation()
    
    def add_received_message(self):
        """Tilføjer modtagerens svar til samtalehistorikken"""
        last_message = self.txt_last_message.get("1.0", tk.END).strip()
        
        if last_message:
            # Opdater samtalehistorik
            context = self.txt_context.get("1.0", tk.END).strip()
            context += f"\nHende: {last_message}"
            self.txt_context.delete("1.0", tk.END)
            self.txt_context.insert("1.0", context)
            
            # Ryd sidste besked felt
            self.txt_last_message.delete("1.0", tk.END)
            
            # Gem samtalen
            self.save_current_conversation_state()
            self.save_current_conversation()
            
            self.lbl_status.config(text="Hendes besked tilføjet til historikken.")
        else:
            messagebox.showinfo("Information", "Indtast hendes besked først.")
    
    def key_pressed(self, event):
        """Håndterer tastetryk i listbox"""
        if event.char.isdigit():
            digit = int(event.char)
            if 1 <= digit <= len(self.suggestions):
                self.listbox_suggestions.selection_clear(0, tk.END)
                self.listbox_suggestions.selection_set(digit-1)
                self.listbox_suggestions.see(digit-1)
                self.send_to_messenger()

# Hovedfunktion til at starte applikationen
def main():
    root = tk.Tk()
    app = ChatGPTMessengerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
#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