import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import shutil
import os
import ctypes
import sys
import threading

# Vérification des droits administrateur
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def ping_host(host):
    """Effectue un ping sur l'hôte spécifié et affiche un message personnalisé."""
    if not host:
        messagebox.showwarning("Attention", "Veuillez entrer un nom ou une adresse IP.")
        return False
        
    try:
        # Commande ping adaptée au système d'exploitation avec timeout
        if os.name == "nt":  # Windows
            command = ["ping", "-n", "1", "-w", "1000", host]  # 1000ms timeout
        else:  # Linux/Mac
            command = ["ping", "-c", "1", "-W", "1", host]  # 1 second timeout
        
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        
        # Analyse des résultats du ping
        output = result.stdout.lower()
        
        # Vérification approfondie que des paquets ont été reçus
        if result.returncode == 0:
            # Sur Windows, vérifions si des paquets ont été reçus
            if os.name == "nt" and ("reçus = 0" in output or "received = 0" in output):
                messagebox.showwarning("Ping", "Le PC distant est injoignable")
                return False
            # Sur Linux/Mac, vérifions également
            elif "0 received" in output or "0 packets received" in output:
                messagebox.showwarning("Ping", "Le PC distant est injoignable")
                return False
            
            # Si nous arrivons ici, le ping a vraiment réussi
            messagebox.showinfo("Ping", "Le PC distant est joignable")
            return True
        else:
            messagebox.showwarning("Ping", "Le PC distant est injoignable")
            return False
            
    except subprocess.TimeoutExpired:
        messagebox.showwarning("Ping", "Le PC distant est injoignable")
        return False
    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue lors du ping : {str(e)}")
        return False

def select_destination():
    """Sélectionne le dossier de destination et met à jour l'interface"""
    global destination_folder
    try:
        folder = filedialog.askdirectory(
            title="Sélectionner le dossier de destination",
            mustexist=True
        )
        if folder:  # Vérifie si un dossier a été sélectionné
            destination_folder = folder
            destination_label.config(text=folder)
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de sélectionner le dossier : {str(e)}")

def update_backup_paths():
    """Met à jour les chemins en fonction de l'utilisateur saisi"""
    global folders_to_backup
    selected_user = user_entry.get().strip()
    pc_name = remote_pc_entry.get().strip()
    
    if not pc_name:
        messagebox.showwarning("Attention", "Veuillez saisir le nom du PC distant.")
        return
        
    if not selected_user:
        messagebox.showwarning("Attention", "Veuillez saisir le nom de la session utilisateur.")
        return
    
    # Vérifier d'abord que le PC est accessible
    if not ping_host(pc_name):
        messagebox.showwarning("Attention", f"Impossible de mettre à jour les chemins.")
        return
    
    # Construction des chemins de sauvegarde
    folders_to_backup = {
        "Bureau": f"\\\\{pc_name}\\C$\\Users\\{selected_user}\\Desktop",
        "Mes documents": f"\\\\{pc_name}\\C$\\Users\\{selected_user}\\Documents",
        "Mes images": f"\\\\{pc_name}\\C$\\Users\\{selected_user}\\Pictures",
        "Ma musique": f"\\\\{pc_name}\\C$\\Users\\{selected_user}\\Music",
        "Mes vidéos": f"\\\\{pc_name}\\C$\\Users\\{selected_user}\\Videos",
        "Téléchargements": f"\\\\{pc_name}\\C$\\Users\\{selected_user}\\Downloads",
        "thunderbird": f"\\\\{pc_name}\\C$\\Users\\{selected_user}\\AppData\\Roaming\\thunderbird",
        "Mozilla": f"\\\\{pc_name}\\C$\\Users\\{selected_user}\\AppData\\Roaming\\Mozilla",
        "LRPPN3/INSER_AUTO": f"\\\\{pc_name}\\C$\\clients\\LRPPN3\\INSER_AUTO"
    }
    
    # Vérification de l'existence d'au moins un dossier
    path_exists = False
    for folder, path in folders_to_backup.items():
        if os.path.exists(path):
            path_exists = True
            break
    
    if path_exists:
        messagebox.showinfo("Succès", f"Chemins mis à jour pour l'utilisateur {selected_user} sur {pc_name}.")
    else:
        messagebox.showwarning("Attention", f"Impossible d'accéder aux dossiers de l'utilisateur {selected_user} sur {pc_name}.\nVérifiez que le PC est accessible et que l'utilisateur existe.")

def perform_backup(source, destination, callback=None):
    """Effectue la copie des fichiers en arrière-plan"""
    try:
        # Créer le dossier de destination s'il n'existe pas
        if not os.path.exists(destination):
            os.makedirs(destination)
        
        # Copier le contenu du dossier source vers la destination
        if os.path.exists(source):
            # Utiliser shutil.copytree avec dirs_exist_ok=True (Python 3.8+)
            # Pour Python < 3.8, il faudrait gérer différemment
            shutil.copytree(source, destination, dirs_exist_ok=True)
    except Exception as e:
        print(f"Erreur lors de la copie de {source} vers {destination}: {str(e)}")
    
    if callback:
        callback()

