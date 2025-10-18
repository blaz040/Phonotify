import tkinter as tk
readLines = 0
root = tk.Tk()
def run():
    global root
    def update_logs():
        with open('myLogs.log', 'r') as f:
            global readLines
            for i in range(readLines):
                f.readline()
            line = f.readline()
            while line != "":
                mylist.insert(tk.END,line)
                line = f.readline()
                readLines+=1
        root.after(5000, update_logs)  # update every 1 second

    root.title("Live Logs")
    scrollbar = tk.Scrollbar(root)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    mylist = tk.Listbox(root, yscrollcommand=scrollbar.set)
    #text = tk.Text(root, width=80, height=20)
    #text.pack()
    
    update_logs()
    
    mylist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=mylist.yview)
    root.geometry("700x500")
    root.mainloop()
    
def end():
    global root
    root.destroy()