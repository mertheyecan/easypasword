import ctypes
import sys
import tkinter as tk
from tkinter import messagebox, PhotoImage, Entry, Toplevel
from tkinter.ttk import Frame, Button, Style, Scrollbar
import pyperclip
import configparser
import tempfile
import atexit
import os 

# Classes to encapsulate password management and GUI
class PasswordManager:
    PASSWORDS = {}

    def __init__(self, config_file="config.ini"):
        self.config_file = config_file
        self.PASSWORDS = self.load_passwords()
        self.mutex = ctypes.windll.kernel32.CreateMutexA(None, 1, 'EurekaPassManager')
        self.last_error = ctypes.windll.kernel32.GetLastError()

        if self.last_error == 183:  # ERROR_ALREADY_EXISTS
            messagebox.showerror('Error', 'Another instance of the app is already running.')
            self.cleanup()
            return  # Prevent the rest of the __init__ method
        
    def load_passwords(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        return dict(config["Passwords"]) if "Passwords" in config else {}

    def save_passwords(self):
        config = configparser.ConfigParser()
        config["Passwords"] = self.PASSWORDS
        with open(self.config_file, "w") as configfile:
            config.write(configfile)

    def add_password(self, account, password):
        self.PASSWORDS[account] = password
        self.save_passwords()

    def delete_password(self, account):
        if account in self.passwords:
            del self.PASSWORDS[account]
            self.save_passwords()

    def edit_password(self, account, password):
        if account in self.passwords:
            self.PASSWORDS[account] = password
            self.save_passwords()

    def get_passwords(self):
        return self.PASSWORDS

    def cleanup(self):
            if self.mutex:
                ctypes.windll.kernel32.ReleaseMutex(self.mutex)
            self.root.destroy()
            sys.exit()  # Make sure to exit the application
            
class PasswordManagerGUI:
    def __init__(self, password_manager):
        self.password_manager = password_manager
        self.deep_blue = "#002244"
        self.metallic_blue = "#1A3A5A"
        self.bright_blue = "#00A8FF"
        self.root = tk.Tk()
        self.setup_styles()
        self.setup_gui()
        self.root.attributes('-topmost', True)
        self.x = None
        self.y = None
        # To make sure it stays on top after clicking elsewhere,
        # you might want to bind the focus event to a method that 
        # keeps setting the window to the topmost position.
        self.child_window_open = False
        self.root.bind("<FocusIn>", self.on_focus)

        self.on_focus()
    
    def copy_password_to_clipboard(self, account, password):
            # Logic to copy password to clipboard
            # Assuming root is a Tk root window, which should be self.root in this context
            self.root.clipboard_clear()
            self.root.clipboard_append(password)
            messagebox.showinfo(
                "Password Manager", f"Password for {account} copied to clipboard!"
            )
                
        
    def on_focus(self, event=None):
        if not self.child_window_open:
            self.root.attributes('-topmost', True)
            self.root.after(10, self.keep_on_top)
        
    def keep_on_top(self):
        if not self.child_window_open:
            self.root.attributes('-topmost', True)  # Keep the window on top
            self.root.after(10, self.keep_on_top)   # Continue to call this method to ensure topmost    
        
    def disable_topmost(self):
        self.child_window_open = True
        self.root.attributes('-topmost', False)    
                
    def start_move_window(self, event):

        self.root.x = event.x
        self.root.y = event.y

    def stop_move_window(self, event):
        self.root.x = None
        self.root.y = None

    def on_move_window(self, event):
        deltax = event.x - self.root.x
        deltay = event.y - self.root.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")


    def on_password_selected(self, event):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            selected_key = self.listbox.get(index)
            selected_password = self.password_manager.PASSWORDS[selected_key]
            self.copy_password_to_clipboard(selected_key, selected_password)
        else:
            messagebox.showwarning("Password Manager", "No password selected!")


    def on_closing(self):
        if hasattr(self, "mutex") and self.mutex:
            ctypes.windll.kernel32.ReleaseMutex(self.mutex)
        self.root.destroy()

 
        

    def setup_styles(self):
        self.style = Style()
        self.style.theme_use("default")

        # Using colors inspired by the logo


        self.style.configure("TFrame", background=self.deep_blue)
        self.style.configure("TButton", background=self.metallic_blue, foreground=self.bright_blue)
        self.style.configure("TLabel", background=self.deep_blue, foreground=self.bright_blue)
        self.style.configure("TEntry", insertbackground=self.bright_blue)
        self.style.configure(
            "Vertical.TScrollbar",
            background=self.deep_blue,       # Background color of the entire scrollbar
            troughcolor=self.deep_blue,      # Color of the trough (the area scrollbar moves in)
            gripcount=10,               # Number of grips on the scrollbar handle
            relief="flat",              # Make the scrollbar flat
        )

        self.style.map(
            "Vertical.TScrollbar",
            background=[('active', self.metallic_blue), ('pressed', self.bright_blue)],  # Color of the scrollbar handle when hovered and pressed
            sliderrelief=[('active', 'sunken'), ('!active', 'raised')]  # Relief of the scrollbar handle when hovered and not hovered
        )
        
                # Close button on title bar
        self.style.configure(
            "Close.TButton",
            background=self.deep_blue,               # Base background color
            foreground="white",                 # Text color
            relief="flat",                      # Flat appearance
            borderwidth=0,                      # No border
            padding=5,                          # Padding around the text/label
            font=("Arial", 10, "bold")          # Font styling
        )

        # Mouse hover effect for the Close Button
        self.style.map(
            "Close.TButton",
            background=[
                ('active', self.metallic_blue),       # Background color when hovered
                ('pressed', self.bright_blue)         # Background color when pressed
            ],
            foreground=[
                ('active', "white"),             # Text color when hovered
                ('pressed', "white")             # Text color when pressed
            ],
            relief=[
                ('pressed', 'sunken'),           # Relief when pressed
                ('!active', 'raised')            # Relief when not active
            ]
        )
    

    def setup_gui(self):
        self.root.configure(bg="#002244")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(dir_path, 'favicon.png')
        self.root.iconbitmap(icon_path)
        self.favicon_image = PhotoImage(file=icon_path)  # If you use `.png`, make sure to update the file extension

        # Window closing protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Define styles
        self.root.title("")
        self.root.overrideredirect(True)  # remove the title bar

        title_bar = tk.Frame(self.root, bg=self.deep_blue)

        title_label = tk.Label(title_bar, text="Eureka - Easy Pass", bg=self.deep_blue, fg="#00FF00")
        title_label.grid(row=0, column=0, sticky="w")

        close_button = tk.Button(title_bar, text="X", bg=self.deep_blue, fg="#00FF00", command=lambda : self.root.destroy())
        close_button.grid(row=0, column=1, sticky="e")

        # These settings will ensure that the title_label takes up most of the space and
        # close_button stays at the right-most side.
        title_bar.grid_columnconfigure(0, weight=1)
        title_bar.grid_columnconfigure(1, weight=0)

        title_bar.bind('<Button-1>', self.start_move_window)
        title_bar.bind('<ButtonRelease-1>', self.stop_move_window)
        title_bar.bind('<B1-Motion>', self.on_move_window)
        title_bar.grid(row=0, column=0, columnspan=3, sticky="nsew")
        
        # Window sizing
        window_width = 300
        window_height = min(200, len(self.password_manager.PASSWORDS) * 20 + 170)
        self.root.geometry(f"{window_width}x{window_height}")
        self.root.resizable(False, True)

        # Frame and Listbox
        self.frame = Frame(self.root, style="TFrame")
        self.frame.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=20)

        self.listbox = tk.Listbox(
            self.frame,
            height=len(self.password_manager.PASSWORDS),
            selectmode="single",
            bg=self.deep_blue,              # Background color of the listbox
            fg=self.bright_blue,            # Text color in the listbox
            selectbackground=self.metallic_blue,  # Color of the selected item's background
            selectforeground="#FFFFFF",      # Color of the selected item's text
        )
        for key in self.password_manager.PASSWORDS:
            self.listbox.insert(tk.END, key)
        self.listbox.grid(row=0, column=0, sticky="nsew")

        # Scrollbar for listbox
        scrollbar = Scrollbar(
            self.frame,
            orient="vertical",
            command=self.listbox.yview,
            style="Vertical.TScrollbar",
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.bind("<Double-Button-1>", self.on_password_selected)

        # Buttons for managing passwords
        Button(
            self.root, text="Add Password", command=self.add_password, style="TButton"
        ).grid(row=2, column=0, sticky="nsew")
        Button(
            self.root, text="Edit Selected", command=self.edit_password, style="TButton"
        ).grid(row=2, column=1, sticky="nsew")
        Button(
            self.root,
            text="Delete Selected",
            command=self.delete_password,
            style="TButton",
        ).grid(row=2, column=2, sticky="nsew")

        # To make sure the grid columns and rows resize properly
        self.root.grid_rowconfigure(1, weight=1)  # makes the listbox frame expandable
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        self.frame.grid_columnconfigure(0, weight=1)  # makes the listbox expandable
        self.frame.grid_rowconfigure(0, weight=1)
        
    def add_password(self):
        add_window = tk.Toplevel(self.root)
        self.disable_topmost()
        add_window.configure(bg=self.deep_blue)
        add_window.grab_set()  # Disable interaction with the root window
        
        add_window.update_idletasks() 

        # Dimensions of the root window
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()    
        root_height = self.root.winfo_height()

        # Dimensions of the edit window
        edit_width = add_window.winfo_width()
        edit_height = add_window.winfo_height()

        # Calculate position for edit window to be at the center of the root window
        center_x = root_x + (root_width - edit_width) // 2
        center_y = root_y + (root_height - edit_height) // 2

        # Set the position of the window
        add_window.geometry(f'+{center_x}+{center_y}')

        add_window.transient(self.root)  # Make this window transient with respect to root
        add_window.protocol("WM_DELETE_WINDOW", lambda: self.on_child_close(add_window))

        

        
        tk.Label(add_window, text="Account Name", bg=self.deep_blue, fg=self.bright_blue).grid(
            row=0, column=0, sticky="e", padx=5, pady=5
        )
        account_entry = tk.Entry(add_window)
        account_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        tk.Label(add_window, text="Password", bg=self.deep_blue, fg=self.bright_blue).grid(
            row=1, column=0, sticky="e", padx=5, pady=5
        )
        password_entry = tk.Entry(add_window, show="*")
        password_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        def save_password():
            account = account_entry.get()
            password = password_entry.get()
            self.password_manager.PASSWORDS[account] = password  # Update the passwords dictionary
            self.password_manager.save_passwords()  # Save the updated dictionary
            add_window.destroy()
            self.listbox.insert(tk.END, account)  # Update listbox with new account
            

            
        tk.Button(add_window, text="Save", command=save_password).grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10
        )

        add_window.grid_columnconfigure(1, weight=1)
        add_window.update_idletasks()
        required_width = add_window.winfo_reqwidth()
        required_height = add_window.winfo_reqheight()
        add_window.minsize(required_width, required_height)
        add_window.resizable(width=False, height=True)


    def edit_password(self):
  
        self.disable_topmost()
        selection = self.listbox.curselection()
        if not selection:
            tk.messagebox.showwarning(
                "Password Manager", "No password selected to edit."
            )
            return
        index = selection[0]
        selected_key = self.listbox.get(index)
        edit_window = tk.Toplevel(self.root)
        edit_window.configure(bg=self.deep_blue)
        
        edit_window.transient(self.root)

        edit_window.update_idletasks() 

        # Dimensions of the root window
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()    
        root_height = self.root.winfo_height()

        # Dimensions of the edit window
        edit_width = edit_window.winfo_width()
        edit_height = edit_window.winfo_height()

        # Calculate position for edit window to be at the center of the root window
        center_x = root_x + (root_width - edit_width) // 2
        center_y = root_y + (root_height - edit_height) // 2

        # Set the position of the window
        edit_window.geometry(f'+{center_x}+{center_y}')

        # Set window to grab input focus
        edit_window.grab_set()
        

        edit_window.protocol("WM_DELETE_WINDOW", lambda: self.on_child_close(edit_window))
        tk.Label(edit_window, text="Account Name", bg=self.deep_blue, fg=self.bright_blue).grid(
            row=0, column=0
        )
        account_entry = tk.Entry(edit_window)
        account_entry.insert(0, selected_key)
        account_entry.grid(row=0, column=1)

        tk.Label(edit_window, text="Password", bg=self.deep_blue, fg=self.bright_blue).grid(
            row=1, column=0
        )
        password_entry = tk.Entry(edit_window, show="*")
        password_entry.insert(0, self.password_manager.PASSWORDS[selected_key])
        password_entry.grid(row=1, column=1)

        def update_password():
            # Get the current selection index
            selection = self.listbox.curselection()
            old_key = selection
            print(old_key)

            # Get the new account name and password from the entries
            new_account = account_entry.get()
            new_password = password_entry.get()

            # Check if the new account name is valid
            if not new_account:
                tk.messagebox.showwarning("Update Error", "The account name cannot be empty.")
                return
            if new_account != old_key and new_account in self.password_manager.PASSWORDS:
                tk.messagebox.showwarning("Update Error", "The account name already exists.")
                return

            # Update the password dictionary and listbox
            if new_account == old_key:
                self.password_manager.PASSWORDS[old_key] = new_password
            else:
            # Remove the old entry and add the new one



                # Use next() to get the first index from the iterable, or return the size of the listbox if the iterable is empty
         
                self.password_manager.PASSWORDS.pop(old_key, None)  # Safely remove the old key
                self.password_manager.PASSWORDS[new_account] = new_password
                # Update the listbox entry
                self.listbox.delete(index)
               
                self.listbox.insert(index, new_account)

                # Select the newly inserted item
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(index)

            # Save the updated dictionary
            self.password_manager.save_passwords()

            # Keep the updated entry selected
            self.listbox.selection_set(index)

            # Close the edit window
            edit_window.destroy()


        tk.Button(edit_window, text="Update", command=update_password).grid(
                row=2, column=0, columnspan=2
            )
        
    def delete_password(self):
        selection = self.listbox.curselection()
        self.disable_topmost()
        if selection:
            index = selection[0]
            selected_key = self.listbox.get(index)
            # Confirmation dialog
            response = tk.messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete the password for {selected_key}?",
                default="no",
            )
            if response:
                del self.password_manager.PASSWORDS[selected_key]  # Remove from the passwords dictionary
                self.password_manager.save_passwords()  # Save the updated dictionary
                self.listbox.delete(index)  # Remove from the listbox
                tk.messagebox.showinfo(
                    "Password Manager", f"Password for {selected_key} has been deleted."
                )
            else:
                tk.messagebox.showinfo(
                    "Password Manager", "Delete operation cancelled."
                )
        else:
            tk.messagebox.showwarning(
                "Password Manager", "No password selected to delete."
            )
  
    def on_child_close(self,window):
            self.child_window_open = False
            self.root.attributes('-topmost', True)
            window.destroy()
            
       
    def run(self):
        self.root.mainloop()


def cleanup_mutex():
    if mutex:
        ctypes.windll.kernel32.CloseHandle(mutex)


@atexit.register
def on_exit():
    cleanup_mutex()


# Mutex and single instance check can stay outside the classes as they relate to the application instance
mutex = ctypes.windll.kernel32.CreateMutexA(None, False, "Global\\PasswordManagerMutex")
last_error = ctypes.windll.kernel32.GetLastError()

if last_error == 183:
    messagebox.showerror("Error", "Application is already running.")
    sys.exit(0)

# Starting point of the application
if __name__ == "__main__":
    try:
        manager = PasswordManager()
        gui = PasswordManagerGUI(manager)
        gui.run()
    except Exception as e:
        # Print the exception message
        print(f"An error occurred: {e}")
        
        # Optionally, print the entire traceback for more detailed debugging
        import traceback
        print(traceback.format_exc())