def execute_backup():
    """Exécute la sauvegarde des dossiers sélectionnés"""
    if not destination_folder:
        messagebox.showwarning("Erreur", "Veuillez sélectionner une destination de sauvegarde.")
        return
    
    # Vérifier que l'utilisateur et le PC sont saisis
    pc_name = remote_pc_entry.get().strip()
    selected_user = user_entry.get().strip()
    
    if not pc_name or not selected_user:
        messagebox.showwarning("Erreur", "Veuillez saisir le nom du PC distant et la session utilisateur.")
        return
    
    # Vérifier d'abord que le PC est accessible
    if not ping_host(pc_name):
        messagebox.showwarning("Attention", "Impossible de démarrer la sauvegarde.")
        return
    
    # Mettre à jour les chemins avant la sauvegarde
    update_backup_paths()
    
    # Vérifier quels dossiers sont sélectionnés
    selected_folders = []
    for i, var in enumerate(selected_files):
        if var.get():
            selected_folders.append(file_options[i])
    
    if not selected_folders:
        messagebox.showwarning("Erreur", "Veuillez sélectionner au moins un dossier à sauvegarder.")
        return
    
    # Démarrer la progression
    progress_bar.start()
    execute_button.config(state="disabled")
    
    # Nombre total de dossiers à sauvegarder
    total_folders = len(selected_folders)
    completed_folders = 0
    
    def on_folder_complete():
        nonlocal completed_folders
        completed_folders += 1
        if completed_folders >= total_folders:
            # Toutes les sauvegardes sont terminées
            root.after(0, lambda: progress_bar.stop())
            root.after(0, lambda: execute_button.config(state="normal"))
            root.after(0, lambda: messagebox.showinfo("Succès", "Sauvegarde terminée avec succès !"))
    
    # Lancer les threads de sauvegarde pour chaque dossier
    threads = []
    for folder_name in selected_folders:
        source_path = folders_to_backup.get(folder_name)
        if source_path:
            dest_path = os.path.join(destination_folder, folder_name)
            thread = threading.Thread(
                target=perform_backup,
                args=(source_path, dest_path, on_folder_complete)
            )
            threads.append(thread)
            thread.start()

# Interface graphique
root = tk.Tk()
root.title("Super Backup utilitaire by Jer0m3 v7.1")
root.geometry("800x400")

# Variables globales
destination_folder = ""
folders_to_backup = {}

# Frame PC distant
remote_frame = ttk.LabelFrame(root, text="🔧 Configuration du PC distant", padding=10)
remote_frame.pack(fill="x", padx=10, pady=5)

ttk.Label(remote_frame, text="Nom/IP du PC :").grid(row=0, column=0, sticky="w")
remote_pc_entry = ttk.Entry(remote_frame, width=25)
remote_pc_entry.grid(row=0, column=1, padx=5)

# Bouton pour effectuer un ping
ping_button = ttk.Button(remote_frame, text="Ping", command=lambda: ping_host(remote_pc_entry.get().strip()))
ping_button.grid(row=0, column=2, padx=5)

# Champ utilisateur manuel
ttk.Label(remote_frame, text="Session utilisateur :").grid(row=1, column=0, sticky="w")
user_entry = ttk.Entry(remote_frame, width=25)
user_entry.grid(row=1, column=1, padx=5)

# Bouton pour mettre à jour les chemins
update_button = ttk.Button(remote_frame, text="🔄 Mettre à jour les chemins", command=update_backup_paths)
update_button.grid(row=1, column=2, padx=5)

# Liste des fichiers à sauvegarder
files_frame = ttk.LabelFrame(root, text="📁 Sélection des dossiers à sauvegarder", padding=10)
files_frame.pack(padx=10, pady=5, fill="both")

file_options = ["Bureau", "Mes documents", "Mes images", "Ma musique", "Mes vidéos", 
                "Téléchargements", "Thunderbird", "Mozilla", "LRPPN3/INSER_AUTO"]
selected_files = []

for idx, file in enumerate(file_options):
    var = tk.BooleanVar()
    selected_files.append(var)
    cb = ttk.Checkbutton(files_frame, text=file, variable=var)
    cb.grid(row=idx//3, column=idx%3, sticky="w", padx=5, pady=5)

# Destination et progression
dest_frame = ttk.Frame(root)
dest_frame.pack(pady=10)
destination_button = ttk.Button(dest_frame, text="📁 Choisir la destination", command=select_destination)
destination_button.pack(side="left")
destination_label = ttk.Label(dest_frame, text="Aucune destination sélectionnée")
destination_label.pack(side="left", padx=10)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=700, mode="indeterminate")
progress_bar.pack(pady=5)

execute_button = ttk.Button(root, text="🚀 Démarrer la sauvegarde", command=execute_backup)
execute_button.pack(pady=10)

root.mainloop()
