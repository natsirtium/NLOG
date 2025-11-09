"""
NLOG - A simple logging library for Python with multi-threading support and project progress tracking.
"""
import sys
import os
import time
import math
import datetime
import threading
pynput = None # will be imported only if not in headless mode


class NlogObject:
  def __init__(self, doLatestLog:bool=True, logLocation:str="logs/", showDateInLogs:bool=False, headless:bool=False, priorityNames:list|None=None) -> None:
    global pynput
    self.showDateInLogs = showDateInLogs
    self.logPrinted = 0
    self.logText = [] #strings
    self.projects = [] #lists [lastTimeUpdated:int|float, threadName:str, projectName:str, percentDone:int|float, spinner:str]
    self.doLatestLog = doLatestLog
    self.logLocation = logLocation
    self.inputText = ""
    self.prompt = None
    if not priorityNames:
      self.priorityNames = ["VERBOSE", "LOG", "WARN", "ERROR", "CRITICAL"]
    else:
      self.priorityNames = priorityNames
    self.headless = headless


    self.log_lock = threading.Lock()
    self.project_lock = threading.Lock()
    self.io_lock = threading.Lock()
    
    if doLatestLog:
      day = datetime.datetime.now().strftime("%Y-%m-%d")
      for i in range(1, 1000):
        if not os.path.exists(f"{logLocation}{day}-{i}_latest.log"):
          self.sessionName = f"{day}-{i}"
          break
    else:
      self.sessionName = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    if not headless:
      pynput = __import__("pynput")
      threading.Thread(target=self.keyListener, daemon=True).start()

    self.log(f"-----START LOG FOR {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}-----", 1)

  def log(self, content:str, priority:int, thread:str|None=None) -> None:
    """
    General purpose logger. Outputs to the console when not in headless mode.
    `content` : The text you wish to log
    `priority` : The importance of the log, with the default priorities being:
    0 - Verbose, 1 - Log, 2 - Warn, 3 - Error, 4 - Critical. Note that verbose under normal operation does not output without the `verbose` flag being set.
    `thread` : if this is a thread, then this should be the thread's name. If not, leave as None.
    """

    with self.log_lock:
      if not self.showDateInLogs:
        currentTime = datetime.datetime.now().strftime("%H:%M:%S")
      else:
        currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


      threadText = f" [{thread}]" if thread else ""

      self.logText.append("[" + self.priorityNames[priority] + "-" + currentTime + f"]{threadText}: " + content)
      match priority: #Might want to add more specific functionality later
        case 0|1|2:
          pass
        case 3|4:
          self.flushLogs()
    
  def generateSpinner(self) -> str:
    """
    A helper function to generate a spinner based on the current time.
    """
    Time = time.time()
    state = math.floor(Time%4)
    match state:
      case 0:
        return "[▓░░]"
      case 1|3:
        return "[░▓░]"
      case 2:
        return "[░░▓]"
    return "[░░░]"

  def startProject(self, threadName:str|None, projectName:str) -> None:
    """
    Starts a project, i.e. a loading bar or thread progress.
    `threadName` : The name of the thread to be attached to the project, if this isn't a thread pass None
    `projectName` : A unique identifying string for the project.    
    """
    with self.project_lock:
      self.projects.append([time.time(), projectName, threadName, 0.0, self.generateSpinner()])

  def updateProject(self, projectName:str, percentage:int|float|None=None) -> int:
    """
    Updates a given project (uniquely identified by `projectName`). Should be called even without a percentage value in the action loop of the process, as that updates the spinner, and shows the user the process is still active. If you don't for 5 seconds (default), the project will be marked as "STALE".
    `projectName` : The unique identifying string for the project to be updated.
    `percentage` : The percentage of completion for the project, from 0 to 100. If `None`, the percentage will not be updated.

    Returns 1 on success, -1 if the project was not found.
    """
    with self.project_lock:
      if not self.projects:
        return -1  # no projects to update

      names = [project[1] for project in self.projects]
      if projectName not in names:
        return -1
      
      index = names.index(projectName)
      self.projects[index][0] = time.time()
      self.projects[index][4] = self.generateSpinner()
      if percentage:
        self.projects[index][3] = percentage    

      return 1
  
  def closeProject(self, projectName:str) -> int:
    """
    Closes a given project (uniquely identified by `projectName`).
    `projectName` : The unique identifying string for the project to be closed.

    Returns 1 on success, -1 if the project was not found.
    """

    with self.project_lock:
      if not self.projects:
        return -1  # no projects to close

      names = [project[1] for project in self.projects]
      if projectName not in names:
        return -1
      
      self.projects.pop(names.index(projectName))
      return 1

  def flushLogs(self, forceUpdate=False) -> None:
    with self.io_lock:
      """
      Flushes the logs to the console and file. If `forceUpdate` is True, it will update even if there are no new log lines.
      `forceUpdate` : If True, forces an update even if there are no new log lines.
      """

      if not len(self.logText) > self.logPrinted and not forceUpdate:
        return
      
      ANSI = self.ANSICodes
      if self.prompt:
        numbPrompts = 1
      else:
        numbPrompts = 0

      if len(self.projects) >= 1:
        sys.stdout.write(ANSI["ESCAPE"] + str(len(self.projects) + numbPrompts) + ANSI["CURSORUP"])
        sys.stdout.write(ANSI["ESCAPE"] + ANSI["FLUSH"])
      
      startTime = time.time()

      # capture starting index so we only append newly-printed lines to the file
      start_printed = self.logPrinted
      while len(self.logText) > self.logPrinted and time.time() < startTime + 5:
        if isinstance(self.logText[self.logPrinted], str):
          sys.stdout.write(self.logText[self.logPrinted] + "\n")
          self.logPrinted += 1
        else:
          sys.stdout.write("INVALID LINE\n")
          self.logPrinted += 1
      if self.doLatestLog:
        # Create the log directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(f"{self.logLocation}_latest.log")), exist_ok=True)
        with open(f"{self.logLocation}{self.sessionName}_latest.log", "a") as f:
          # write only the entries printed in this flush (do not re-write the last printed line)
          for log_entry in self.logText[start_printed:self.logPrinted]:
            f.write(f"{log_entry}\n")

      for project in self.projects:
        lastTimeUpdated = project[0]
        projectName = project[1]
        threadName = project[2]
        percentDone = project[3]
        spinner = project[4]

        line = ""
        if time.time()-lastTimeUpdated > 5:
          line = "STALE - "
        else:
          line = spinner + " "

        if threadName:
          line += threadName + ": "
        
        line += projectName

        if isinstance(percentDone, (float, int)):
          percentDone = round(float(percentDone), 2)
        else:
          percentDone = 0.0  # fallback if someone breaks the rules

        line += f" {percentDone:.2f}% "

        if -1 < percentDone <= 100:
          numbFilled = math.floor(percentDone/10)
          numbEmpty = 10-numbFilled
          line += "▓"*numbFilled + "░"*numbEmpty

        ANSIFlush = self.ANSICodes["ESCAPE"] + self.ANSICodes["FLUSH"]

        sys.stdout.write(ANSIFlush + line + "\n")
      
      if self.prompt:
        spinnerNumber = math.floor(time.time() % 3) + 1
        promptSpinner = "."*spinnerNumber + " "*(3- spinnerNumber)

        sys.stdout.write(self.prompt + promptSpinner + self.inputText + "\n")
      
      if not self.headless:
        sys.stdout.flush()

  def saveLogsToFile(self, fileLocation:str, fileNameOverride:str|None=None) -> None:
    with self.log_lock:
      """
      Saves the logs to a file.
      `fileLocation` : The directory where the log file will be saved.
      `fileNameOverride` : If provided, this will be the name of the log file. If None, a default name based on the current date and time will be used.
      """
      if fileNameOverride:
        fileName = fileNameOverride
      else:
        fileName = f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
      # ensure directory exists and write all collected log lines to the target file
      full_path = os.path.join(fileLocation, fileName)
      os.makedirs(os.path.dirname(os.path.abspath(full_path)), exist_ok=True)
      
      with open(full_path, "a") as f:
        for logLine in self.logText:
          f.write(f"{logLine}\n")

  def onKey(self, key) -> None:
    with self.io_lock:
      """
      Handles key press events.
      """
      if not pynput:
        self.log("Key input attempted in headless mode. Ignoring.", 3)
        return
      k = pynput.keyboard

      if key == k.Key.enter:
        self.inputText += "\n"

      # use getattr to avoid attribute errors.
      ch = getattr(key, "char", None)
      if ch:
        self.inputText += ch
        
      self.flushLogs(True)

  def keyListener(self) -> None:
    """
    To be called as a thread. Listens for keyboard input.
    """
    if not pynput:
      self.log("Key listener attempted to start in headless mode. Ignoring.", 3)
      return
    with pynput.keyboard.Listener(on_press=self.onKey) as listener:
      listener.join()
    
  def input(self, prompt:str) -> str:
    if self.headless:
      self.log("Attempted to use input() in headless mode. Defaulting to empty string.", 3)
    with self.io_lock:
      """
      Prompts the user for input, while still allowing logs to be flushed in other threads.
      `prompt` : The prompt text to display to the user.
      """
      self.inputText = ""
      self.prompt = prompt

      try:
        while True:
          if not "\n" in self.inputText:
            time.sleep(0.1)
            continue
          
          result = self.inputText.replace("\n", "")
          self.inputText = ""
          self.prompt = None
          return result
      except:
        self.prompt = None #!This can't be auto erased, so it **must** be reset after we are done with it.
        return ""

  def startLoggingThread(self, flushInterval:float=0.5) -> threading.Thread:
    """
    Starts a background thread that continuously flushes logs every `flushInterval` seconds. Returns the thread object.
    """
    def _loggingThread(flushInterval:float):
      while True:
        self.flushLogs(True)
        time.sleep(flushInterval)

    thread = threading.Thread(target=_loggingThread, args=(flushInterval,), daemon=True)
    thread.start()
    return thread

  ANSICodes = {
    #ANSI escape codes
    "ESCAPE" : "\033[",
    "FLUSH" : "K",

    "CURSORUP" : "F",
    "CURSORDOWN" : "E"
  }

