import tkinter as tk
from tkinter import Tk, Listbox

root:Tk = None
    
def run():
    global root
    readLines = 0
        
    def scrolled_down(myList:Listbox) -> bool:
        return myList.yview()[1] == 1.0

    def update_logs():
        nonlocal readLines
        scrolled_d = scrolled_down(myList)
            
        with open('myLogs.log', 'r') as f:
            for i in range(readLines):
                f.readline()
            line = f.readline()
            
            while line != "":
                myList.insert(tk.END,line)
                line = f.readline()
                readLines+=1
        
        if scrolled_d: myList.see(readLines)
        
        root.after(5000, update_logs)  # update every 1 second


    root = tk.Tk() 
    root.title("Live Logs")
    scrollbar = tk.Scrollbar(root)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    myList = tk.Listbox(root, yscrollcommand=scrollbar.set)
    #text = tk.Text(root, width=80, height=20)
    #text.pack()
    update_logs()
    
    myList.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=myList.yview)
    root.geometry('700x500')
    root.mainloop()
    
def end():
    global root
    if(root == None):
        return
    #root.quit()
    root.destroy()
    root = None