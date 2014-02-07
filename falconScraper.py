#!/usr/bin/python
# FIXME: 
#    logging
#    better exception handling

import os
import pickle
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
		self._recipients_to_list = ['jroecks@gmail.com']
		self._recipients_cc_list = []
		self._recipients_bcc_list = []
		self.archive_file = "falcons_games.pickle"
		self.recipients_file = "./recipients.txt"
		self._email_account_file = "./account.txt"

		self._email = EmailerRoutine()

		# initialize logging
		# FIXME LOG

	def start(self):
		"""
		Sleep for an hour, the initiate scraping of schedule website
		"""

		self.reportSchedule()

	def reportSchedule(self):
		"""
		1. Scrape the schedule website
		2. Look for new changes
		3. If changes
			3a. archive changes
			3b. email changes to falconsmanager
		"""

		current_games = None
		new_games = {}

		# scrape the schedule for games. This part is VERY website dependent
		found_games = self._scrapeSSVSchedule()

		# retrieve list of games
		if os.path.exists(self.archive_file):
			fh = open(self.archive_file, 'r')
			current_games = cPickle.load(fh)
			fh.close()

		if current_games:
			# we've already reported some games, check for new games
			for game in found_games:
				if game not in current_games:
					new_games[game] = found_games[game]

		else:
			# no games have been reported so far.  Report all games
			new_games = found_games

		import pdb
		pdb.set_trace()

		# archive new games to pickle file
		fh = open(self.archive_file, 'w')
		pickle.dump(new_games, fh)
		#fh.write(pickled_schedule)
		fh.close()

		# if we've found new games, combine them, report the new games and 
		# archive the current list
		if new_games:

			self._report_new_games(new_games)

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
					# we have a match save the game, keyed by game time
					game = {}
					game['date'] = game_date
					game['field'] = field
					game['time'] = time
					game['home'] = homeTeam
					game['away'] = awayTeam
			
					all_games[game_date] = game
	
		# return all games that were discovered
		return all_games

	def _report_new_games(self, new_games):
		"""
		Report new falcons games to recipients
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
					print "We don't have the right number of lines in email account info.\
						   Found %d, expected 3" % len(account_info)
					raise

				# save the account info
				account = account_info[0].strip()
				user = account_info[1].strip()
				password = account_info[2].strip()

				account_file.close()

			except:
				print "Unable to open account file %s" % self._email_account_file
				raise
	
		# return account information
		return account, user, password

	def _get_recipients(self):
		"""
		read recipients from file. File format is one list per line:
			[to]
			[cc]
			[bcc]
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
					print "Malformed recipient list!"
					raise

				# save recipients
				to_list = eval(recp_info[0])
				cc_list = eval(recp_info[1])
				bcc_list = eval(recp_info[2])

				recp_file.close()

			except:
				print "Unable to process recipient file %s" % self.recipients_file
				raise

		return to_list, cc_list, bcc_list

	def _construct_message(self, new_games):
		"""
		Construct the body of the email.
		
		Args:
			new_games: list of new games available
		"""

		message = " *** This is an automated message *** \n\n The following Falcons Games have been posted in the past hour on %s\n" % self._schedule_site

		for key in new_games:
			message += "\n Day:   %s" % new_games[key]['date']
			message += "\n Time:  %s" % new_games[key]['time']
			message += "\n Field:  %s" % new_games[key]['field']
			message += "\n Home Team:  %s, Away Team: %s" % (new_games[key]['home'], new_games[key]['away'])
			message += "\n\n\n"

		message += "This message was generated on %s at %s.\n" % (time.strftime("%d/%m/%Y"), time.strftime("%H:%M:%S"))
		message += "If you would like to be removed from this list, please send a message to Jeff Roecks at jroecks@gmail.com"

		return message
def main():
	# create the scraper
	scraper = FalconsScheduleScraper()
	scraper.start()

# execute main
if __name__ == "__main__":
	main()
