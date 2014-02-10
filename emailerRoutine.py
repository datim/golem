#!/usr/bin/python
import smtplib
from email.mime.text import MIMEText

class EmailerRoutine(object):

	def __init__(self):
		pass

	def email(self, service_provider, user, password, to, cc, bcc, subject, message):
		"""
		Send an email.

		Args:
			service_provider: string specifying service provider
			user: user account
			password: password for user account
			to: list of 
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

		server = smtplib.SMTP('smtp.gmail.com:587')
		server.starttls()  

		server.login(username,password)  

		return server

	def _send_email(self, server, user, to_list, cc_list, bcc_list, subject, message):
		"""
		Send an email message
		"""
		msg = MIMEText(message)

		msg['To'] = ', '.join(to_list)
		msg['Cc'] = ', '.join(cc_list)
		msg['Bcc'] = ', '.join(bcc_list)
		msg['From'] = user
		msg['Subject'] = subject

		server.sendmail(user, to_list, msg.as_string())
		

		# construct the message header
		#headers = ["from: " + user,
        #   "subject: " + subject,
        #   "to: " + '. '.join(to_list)]

		#headers = "\r\n".join(headers)

		#server.sendmail(user, to, headers + "\n" + message)  

	def _stop_server(self, server):
		""" 
		stop the server
		"""
		server.quit()
