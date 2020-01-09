import os, time, glob, subprocess
import logging

#Global Varaibles
camPath = "/home/pi/cam/"
networkPath = "/home/pi/NAS/picamera/"
maxFileAgeLocal = 1440 # 1 day = 1440 | 1 week = 10080 | 2 weeks = 20160
maxFileAgeNetwork = 10080
syncInterval = 2 #time in seconds how ofte the script checks for new pictures
DELETE_OLD_FILES_ON_NAS = 1 # 1 == Löschen |  0 == Behalten
logger = logging.getLogger('camMonitor_Logger')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('/home/pi/camera-project/camMonitor_log.log')
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# pattern = camPath + "*.jpg"

def checkIfNasIsMounted():
	binResult = subprocess.run(['sudo', 'mount', '-l'], stdout=subprocess.PIPE)
	result = binResult.stdout.decode('utf-8')
	if( result.find("type cifs") > 0): 
		logger.info("NAS mounted")
		return True
	else:  #in mount -l Ergebnis taucht kein Eintrag "type cifs" auf
		logger.error("NAS not mounted yet")
		return False
	
def mountNAS():
	subprocess.run(['sudo', 'mount', '-a'])

def updateLocalDirectory():
	pattern = camPath + "*.jpg"
	now = time.time()
	list_of_files = glob.glob(pattern)
	deleteCount = 0
	if(len(list_of_files) == 0):
		logger.error("No Files Detected at all!");
	for file in list_of_files:
		ctime = os.path.getctime(file)
		ageInMinutes = (now - ctime) / 60 
		if( ageInMinutes > maxFileAgeLocal ):
			os.remove(file)
			deleteCount = deleteCount + 1
			logger.debug("DELETED --- " + str(file) + " -- " + str(ageInMinutes) + " Minutes old")
		logger.debug(str(file) + " -- " + str(ageInMinutes) + " Minutes old")
	logger.info(str(len(list_of_files) - deleteCount) + " Files in Directory")
	logger.info(str(deleteCount) + " Files deleted")
	
def updateNetworkDirectory():
	pattern = networkPath + "*.jpg"
	now = time.time()
	list_of_files = glob.glob(pattern)
	deleteCount = 0
	if(len(list_of_files) == 0):
		logger.error("No Files Detected at all!");
	for file in list_of_files:
		ctime = os.path.getctime(file)
		ageInMinutes = (now - ctime) / 60 
		if( ageInMinutes > maxFileAgeNetwork ):
			os.remove(file)
			deleteCount = deleteCount + 1
			logger.debug("DELETED --- " + str(file) + " -- " + str(ageInMinutes) + " Minutes old")
		logger.debug(str(file) + " -- " + str(ageInMinutes) + " Minutes old")
	logger.info(str(len(list_of_files) - deleteCount) + " Files in Network Directory")
	logger.info(str(deleteCount) + " Files deleted")


def syncFilesToNAS():
	command = "rsync -a"
	if(logger.level == logging.DEBUG ) : 
		command = command + " -v"
	command = command + " " + camPath
	command = command + " " + networkPath
	logger.debug("Executing Command: " + command)
	os.system(command)

#----------- Main Loop ----------------
oldFileCount = 0
nasMounted = False
patternLocal = camPath + "*.jpg"
while True:
	if( nasMounted == False ):
		if ( checkIfNasIsMounted() == False):
			mountNAS()
		else:
			nasMounted = True
	currentFileCount = len(glob.glob(patternLocal))
	logger.debug("currentFiles: " + str(currentFileCount) + " | Files last Time: " + str(oldFileCount))
	if( oldFileCount != currentFileCount or nasMounted == False ):
		logger.info("New Files detected!! currentFiles: " + str(currentFileCount) + " | Files last Time: " + str(oldFileCount))
		updateLocalDirectory()
		oldFileCount = len(glob.glob(patternLocal))
		syncFilesToNAS()
		if(DELETE_OLD_FILES_ON_NAS == 1):
			updateNetworkDirectory()
	time.sleep(syncInterval)
