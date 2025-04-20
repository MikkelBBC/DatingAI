import tkinter as tk
from tkinter import filedialog, scrolledtext
from PIL import Image, ImageTk, ImageGrab
import pytesseract
import os
import time

# Tesseract sti
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class MessengerScanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Messenger Scanner")
        self.root.geometry("800x600")
        
        # Hovedramme
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Kontrolpanel
        control_panel = tk.Frame(main_frame)
        control_panel.pack(fill=tk.X, pady=5)
        
        # Knapper
        upload_btn = tk.Button(control_panel, text="Upload billede", command=self.upload_image)
        upload_btn.pack(side=tk.LEFT, padx=5)
        
        screenshot_btn = tk.Button(control_panel, text="Tag skærmbillede", command=self.select_area)
        screenshot_btn.pack(side=tk.LEFT, padx=5)
        
        scan_btn = tk.Button(control_panel, text="Scan samtale", command=self.scan_conversation)
        scan_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(control_panel, text="Slet billede", command=self.clear_image)
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # Billedområde
        image_frame = tk.LabelFrame(main_frame, text="Billede")
        image_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.image_label = tk.Label(image_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Resultatområde
        result_frame = tk.LabelFrame(main_frame, text="Samtaleresultat")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=10)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Statuslinje
        self.status_var = tk.StringVar(value="Klar")
        status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Variabler
        self.current_image = None
        self.full_screenshot = None
        self.area_window = None
        
    def upload_image(self):
        """Upload et billede fra fil"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Billedfiler", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        
        if file_path:
            try:
                self.current_image = Image.open(file_path)
                self.display_image(self.current_image)
                self.status_var.set(f"Billede indlæst: {os.path.basename(file_path)}")
            except Exception as e:
                self.status_var.set(f"Fejl ved indlæsning: {str(e)}")
    
    def select_area(self):
        """Ny metode: Tag først et fuldt skærmbillede og vælg så området"""
        # Tag et komplet skærmbillede
        try:
            self.status_var.set("Tager fuldt skærmbillede...")
            self.full_screenshot = ImageGrab.grab(all_screens=True)
            
            # Skjul hovedvinduet
            self.root.withdraw()
            
            # Opret et vindue til at vise det fulde skærmbillede
            self.area_window = tk.Toplevel(self.root)
            self.area_window.attributes('-fullscreen', True)
            self.area_window.title("Vælg område")
            
            # Konverter billedet til PhotoImage
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Tilpas billedet til skærmstørrelsen hvis nødvendigt
            if self.full_screenshot.width > screen_width or self.full_screenshot.height > screen_height:
                self.full_screenshot = self.full_screenshot.resize((screen_width, screen_height), Image.LANCZOS)
            
            # Konverter til PhotoImage
            self.tk_image = ImageTk.PhotoImage(self.full_screenshot)
            
            # Opret canvas med billedet
            self.canvas = tk.Canvas(self.area_window, width=screen_width, height=screen_height)
            self.canvas.pack(fill=tk.BOTH, expand=True)
            self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)
            
            # Variable for udvalg
            self.start_x = 0
            self.start_y = 0
            self.rect = None
            
            # Instruktionstekst (vis oven på billedet)
            self.canvas.create_text(
                screen_width // 2, 30, 
                text="Træk for at vælge område - ESC/Q for at annullere", 
                fill="red", font=("Arial", 16, "bold")
            )
            
            # Bind begivenheder
            self.canvas.bind("<ButtonPress-1>", self.on_area_start)
            self.canvas.bind("<B1-Motion>", self.on_area_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_area_release)
            self.area_window.bind("<Escape>", self.cancel_area_selection)
            self.area_window.bind("q", self.cancel_area_selection)
            self.area_window.bind("Q", self.cancel_area_selection)
            
            # Fokuser på vinduet
            self.area_window.focus_force()
            
        except Exception as e:
            self.root.deiconify()
            self.status_var.set(f"Fejl ved skærmbillede: {str(e)}")
    
    def on_area_start(self, event):
        """Museknap ned - start område"""
        self.start_x = event.x
        self.start_y = event.y
        
        # Slet eksisterende rektangel
        if self.rect:
            self.canvas.delete(self.rect)
        
        # Opret nyt rektangel
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )
    
    def on_area_drag(self, event):
        """Mus trækkes - opdater område"""
        if self.rect:
            # Opdater rektangel
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    
    def on_area_release(self, event):
        """Museknap op - afslut område"""
        if not self.rect:
            return
            
        # Beregn koordinater (sikrer at x1 < x2 og y1 < y2)
        x1 = min(self.start_x, event.x)
        y1 = min(self.start_y, event.y)
        x2 = max(self.start_x, event.x)
        y2 = max(self.start_y, event.y)
        
        # Kontroller områdets størrelse
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            # For lille område
            self.status_var.set("Området er for lille. Prøv igen.")
            return
        
        try:
            # Beskær det fulde skærmbillede til det valgte område
            self.current_image = self.full_screenshot.crop((x1, y1, x2, y2))
            
            # Luk område-vinduet
            self.area_window.destroy()
            self.area_window = None
            
            # Vis hovedvinduet igen
            self.root.deiconify()
            
            # Vis det beskårne billede
            self.display_image(self.current_image)
            
            # Opdater status
            self.status_var.set(f"Område valgt: {x2-x1}x{y2-y1} pixels")
            
        except Exception as e:
            if self.area_window:
                self.area_window.destroy()
                self.area_window = None
            self.root.deiconify()
            self.status_var.set(f"Fejl ved beskæring: {str(e)}")
    
    def cancel_area_selection(self, event=None):
        """Annuller valg af område"""
        if self.area_window:
            self.area_window.destroy()
            self.area_window = None
        
        self.root.deiconify()
        self.status_var.set("Områdevalg annulleret")
    
    def display_image(self, img):
        """Vis billede i grænsefladen"""
        if img is None:
            return
            
        # Lav en kopi af billedet
        display_img = img.copy()
        
        # Få labelens dimensioner
        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()
        
        # Brug standarddimensioner hvis labelen ikke er synlig endnu
        if label_width <= 1:
            label_width = 600
        if label_height <= 1:
            label_height = 300
        
        # Tilpas billedet til labelens størrelse
        img_width, img_height = display_img.size
        ratio = min(label_width/img_width, label_height/img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        display_img = display_img.resize((new_width, new_height), Image.LANCZOS)
        
        # Vis billedet
        tk_img = ImageTk.PhotoImage(display_img)
        self.image_label.config(image=tk_img)
        self.image_label.image = tk_img  # Behold reference
    
    def clear_image(self):
        """Fjern det aktuelle billede"""
        self.current_image = None
        self.image_label.config(image='')
        self.result_text.delete(1.0, tk.END)
        self.status_var.set("Billede slettet")
    
    def scan_conversation(self):
        """Scan billedet for tekst"""
        if self.current_image is None:
            self.status_var.set("Intet billede at scanne")
            return
        
        try:
            self.status_var.set("Scanner billede...")
            
            # Prøv at scanne med dansk sprog, fald tilbage til engelsk
            try:
                text = pytesseract.image_to_string(self.current_image, lang='dan')
            except:
                text = pytesseract.image_to_string(self.current_image)
            
            # Behandl teksten
            result = self.process_conversation(text)
            
            # Vis resultatet
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result)
            
            self.status_var.set("Scanning fuldført")
        except Exception as e:
            self.status_var.set(f"Fejl ved scanning: {str(e)}")
    
    def process_conversation(self, text):
        """Bearbejd tekst til at identificere beskedtyper"""
        lines = text.split('\n')
        result_lines = []
        
        # Nøgleord til at identificere beskedtyper
        your_message_keywords = ["Jep", "Får", "Bare kom", "Sådan ik", "længt væk", "bor", "hvor du bor"]
        their_message_keywords = ["Er det i dag", "Fuck måske", "Hvor er det", "Fair okay", "Men kommer", "arbejdstøj", "Mårslev"]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Kontroller om linjen matcher nøgleord
            if any(keyword in line for keyword in your_message_keywords):
                result_lines.append(f"DIG (højre): {line}")
            elif any(keyword in line for keyword in their_message_keywords):
                result_lines.append(f"DEM (venstre): {line}")
            else:
                result_lines.append(f"UKENDT: {line}")
        
        return '\n'.join(result_lines)

def main():
    root = tk.Tk()
    app = MessengerScanner(root)
    root.mainloop()

if __name__ == "__main__":
    main()