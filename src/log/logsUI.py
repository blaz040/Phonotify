from tkinter import *
from log.logAPI import LOG_PATH, init_log
from PIL import Image, ImageTk
from pathlib import Path
import os
import shutil
from config import *

TAG = "LOG UI"
log = init_log(tag=TAG)

class LogUI():
    
    TITLE = "Live Logs"
    UPDATING_LOGS_WAIT_MS = 1000
    updating_logs = False

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

        I = Image.open(app_icon)
        photo = ImageTk.PhotoImage(I)
        root.iconphoto(True, photo)
        
        root.geometry('1300x800')

    def _perform_cleanup(self):
        root = self.root

        if root is not None:
            try:
                root.quit()
                root.destroy()
                root = None
                print("quited root")
            except Exception as e:
                pass
                log.error(f"Destroy failed: {e}")
                print("failed to quit root ")
            finally:
                root = None

    def scrolled_down(self) -> bool:
        return self.text_area.yview()[1] >= 0.98

    def update_logs(self, readLines=0):

        # End if stopped
        if self.updating_logs is False: return
        
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
        if was_at_bottom: self.move_to_bottom()

        self.root.after(
            self.UPDATING_LOGS_WAIT_MS,
            self.update_logs,
            readLines   
        )

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
        self.start_updating_logs()    
    
    def stop_updating_logs(self):
        if self.updating_logs is True:
            log.info(f"Stopped updating logs")
            self.updating_logs = False

    def start_updating_logs(self):
        if self.updating_logs is False:
            log.info(f"Starting updating logs")
            self.updating_logs = True
            self.update_logs()
       
    def start(self):
        self.start_updating_logs()
        self.root.withdraw()
        self.root.mainloop()

    def close_window(self):
        self.stop_updating_logs()
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()
        self.move_to_bottom()
        self.start_updating_logs()

        # Support for linux and windows 
        if IS_LINUX:
            # Cinnamon/GNOME focus
            if shutil.which("wmctrl"):
                os.system(f"wmctrl -a '{self.TITLE}'")
            else:
                self.root.lift()
                self.root.focus_force()
        elif IS_WINDOWS:
            # Windows focus logic
            self.root.state('normal')
            self.root.attributes('-topmost', True)
            self.root.attributes('-topmost', False)
            self.root.focus_force()

    def end(self):
        self.root.after(10, self._perform_cleanup)