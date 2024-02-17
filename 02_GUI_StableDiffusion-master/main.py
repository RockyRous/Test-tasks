from app import GUI_gradio

# Create app
app = GUI_gradio()
# Start app
app.launch_gui()


# Alternative option on the desktop interface
# Replace one with another

"""
import tkinter as tk
from app import GUI_tkinter

# Create app
root = tk.Tk()
app = GUI_tkinter(root)
# Start app
root.mainloop()
"""