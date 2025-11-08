import nlog, time, threading

logger = nlog.NlogObject()

logger.start_project("task-thread", "Task")

def example_process():
  global logger
  import tkinter as tk
  root = tk.Tk()
  root.title("Example")

  def log(): 
    logger.log("Hi", 1, "task-thread")
  b1 = tk.Button(root, text="log", command=log)
  b1.pack()

  def update():
    logger.update_project("Task")
  b2 = tk.Button(root, text="update", command=update)
  b2.pack()

  root.mainloop()

def log_thread():
  while True:
    logger.flushLogs(True)
    time.sleep(0.5)

threading.Thread(target=example_process, daemon=True).start()
threading.Thread(target=log_thread, daemon=True).start()

logger.input("Press any enter to stop")

