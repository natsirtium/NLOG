import nlog, time, threading, random

logger = nlog.NlogObject()

def exampleProcess():
  global logger
  logger.startProject("thread", "project")
  p = 0.0
  while True:
    p += random.random()
    logger.updateProject("project", p)
    if p >= 100.0:
      p = 0.0
    
    time.sleep(0.1)

    if random.random() < 0.1:
      logger.log(f"I'm a log!", 1)


threading.Thread(target=exampleProcess, daemon=True).start()
logger.startLoggingThread(0.5)

logger.input("input")
logger.log("Finished input", 1)
