from tkinter import *
from logAPI import LOG_PATH, log
import os 
# ============================================================================================
# This is old version of logsUI do not use it 
# ============================================================================================
class LogUI():
    UPDATING_LOGS_WAIT_MS = 1000
    updating_logs_id = None

    def __init__(self):
        root = Tk()
        self.root = root
        root.title("Live Logs")
        root.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Creating Menubar
        menubar = Menu(root)
        menubar.add_command(label="Clear Logs", command=self.clear_log)
        root.config(menu=menubar)

        # Scrollbar
        scrollbar = Scrollbar(root)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Text Widget (Replaces Listbox)
        # tabs='0.5i' sets a tab stop every 0.5 inches
        self.text_area = Text(root, 
                              yscrollcommand=scrollbar.set, 
                              font="TkFixedFont", 
                              padx=10, 
                              pady=10,
                              tabs='1i')
        
        self.text_area.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self.text_area.yview)

        # Define styles (tags)
        self.text_area.tag_config("error", foreground="red")
        self.text_area.tag_config("info", foreground="blue")

        root.geometry('800x500')

    def scrolled_down(self) -> bool:
        # Text widget yview returns (top, bottom) as floats
        return self.text_area.yview()[1] >= 0.9

    def start_updating_logs(self, readLines: int = 0):
        was_at_bottom = self.scrolled_down()
        
        try:
            with open(LOG_PATH, 'r') as f:
                # Skip old lines
                for _ in range(readLines):
                    f.readline()
                
                content = f.read() # Read all new content at once
                if content:
                    # Determine which tag to use based on content
                    tag = None
                    if "ERROR" in content.upper():
                        tag = "error"
                    
                    # Insert content at the end
                    self.text_area.insert(END, content, tag)
                    
                    # Update the count of read lines
                    readLines += content.count('\n')
        except FileNotFoundError:
            pass

        # Auto-scroll logic
        if was_at_bottom:
            self.text_area.see(END)
        
        self.updating_logs_id = self.root.after(
            self.UPDATING_LOGS_WAIT_MS, 
            self.start_updating_logs, 
            readLines
        )

    def clear_log(self):
        # self.stop_updating_logs()
        self.text_area.delete('1.0', END) # Text uses '1.0' for start
        with open(LOG_PATH, 'w') as f:
            f.write("")
        #self.start_updating_logs(0)

    def stop_updating_logs(self):
        if self.updating_logs_id:
            self.root.after_cancel(self.updating_logs_id)
            self.updating_logs_id = None

    def start(self):
        self.start_updating_logs()
        self.root.withdraw()
        self.root.mainloop()

    def show_window(self):
        self.root.deiconify()
        os.system("wmctrl -a 'Live Logs'")
        self.text_area.see(END)

    def close_window(self):
        self.root.withdraw()
    
    def end(self):
        self.root.after(100, self._perform_cleanup)