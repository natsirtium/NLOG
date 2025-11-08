import nlog, time, threading, random

logger = nlog.NlogObject()

logger.startProject("task-thread", "Task")

def exampleProcess():
  global logger
  import tkinter as tk
  root = tk.Tk()
  root.title("Example")

  def log(): 
    logger.log("I'm a log", random.randint(0, 4), "task-thread")
  b1 = tk.Button(root, text="Log", command=log)
  b1.pack()

  def update():
    logger.updateProject("Task")
  b2 = tk.Button(root, text="Update", command=update)
  b2.pack()

  root.mainloop()

def logThread():
  while True:
    logger.flushLogs(True)
    time.sleep(0.5)

threading.Thread(target=exampleProcess, daemon=True).start()
threading.Thread(target=logThread, daemon=True).start()

logger.input("Press enter to stop")

