import nlog, random, time

logger = nlog.NlogObject(doLatestLog=True)

logger.start_project(None, "Task")
logger.log("Hi", 1)

perc = 0
while True:
    if random.random() < 0.3:
        logger.update_project("Task", perc)
    perc += round(random.random(),2)
    if perc >= 100:
        logger.log("Task done!", 1)
        logger.close_project("Task")
        perc = -100000

    logger.flushLogs(True)
    
    if random.random() <= 0.15:
        logger.log("I'm a log", random.randrange(0,4))

    
    time.sleep(0.1)