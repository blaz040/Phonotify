import tkinter as tk
from tkinter import Tk, Listbox

root:Tk = None
after_id:str = ""
def run():
    global root
    readLines = 0
        
    def scrolled_down(myList:Listbox) -> bool:
        return myList.yview()[1] == 1.0

    def update_logs(myList:Listbox):
        global after_id
        nonlocal readLines
        scrolled_d = scrolled_down(myList)
        #print("updating logs....")
        with open('myLogs.log', 'r') as f:
        
            for i in range(readLines):
                f.readline()
            line = f.readline()
            
            while line != "":
                myList.insert(tk.END,line)
                line = f.readline()
                readLines+=1
        
        if scrolled_d: myList.see(readLines)
        
        after_id = root.after(5000, update_logs, myList)  # update every 1 second
    

    root = tk.Tk() 
    root.title("Live Logs")
    
    scrollbar = tk.Scrollbar(root)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    myList = tk.Listbox(root, yscrollcommand=scrollbar.set)
    
    update_logs(myList)
    
    myList.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=myList.yview)
    
    root.geometry('700x500')
    root.mainloop()
    
def end():
    global root
    global after_id
    if(root == None):
        return
    #root.quit()
    if after_id != "":
        root.after_cancel(after_id)
        after_id = ""
    root.destroy()
    root = None