import os
import sys
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import subprocess

# Vérification des privilèges administrateurs
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()

class RemoteFileDeleterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Suppression de fichiers distants")
        self.root.geometry("600x400")
        
        # Variables
        self.nom_fichier = tk.StringVar()  # Stocke le chemin du fichier sélectionné
        self.pc_list_file = tk.StringVar()
        self.pc_list = []
        
        # Initialisation interface
        self.create_widgets()
        self.update_validation_button()
        
        # Surveillance des champs
        self.nom_fichier.trace_add("write", lambda *_: self.update_validation_button())
        self.pc_list_file.trace_add("write", lambda *_: self.update_validation_button())
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Section fichier à supprimer
        file_frame = ttk.LabelFrame(main_frame, text="Fichier à supprimer")
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(file_frame, text="Sélectionner un fichier", command=self.select_file).pack(side=tk.LEFT, padx=5)
        
        # Section liste des PC
        pc_frame = ttk.LabelFrame(main_frame, text="Liste des ordinateurs")
        pc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(pc_frame, textvariable=self.pc_list_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(pc_frame, text="Parcourir", command=self.select_pc_list).pack(side=tk.LEFT, padx=5)
        
        # Progression
        progress_frame = ttk.LabelFrame(main_frame, text="Progression")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=2)
        
        self.progress_text = tk.Text(progress_frame, wrap=tk.WORD, height=8)
        scrollbar = ttk.Scrollbar(progress_frame, command=self.progress_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.progress_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.progress_text.config(yscrollcommand=scrollbar.set)
        
        # Bouton validation
        self.btn_valider = ttk.Button(main_frame,
                                      text="Valider suppression",
                                      state="disabled",
                                      command=self.start_deletion)
        self.btn_valider.pack(pady=10)

    def update_validation_button(self):
        """Active ou désactive le bouton de validation en fonction des champs remplis."""
        if self.nom_fichier.get() and self.pc_list_file.get():
            self.btn_valider.config(state="normal")
        else:
            self.btn_valider.config(state="disabled")

    def select_file(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier."""
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier à supprimer",
            filetypes=[("Tous les fichiers", "*.*")]
        )
        if file_path:
            self.nom_fichier.set(file_path)  # Stocke le chemin du fichier sélectionné
            self.log(f"Fichier sélectionné : {file_path}")

    def select_pc_list(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier contenant la liste des PC."""
        file_path = filedialog.askopenfilename(
            title="Sélectionner la liste des PC",
            filetypes=[("Fichiers texte", "*.txt *.csv")]
        )
        if file_path:
            self.pc_list_file.set(file_path)
            self.load_pc_list()

    def load_pc_list(self):
        """Charge la liste des PC à partir du fichier sélectionné."""
        try:
            with open(self.pc_list_file.get(), 'r') as f:
                self.pc_list = [line.strip() for line in f if line.strip()]
            self.log(f"{len(self.pc_list)} machines chargées")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de chargement : {str(e)}")

    def log(self, message):
        """Ajoute un message dans la zone de progression."""
        timestamp = time.strftime('%H:%M:%S')
        self.progress_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.progress_text.see(tk.END)

    def start_deletion(self):
        """Démarre la suppression des fichiers sur les PC distants."""
        if messagebox.askyesno("Confirmation", "Démarrer la suppression ?"):
            self.progress_bar['value'] = 0
            self.progress_bar['maximum'] = len(self.pc_list)
            threading.Thread(target=self.run_deletion, daemon=True).start()

    def run_deletion(self):
        """Exécute la suppression sur chaque PC distant."""
        fichier = os.path.basename(self.nom_fichier.get())
        
        for index, pc in enumerate(self.pc_list):
            try:
                chemin_complet = f"\\\\{pc}\\c$\\Users\\Public\\Desktop\\{fichier}"
                
                # Commande de suppression (Windows uniquement)
                result = subprocess.run(
                    ["del", "/F", "/Q", chemin_complet],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                if result.returncode == 0:
                    self.log(f"{pc} : Suppression réussie")
                else:
                    error_msg = result.stderr.decode().strip()
                    self.log(f"{pc} : Échec - {error_msg}")
                
            except Exception as e:
                self.log(f"{pc} : Erreur - {str(e)}")
            
            # Mise à jour de la barre de progression
            self.progress_bar['value'] = index + 1

if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteFileDeleterApp(root)
    root.mainloop()
