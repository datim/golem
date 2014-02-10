#!/usr/bin/python
# class that can send emails.
import smtplib
import copy
import logging
from email.mime.text import MIMEText

class EmailerRoutine(object):
	"""
	Wrap ability to send emails to recipients in a class
	"""

	def __init__(self):
		""" constructor """
		pass

	def email(self, service_provider, user, password, to, cc, bcc, subject, message):
		"""
		Send an email.

		Args:
			service_provider: string specifying service provider
			user: user account
			password: password for user account
			to: list of recipients
			cc: list of recipients
			bcc: list of recipients
			subject: email subject
			message: email content

		Returns:
			N.A.
		"""

		server = None
		success = False

		# read config file

		if service_provider == "gmail":
			# the user wants to use a gmail provider. Set it up

			# read config
			server = self._setup_gmail_provider(user, password)

		if server:

			# read config file, including from
			self._send_email(server, user, to, cc, bcc, subject, message)
			success = True

			self._stop_server(server)

		return success

	def _setup_gmail_provider(self, username, password):
		"""
		Create a connection to an gmail service provider"
	
		Args:
			Username: gmail user name
			password: gmail password

		Returns:
			Configured server object
		"""

		server = smtplib.SMTP('smtp.gmail.com:587')
		server.starttls()  

		server.login(username,password)  

		return server

	def _send_email(self, server, user, to_list, cc_list, bcc_list, subject, message):
		"""
		Send an email message

		Args:
			server: initialized email server obj
			user: sender email
			to_list: recipient list
			cc_list: recipient list
			bcc_list: recipient list
			subject: email subject
			message: email message

		Returns:
			N.A.
		"""
		msg = MIMEText(message)

		msg['To'] = ', '.join(to_list)
		msg['Cc'] = ', '.join(cc_list)
		msg['Bcc'] = ', '.join(bcc_list)
		msg['From'] = user
		msg['Subject'] = subject

		logging.info("Emailing to: %s, cc: %s, bcc: %s" % (to_list, cc_list, bcc_list))

		all_recipients_list = copy.copy(to_list)
		all_recipients_list.extend(cc_list)
		all_recipients_list.extend(bcc_list)

		server.sendmail(user, all_recipients_list, msg.as_string())

	def _stop_server(self, server):
		""" 
		stop the server
	
		Args:
			Server object to stop

		Returns:
			N.A.
		"""

		server.quit()
