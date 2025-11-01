from tkinter import *
from logAPI import logPath, log

root:Tk = None
after_id:str = ""

def run():
    def on_closing():
        end()
        #global root 
        #root.destroy()
        #root = None
        
        
    def scrolled_down(myList:Listbox) -> bool:
        return myList.yview()[1] == 1.0

    def update_logs(readLines:int=0):
        global root
        global after_id
        nonlocal myList
        
        updating_logs_wait = 1000
        scrolled_d = scrolled_down(myList)
        
        with open(logPath, 'r') as f:
        
            for i in range(readLines):
                f.readline()
            line = f.readline()
            
            while line != "":
                myList.insert(END,line)
                line = f.readline()
                readLines+=1
        
        # if scrolled all the way down follow
        if scrolled_d: myList.see(readLines)
        
        after_id = root.after(updating_logs_wait, update_logs, readLines)  # update every 1 second
    
    def clear_log():
        global after_id
        nonlocal myList
        
        # Stop timer 
        if after_id != "":
            root.after_cancel(after_id)
            after_id = ""

        #reset values
        myList.delete(0,END)
        
        with open(logPath,'w') as f:
            f.write("")

        # start timer
        update_logs()
        
    global root
    # checks if there is alvready a window open
    if is_showing(root):
        return 
    root = Tk() 
    root.title("Live Logs")
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    #Creating Menubar
    menubar = Menu(root)
    menubar.add_command(label="Clear Logs", command=clear_log)

    scrollbar = Scrollbar(root)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    myList = Listbox(root, yscrollcommand=scrollbar.set)
    update_logs()
    
    myList.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.config(command=myList.yview)

    root.config(menu=menubar)
    root.geometry('700x500')
    root.mainloop()

def is_showing(root:Tk)->bool:

    if root is None:
        return False
    # put at the top of the stack for a moment
    # root.focus() crashed if it is at the top of the stack
    root.attributes('-topmost', True)
    root.attributes('-topmost', False)
    return True

def end()->bool:
    global root
    global after_id

    if root is None:
        return False
    
    # Cancel the next updateLogs 
    if after_id != "":
        root.after_cancel(after_id)
        after_id = ""
    try:
        root.destroy()
    except Exception as e:
        log.error(f"Logs UI cant destroy... {e}")
    root = None
    log.info("going on")
    return True
