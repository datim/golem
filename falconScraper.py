#!/usr/bin/python
# simple program to scrape soccer schedules for new falcons games. HIGHLY data dependent.
# FIXME: 
#    better exception handling

import os
import cPickle as pickle
import logging
import time
from bs4 import BeautifulSoup
from urllib2 import urlopen

from emailerRoutine import EmailerRoutine

class FalconsScheduleScraper(object):
	""" Scrape websites for Falcons schedules """

	def __init__(self):
		""" initialize parameters """

		# FIXME move to config file
		self._schedule_site = "http://siliconvalleysoccer.com/league/Coed_Spring_PA_2014/schedule.php"
		self.archive_file = "reported_games_falcons.pickle"
		self.recipients_file = "./recipients.txt"
		self._email_account_file = "./account.txt"

		self._email = EmailerRoutine()
		self._sleep_seconds = 60 * 60 # one hour

	def start(self):
		"""
		Sleep for an hour, the initiate scraping of schedule website
		"""

		# report schedule, them sleep for an expected number of hours
		while True:
			self.reportSchedule()
			logging.info("Sleeping %d seconds before next check" % self._sleep_seconds)
			time.sleep(self._sleep_seconds)

	def reportSchedule(self):
		"""
		1. Scrape the schedule website
		2. Look for new changes
		3. If changes
			3a. archive changes
			3b. email changes to falconsmanager
		"""

		reported_games = {}
		unreported_games = {}

		logging.info("Scraping...")
		# scrape the schedule for games. This part is VERY website dependent
		discovered_games = self._scrapeSSVSchedule()

		# retrieve list of games we've already reported
		if os.path.exists(self.archive_file):
			fh = open(self.archive_file, 'rb')
			reported_games = pickle.load(fh)
			fh.close()

		if reported_games:
			# we've already reported some games, check for new games
			for game in discovered_games:
				if game not in reported_games:
					unreported_games[game] = discovered_games[game]
					logging.info("Discovered new game %s : %s" % (game, discovered_games[game]))

		else:
			# we've never reported any games. Report all games
			unreported_games = discovered_games

		# now that we've picked out all of the games that we want to report
		# save all the games we discovered for the next time we check
		fh = open(self.archive_file, 'wb')
		pickle.dump(discovered_games, fh)
		fh.close()

		# email list of new games that have been found
		if unreported_games:
			# log new games
			logging.info("Reporting new games:")
			for game in unreported_games:
				logging.info(" %s : %s" % (game, unreported_games[game]))

			# email new games
			self._report_new_games(unreported_games)

	def _scrapeSSVSchedule(self):
		"""
		perform scraping of silliconvalleysoccer schedule
		"""

		all_games = {}

		# read the URL and convert it to a parsable structure
		html = urlopen(self._schedule_site).read()
		soup = BeautifulSoup(html, "lxml")

		# find all the schedule tables. There is one table per 
		# day of play
		sched_tables = soup.find_all("table", "scheduleTable")
		our_team = "The Falcons"

		# for each table, parse out the rows
		for table in sched_tables:
	
			# get the table header. Game date is first entry
			table_header = table.find("th")
			game_date = table_header.contents[0]

			# now get the teams playing, along with the times
			table_rows = table.find_all("tr")

			# first two rows are header and column titles. Start at second row
			for i in range(2, len(table_rows)):
				field = table_rows[i].contents[1].contents[0]
				time = table_rows[i].contents[3].contents[0]
				homeTeam = table_rows[i].contents[5].contents[0].contents[0].contents[0]
				awayTeam = table_rows[i].contents[7].contents[0].contents[0].contents[0]

				# strip out all the extra white-spacing from the team names
				homeTeam = homeTeam.strip()
				awayTeam = awayTeam.strip()
			
				
				if homeTeam == our_team or awayTeam == our_team:
					# we have a match save the game, keyed by game time. Convert all
					# clases to strings
					game = {}
					game['date'] = str(game_date)
					game['field'] = str(field)
					game['time'] = str(time)
					game['home'] = str(homeTeam)
					game['away'] = str(awayTeam)
			
					all_games[str(game_date)] = game
	
		# return all games that were discovered
		return all_games

	def _report_new_games(self, new_games):
		"""
		Report new falcons games to recipients

		Args:
			new_games: Dictionary of games to report

		Returns:
			N.A.
		"""

		# get recipients
		to_list, cc_list, bcc_list = self._get_recipients()

		# read config file
		account, user, password = self._readEmailAccount()

		message = self._construct_message(new_games)

		subject = "New Falcons Game Posted!"

		# email the recipients
		self._email.email(account, user, password, to_list, cc_list, bcc_list, subject, message)

	def _readEmailAccount(self):
		"""
		Read the email account information from a file. Config file format is (one per line):
		   account type
           user 
           password

		Returns:
			account, user, and password for email address
		"""

		account = None
		user = None
		password = None

		if os.path.exists(self._email_account_file):

			try:
				account_file = open(self._email_account_file, 'r')
				account_info = account_file.readlines()

				# make sure we have the proper number of lines
				if len(account_info) != 3:
					logging.error("We don't have the right number of lines in email account info.\
						   Found %d, expected 3" % len(account_info))
					raise

				# save the account info
				account = account_info[0].strip()
				user = account_info[1].strip()
				password = account_info[2].strip()

				account_file.close()

			except:
				logging.error("Unable to open account file %s" % self._email_account_file)
				raise
	
		# return account information
		return account, user, password

	def _get_recipients(self):
		"""
		read recipients from file. File format is (one entry per line):
			[to]
			[cc]
			[bcc]

		Returns:
			Recipient to, cc, and bcc lists
		"""

		to_list = []
		cc_list = []
		bcc_list = []

		if os.path.exists(self.recipients_file):
			
			try:
				recp_file = open(self.recipients_file, 'r')
				recp_info = recp_file.readlines()

				# make sure we have the appropriate number of elements
				if len(recp_info) != 3:
					logging.error("Malformed recipient list!")
					raise

				# save recipients, which are recorded as a list
				to_list = eval(recp_info[0])
				cc_list = eval(recp_info[1])
				bcc_list = eval(recp_info[2])

				recp_file.close()

			except Exception, e:
				logging.error("Unable to process recipient file %s. Exception %s" % (self.recipients_file, e))
				raise

		return to_list, cc_list, bcc_list

	def _construct_message(self, new_games):
		"""
		Construct the body of the email.
		
		Args:
			new_games: list of new games available

		Returns;
			Constructed email
		"""

		message = " *** This is an automated message *** \n\n The following Falcons Games have been posted in the past hour on %s\n" % self._schedule_site

		for key in new_games:
			message += "\n Day:   %s" % new_games[key]['date']
			message += "\n Time:  %s" % new_games[key]['time']
			message += "\n Field:  %s" % new_games[key]['field']
			message += "\n Home Team: %s" % new_games[key]['home'] 
			message += "\n Away Team: %s" % new_games[key]['away']
			message += "\n\n\n"

		# message footer 
		message += "This message was generated on %s at %s.\n" % (time.strftime("%m/%d/%Y"), time.strftime("%H:%M:%S"))
		message += "If you would like to be removed from these messages, please send a message to Jeff Roecks at jroecks@gmail.com"

		return message
	
def main():
	"""
	main method. Call Falcons scraper
	"""

	# setup logging
	logging.basicConfig(filename='./scraper.log', level=logging.INFO, \
                        format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')

	# create the scraper
	scraper = FalconsScheduleScraper()
	scraper.start()

# execute main
if __name__ == "__main__":
	main()
