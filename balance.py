import sys, time, asyncio
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5 import uic, QtCore
import PyQt5.QtWidgets # to change style

import time
import psutil,os

# to report time and to save time
import serial # to communicate with the serial port
import serial.tools.list_ports # to find all the com used

### import the python file to control the balance
fbcontrol = 'bal_KERN25002.py'

with open(fbcontrol) as infile: # this is to make sure the file is closed
    exec(infile.read())
### end code for importing balance controller

# open the communication with the balance
mybal = BAL_KERN25002()


# set the UI file I need to use
Ui_MainWindow, QtBaseClass = uic.loadUiType("balance.ui")

class MyApp(QMainWindow):

    def __init__(self):
        super(MyApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.connect_button.clicked.connect(self.Connect)
        self.ui.tare_button.clicked.connect(self.Tare)
        self.ui.read_button.clicked.connect(self.Read)
        self.ui.kill_button.clicked.connect(self.Kill)

        # disable all the buttons until the balance is connected
        self.ui.tare_button.setEnabled(False)
        self.ui.read_button.setEnabled(False)
        self.ui.kill_button.setEnabled(False)

        self.ui.to_kill_le.setPlaceholderText("example.exe")

        self.ui.process_dropdown.installEventFilter(self) # create an event filter to detect the click on the dropdown menu
        self.ui.com_dropdown.installEventFilter(self) # create an event filter to detect the click on the dropdown menu

    # detect when the dropdown menu of the processes is clicked and populate the menu with the current processes
    def eventFilter(self,target,event):
        if target == self.ui.process_dropdown and event.type() == QtCore.QEvent.MouseButtonPress: # if the dropdown menu was clicked
            processes_list = [process.name() for process in psutil.process_iter()] # take all the current processes
            processes_list = sorted(processes_list, key=str.casefold) # sort them ignoring the case
            for process in processes_list: # add them to the dropdown menu
                self.ui.process_dropdown.addItem(process)
        elif target == self.ui.com_dropdown and event.type() == QtCore.QEvent.MouseButtonPress: # if the dropdown menu was clicked
            self.ui.com_dropdown.clear()
            # scan all the used COM ports and report them in the dropdown menu
            ports = serial.tools.list_ports.comports() # find all the used com ports
            for port, desc, hwid in sorted(ports): # loop into the list of devices and add them to the dropdown menu
                self.ui.com_dropdown.addItem(port)
            if port:
                self.ui.connect_button.setEnabled(True)
        return False
            
    # this is needed to make a pause
    async def main(self, sec):
        await asyncio.sleep(sec)

    def Connect(self):
        com_port = self.ui.com_dropdown.currentText() # take the value from the com port drop down menu and use it for the connection to balance
        mybal.connect(com_port)
        self.ui.connect_button.setText("CONNECTED")
        self.ui.connect_button.setEnabled(False)
        # now, enable the other buttons
        self.ui.tare_button.setEnabled(True)
        self.ui.read_button.setEnabled(True)
        self.ui.kill_button.setEnabled(True)

    def Tare(self):
        mybal.zero_scale() # zero the balance
        #weight, unit =  mybal.read_weight(stabilised = False, read_sleeptime = 1)
        text = "Balance zeroed." # Current reading: " + str(weight) + " gr"
        self.ui.weigth_label.setText(text)

    def Read(self):
        sec_to_wait = self.ui.sec_to_wait.value()
        asyncio.run(self.main(sec_to_wait))
        weight, unit =  mybal.read_weight(stabilised = False, read_sleeptime = 1)
        text = "Current reading: " + str(weight) + " gr"
        self.ui.weigth_label.setText(text)
    
    def Kill(self):
        process_to_kill = self.ui.to_kill_le.text()
        if process_to_kill != "":
            for process in (process for process in psutil.process_iter() if process.name()==process_to_kill):
                process.kill()
        else:
            # take dorpdown menu item
            process_to_kill = str(self.ui.process_dropdown.currentText())
            for process in (process for process in psutil.process_iter() if process.name()==process_to_kill):
                process.kill()

        mybal.zero_scale()
        text = "Balance zeroed."
        self.ui.weigth_label.setText(text)
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, " Message",
            "Are you sure you want to quit?",
            QMessageBox.Close | QMessageBox.Cancel)

        if reply == QMessageBox.Close:
            mybal.close_instrument() # close the communication
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # print(PyQt5.QtWidgets.QStyleFactory.keys()) # show available styles
    # stream = QtCore.QFile("orange.txt")
    # stream.open(QtCore.QIODevice.ReadOnly)
    # app.setStyleSheet(QtCore.QTextStream(stream).readAll())
    app.setStyle('Fusion')
    window = MyApp()
    window.show()
    sys.exit(app.exec_())