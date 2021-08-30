import os
import time
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QCursor
from PyQt5 import QtCore 
from PyQt5.QtCore import  Qt
import CoreModules.WEASEL.TreeView  as treeView
import CoreModules.WEASEL.WriteXMLfromDICOM as WriteXMLfromDICOM

def isEnabled(weasel):
    return True

logger = logging.getLogger(__name__)

def main(self):
    """This function is executed when the Load DICOM menu item is selected.
    It displays a folder dialog box.  After the user has selected the folder
    containing the DICOM file, an existing XML is searched for. If one is 
    found then the user is given the option of using it, rather than build
    a new one from scratch.
    """
    try:
        logger.info("RefreshDICOM.main called")
        self.close_all_windows()
        #browse to DICOM folder and get DICOM folder name
        #scan_directory = WriteXMLfromDICOM.getScanDirectory(self)
        scan_directory = self.DICOMFolder
        #print(" scan_directory = ",  scan_directory)
        if scan_directory:
            QApplication.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))
            XML_File_Path = WriteXMLfromDICOM.makeDICOM_XML_File(self, scan_directory)
            treeView.makeDICOMStudiesTreeView(self, XML_File_Path)
            QApplication.restoreOverrideCursor()
    except Exception as e:
        print('Error in function RefreshDICOM.main: ' + str(e))
        logger.error('Error in function RefreshDICOM.main: ' + str(e))









