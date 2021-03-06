from threading import Thread
import sys, os, time
from skpy import Skype

from PyQt5.QtWidgets import QMessageBox
from skypebot_MainWindow import *


class SkypeMessenger(QtCore.QObject):
	def __init__(self, skypebot):
		super(SkypeMessenger, self).__init__()
		self.skypebot = skypebot

	def sendMessageToContacts(self):
		self.skypebot.ui.status_label.setText('Status: Signing in to Skype...')
		try:
			username = self.skypebot.ui.username_lineEdit.text()
			password = self.skypebot.ui.password_lineEdit.text()
			self.skypeAccount = Skype(username, password)
			self.skypebot.ui.status_label.setText('Status: Sign in successful!')
			open('login-info.ini', 'w').write(f'{username}\n{password}')
		except Exception as e:
			self.skypebot.ui.status_label.setText('Status: Sign in failed!')
			self.skypebot.showDialog_pyqtSignal.emit('Sign in failed!', 'Could not Sign in to Skype.',
				'Make sure internet is connected and login info is correct', str(e))
			self.skypebot.ui.start_pushButton.setEnabled(True)
			return
		#--------
		message = self.skypebot.ui.message_textEdit.toPlainText()
		count = 1
		failed_count = 0
		last = len(self.skypebot.contact_ids)
		for cid in self.skypebot.contact_ids:
			try:
				self.skypebot.ui.status_label.setText(f'Status: Sending to {count} of {last}')
				self.skypeAccount.contacts[cid].chat.sendMsg(message)
				#
				waiting_time = self.skypebot.ui.waitingTime_spinBox.value()
				self.skypebot.ui.status_label.setText(f'Status: Waiting for {waiting_time} seconds...')
				time.sleep(waiting_time)
			except Exception as e:
				failed_count += 1
				open('failed.csv', 'a', encoding='utf-8').write(cid + '\n')
			count += 1
		self.skypebot.ui.status_label.setText(f'Status: Completed! {failed_count} failed.')
		self.skypebot.ui.start_pushButton.setEnabled(True)


class SkypeBot(QtCore.QObject):
	showDialog_pyqtSignal = QtCore.pyqtSignal(str, str, str, str)

	def __init__(self):
		super(SkypeBot, self).__init__()
		if os.path.isfile('failed.csv'):
			os.remove('failed.csv')
		#
		self.app = QtWidgets.QApplication(sys.argv)
		self.MainWindow = QtWidgets.QMainWindow()
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self.MainWindow)
		#
		self.__connectEvents()
		if os.path.isfile('login-info.ini'):
			try:
				login_info = open('login-info.ini', 'r').read().strip().split('\n')
				self.ui.username_lineEdit.setText(login_info[0])
				self.ui.password_lineEdit.setText(login_info[1])
			except:
				os.remove('login-info.ini')
		#
		self.MainWindow.show()
		sys.exit(self.app.exec_())

	def __connectEvents(self):
		self.ui.browse_pushButton.clicked.connect(self.__browse_pushButton__onClick)
		self.ui.start_pushButton.clicked.connect(self.__start_pushButton__onClick)
		#self.showDialog_pyqtSignal = QtCore.pyqtSignal(str, str, str, str)
		self.showDialog_pyqtSignal.connect(self.showDialog)

	def __browse_pushButton__onClick(self):
		path = QtWidgets.QFileDialog.getOpenFileName(self.MainWindow, "Select File", '.', '*.csv')[0]
		self.ui.contactsFilePath_lineEdit.setText(path)

	def __start_pushButton__onClick(self):
		self.ui.start_pushButton.setEnabled(False)
		if self.ui.contactsFilePath_lineEdit.text() == '':
			self.showDialog('File not selected!', 'Please provide contacts file.')
			self.ui.start_pushButton.setEnabled(True)
			return
		if self.ui.username_lineEdit.text() == '' or self.ui.password_lineEdit.text() == '':
			self.showDialog('Login details required!', 'Please provide a username and password.')
			self.ui.start_pushButton.setEnabled(True)
			return
		if self.ui.message_textEdit.toPlainText().strip() == '':
			self.showDialog('Empty message!', 'Message cannot be empty.')
			self.ui.start_pushButton.setEnabled(True)
			return
		#-----
		try:
			self.contact_ids = [ line for line in \
			open(self.ui.contactsFilePath_lineEdit.text(), 'r', encoding='utf-8').read().strip().split('\n') ]
		except Exception as e:
			self.showDialog('Error processing contacts file!', 'Something went wrong while reading contacts from file.',
				'Verify that the contacts file is properly formatted.', str(e))
			self.ui.start_pushButton.setEnabled(True)
			return
		#-----
		self.skype_messenger = SkypeMessenger(self)
		self.bulkMessagingThread = QtCore.QThread()
		self.skype_messenger.moveToThread(self.bulkMessagingThread)
		self.bulkMessagingThread.started.connect(self.skype_messenger.sendMessageToContacts)
		self.bulkMessagingThread.start()


	def showDialog(self, title='', text='', info_text='', detail_text=''):
		msg = QMessageBox(self.MainWindow)
		#msg = QMessageBox()
		msg.setWindowTitle(title)
		msg.setText(text)
		msg.setInformativeText(info_text)
		msg.setDetailedText(detail_text)
		msg.setStandardButtons(QMessageBox.Ok)
		retval = msg.exec_()



######
######
######

def main():
	bot = SkypeBot()

if __name__ == '__main__':
	main()