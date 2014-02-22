#
# Use Flask to export the log file to a browser at the URL http://<Server IP>/scraper
#

from time import gmtime, strftime, localtime
from flask import Flask
app = Flask(__name__)

scraperLogFile = '/home/pi/falconscraper/scraper.log'
html_new_line = "<br/>"

@app.route("/")
def hello():
	return "Nothing to see here"

@app.route("/scraper")
def anotherPage():

	logString = "Falcon Scraper Log File" + html_new_line

	# open the scraper log file and read the contents

	f = open(scraperLogFile, 'r')

	# write line by line to the log
	for line in f:
		logString = logString + line + html_new_line

	# now right the current timestamp
	logString = logString + html_new_line

	currentTime = strftime("%a, %d %b %Y %H:%M:%S", localtime())

	logString = logString + "Current time: " + currentTime
	return logString

if  __name__ == "__main__":
	app.run('0.0.0.0', port=80, debug=True)
