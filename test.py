import os
from sys import exit
from time import time
try:
	from ollama import chat
except:
	print("Please install the Python ollama library and Ollama itself correctly. ")
	print("Please press the enter key to exit. ")
	input()
	exit(-1)
try:
	from psutil import Process, process_iter
except:
	print("Failed to execute ``from psutil import Process, process_iter``. ")
	print("Please try to install psutil via ``python -m pip install psutil`` or ``apt-get install python3-psutil``. ")
	print("Please press the enter key to exit. ")
	input()
	exit(-1)
try:
	from tqdm import tqdm
except:
	def tqdm(x:tuple|list|set, ncols:int = 100) -> tuple|list|set:
		return x
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


def checkOllama(canCheckAgain:bool = True, doPrint:bool = True) -> int:
	for proc in process_iter(["name"]):
		if proc.info["name"].lower() == "ollama.exe":
			if not isinstance(doPrint, bool) or doPrint:
				print("A possible Ollama process is as follows. ")
				print(proc)
			return proc.pid
	if isinstance(canCheckAgain, bool) and canCheckAgain:
		if not isinstance(doPrint, bool) or doPrint:
			print("Cannot find a process named \"ollama\". Try to start the Ollama soon. ")
			if __import__("platform").system().lower() == "windows":
				print("{0}> start /high \"\" ollama serve".format(os.getcwd()))
				os.system("start /high \"\" ollama serve")
			else:
				print("$ ollama serve &")
				os.system("ollama serve &")
		return checkOllama(False)
	else:
		if not isinstance(doPrint, bool) or doPrint:
			print("Cannot find a process named \"ollama\". ")
		return -1

def getTxt(filePath:str, index:int = 0) -> str: # get .txt content
	coding = ("utf-8", "gbk", "utf-16") # codings
	if 0 <= index < len(coding): # in the range
		try:
			with open(filePath, "r", encoding = coding[index]) as f:
				content = f.read()
			return content[1:] if content.startswith("\ufeff") else content # if utf-8 with BOM, remove BOM
		except (UnicodeError, UnicodeDecodeError):
			return getTxt(filePath, index + 1) # recursion
		except:
			return None
	else:
		return None # out of range

def pressTheEnterKeyToExit(errorLevel:int|None = None):
	try:
		print("Please press the enter key to exit ({0}). ".format(errorLevel) if isinstance(errorLevel, int) else "Please press the enter key to exit. ")
		input()
	except:
		pass

def main() -> int:
	# Parameters #
	databasePath = "database.txt"
	models = ["llama3.2"]
	comments = ("%", "//", "#")
	warmupContent = "Hi"
	
	# Process #
	ollamaPID = checkOllama()
	if ollamaPID <= 0:
		pressTheEnterKeyToExit(EOF)
		return EOF
	pythonProcess, ollamaProcess = Process(os.getpid()), Process(ollamaPID)
	
	# Reading #
	content = getTxt(databasePath)
	if content is None:
		print("Failed to fetch the lines from the database \"{0}\". ".format(databasePath))
		pressTheEnterKeyToExit(EOF)
		return EOF
	
	# Querying #
	lines = content.splitlines()
	results = [] # lineCount model time
	for i, model in enumerate(models):
		try:
			chat(model = model, messages = [{"role":"user", "content":warmupContent}])
		except BaseException as e:
			print("Skip models[{0}] = \"{1}\" since the following exceptions occurred. ".format(i, model))
			print(e)
			continue
		print("Warm up models[{0}] = \"{1}\" successfully. ".format(i, model))
		for idx, line in enumerate(tqdm(lines, ncols = 100)):
			for comment in comments:
				if line.startswith(comment):
					break
			else:
				if line.count("\t") == 1:
					query, phenomenon = line.split("\t")
					for model in models:
						try:
							startTime = time()
							res = chat(model = model, messages = [{"role":"user", "content":query}])
							endTime = time()
							results.append([idx, model, endTime - startTime, pythonProcess.memory_info().rss / 1024 ** 2, ollamaProcess.memory_info().rss / 1024 ** 3])
						except:
							results.append([idx, model, "E", pythonProcess.memory_info().rss / 1024 ** 2, "E"])
	print("ID & Model & Time (s) & Memory (MB) & GPU Memory (GB)")
	for result in results:
		print("{0} & {1} & {2} & {3} & {4}".format(result[0], result[1], result[2], result[3], result[4]))
	iRet = EXIT_SUCCESS if results else EXIT_FAILURE
	pressTheEnterKeyToExit(iRet)
	return iRet



if "__main__" == __name__:
	exit(main())