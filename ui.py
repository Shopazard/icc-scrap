import tkinter as tk
from tkinter import filedialog
import os

root = tk.Tk()
root.title("Select Folder and Display Files")

def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        display_files(folder_path)

def display_files(folder_path):
    file_list = tk.Listbox(root)
    file_list.pack()

    for file in os.listdir(folder_path):
        file_list.insert(tk.END, file)

select_button = tk.Button(root, text="Select Folder", command=select_folder)
select_button.pack()

root.mainloop()