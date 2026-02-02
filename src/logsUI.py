import threading
from tkinter import *
from logAPI import LOG_PATH, log
import os 
from constants import IS_LINUX, IS_WINDOWS

class LogUI():
    TITLE = "Live Logs"
    UPDATING_LOGS_WAIT_MS = 1000
    updating_logs_id = None

    def __init__(self):
        root = Tk()
        self.root = root
        
        root.title(self.TITLE)
        root.protocol("WM_DELETE_WINDOW", self.close_window)
        
        #Creating Menubar
        menubar = Menu(root)
        menubar.add_command(label="Clear Logs", command=self.clear_log)
        menubar.add_command(label="Move to end", command=self.move_to_bottom)
        root.config(menu=menubar)

        scrollbar = Scrollbar(root)
        scrollbar.pack(side=RIGHT, fill=Y)
        
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

        root.geometry('1000x800')

    def _perform_cleanup(self):
        # print(f"_perform_cleanp running on {threading.get_ident()}")
        updating_logs_id = self.updating_logs_id
        root = self.root

        if root is not None:
            if updating_logs_id != "":
                root.after_cancel(updating_logs_id)
                updating_logs_id = ""
            try:
                root.quit()
                root.destroy()
                root = None
                print("quited root")
            except Exception as e:
                pass
                # log.error(f"UI Thread: Destroy failed: {e}")
            finally:
                root = None

    def scrolled_down(self) -> bool:
        return self.text_area.yview()[1] >= 0.98

    def start_updating_logs(self, readLines:int=0):

        was_at_bottom = self.scrolled_down()
        
        with open(LOG_PATH, 'r') as f:
            # Skip old lines
            for _ in range(readLines):
                f.readline()
            
            content = f.read() # Read all new content at once
            if content:
                # Split content into individual lines
                lines = content.splitlines(keepends=True)
                
                for line in lines:
                    # Check if this specific line is an error
                    if "ERROR" in line.upper():
                        self.text_area.insert(END, line, "error")
                    else:
                        self.text_area.insert(END, line)
                
                # Update the count of read lines
                readLines += len(lines)
        # if scrolled all the way down follow
        if was_at_bottom: self.text_area.see(END)
        
        self.updating_logs_id = self.root.after(
            self.UPDATING_LOGS_WAIT_MS, 
            self.start_updating_logs, 
            readLines
        )  # update every 1 second
    def move_to_bottom(self):
        self.text_area.see(END)

    def clear_log(self):
        # Stop update logs timer
        self.stop_updating_logs()
        #reset values
        self.text_area.delete('1.0', END) # Text uses 1.0 for start
        with open(LOG_PATH,'w') as f:
            f.write("")
        # start timer
        self.start_updating_logs(readLines=0)    
    
    def stop_updating_logs(self):
        if self.updating_logs_id is not None:
            self.root.after_cancel(self.updating_logs_id)
            self.updating_logs_id = None
        
    def start(self):
        self.start_updating_logs()
        self.root.withdraw()
        self.root.mainloop()

    def close_window(self):
        self.stop_updating_logs()
        self.root.withdraw()

    def show_window(self):
        self.start_updating_logs()
        self.root.deiconify()

        # Support for linux and windows 
        if IS_LINUX:
            # Cinnamon/GNOME focus
            os.system(f"wmctrl -a '{self.TITLE}'")
        elif IS_WINDOWS:
            # Windows focus logic
            self.root.state('normal')
            self.root.attributes('-topmost', True)
            self.root.attributes('-topmost', False)
            self.root.focus_force()

    def end(self):
        self.root.after(100, self._perform_cleanup)