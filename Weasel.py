
from PyQt5 import QtCore 
from PyQt5.QtCore import  Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QMainWindow, 
        QMdiArea, QMessageBox, QWidget, QGridLayout, QVBoxLayout, QMdiSubWindow, 
        QPushButton, QStatusBar, QLabel, QAbstractSlider, QHeaderView,
        QTreeWidget, QTreeWidgetItem, QGridLayout, QSlider, QCheckBox,  
        QProgressBar, QComboBox, QTableWidget, QTableWidgetItem )
from PyQt5.QtGui import QCursor, QIcon, QColor

import pyqtgraph as pg
import os
import sys
import time
import numpy as np
import math
import logging
import importlib
from scipy.stats import iqr

#Add folders CoreModules  Developer/ModelLibrary to the Module Search Path. 
#path[0] is the current working directory
sys.path.append(os.path.join(sys.path[0],'Developer//WEASEL//Tools//'))
sys.path.append(os.path.join(sys.path[0],
        'Developer//WEASEL//Tools//FERRET_Files//'))
sys.path.append(os.path.join(sys.path[0],'CoreModules'))
import CoreModules.readDICOM_Image as readDICOM_Image
import CoreModules.saveDICOM_Image as saveDICOM_Image
import Developer.WEASEL.Tools.copyDICOM_Image as copyDICOM_Image
import CoreModules.WriteXMLfromDICOM as WriteXMLfromDICOM
import Developer.WEASEL.Tools.binaryOperationDICOM_Image as binaryOperationDICOM_Image
import CoreModules.styleSheet as styleSheet
from Developer.WEASEL.Tools.FERRET import FERRET as ferret
from CoreModules.weaselXMLReader import WeaselXMLReader
from CoreModules.weaselToolsXMLReader import WeaselToolsXMLReader


__version__ = '1.0'
__author__ = 'Steve Shillitoe'

FERRET_LOGO = 'images\\FERRET_LOGO.png'
#Create and configure the logger
#First delete the previous log file if there is one
LOG_FILE_NAME = "WEASEL1.log"
if os.path.exists(LOG_FILE_NAME):
    os.remove(LOG_FILE_NAME) 
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename=LOG_FILE_NAME, 
                level=logging.INFO, 
                format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class Weasel(QMainWindow):
    def __init__(self): 
        """Creates the MDI container."""
        super (). __init__ () 
        self.showFullScreen()
        self.setWindowTitle("WEASEL")
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.centralwidget.setLayout(QVBoxLayout(self.centralwidget))
        self.mdiArea = QMdiArea(self.centralwidget)
        self.mdiArea.tileSubWindows()
        self.centralwidget.layout().addWidget(self.mdiArea)
        self.setupMenus()
        self.setupToolBar()
        self.currentImagePath = ''
        self.statusBar = QStatusBar()
        self.centralwidget.layout().addWidget(self.statusBar)
        self.selectedStudy = ''
        self.selectedSeries = ''
        self.selectedImagePath = ''
        self.selectedImageName = ''
        self.ApplyStyleSheet()
         # XML reader object to process XML configuration file
        self.objXMLReader = WeaselXMLReader() 
        logger.info("WEASEL GUI created successfully.")


    def buildUserDefinedToolsMenuItem(self, tool):
        try:
            #create action button on the fly
            logger.info("WEASEL buildUserDefinedToolsMenuItem called.")
            self.menuItem = QAction(tool.find('action').text, self)
            self.menuItem.setShortcut(tool.find('shortcut').text)
            self.menuItem.setToolTip(tool.find('tooltip').text)
            if tool.find('applies_both_images_series').text == 'True':
                boolApplyBothImagesAndSeries = True
            else:
                #Only acts on a series
                boolApplyBothImagesAndSeries = False
            self.menuItem.setData(boolApplyBothImagesAndSeries)
            self.menuItem.setEnabled(False)
            moduleName = tool.find('module').text
            function = tool.find('function').text
            objFunction = getattr(importlib.import_module(moduleName, 
                                        package=None),
                                        function)
            self.menuItem.triggered.connect(lambda : objFunction(self))
            self.toolsMenu.addAction(self.menuItem)
        except Exception as e:
            print('Error in function WEASEL.buildUserDefinedToolsMenuItem: ' + str(e))


    def addUserDefinedToolsMenuItems(self):
        try:
            logger.info("WEASEL addUserDefinedToolsMenuItems called.")
            self.objXMLReader = WeaselToolsXMLReader() 
            tools = self.objXMLReader.getTools()
            for tool in tools:
                self.buildUserDefinedToolsMenuItem(tool)
        except Exception as e:
            print('Error in function WEASEL.addUserDefinedToolsMenuItem: ' + str(e))


    def buildFileMenu(self):
        try:
            loadDICOM = QAction('&Load DICOM Images', self)
            loadDICOM.setShortcut('Ctrl+L')
            loadDICOM.setStatusTip('Load DICOM images from a scan folder')
            loadDICOM.triggered.connect(self.loadDICOM)
            self.fileMenu.addAction(loadDICOM)

            tileSubWindows = QAction('&Tile Subwindows', self)
            tileSubWindows.setShortcut('Ctrl+T')
            tileSubWindows.setStatusTip('Returns subwindows to a tile pattern')
            tileSubWindows.triggered.connect(self.tileAllSubWindows)
            self.fileMenu.addAction(tileSubWindows)
        
            closeAllImageWindowsButton = QAction('Close &All Image Windows', self)
            closeAllImageWindowsButton.setShortcut('Ctrl+A')
            closeAllImageWindowsButton.setStatusTip('Closes all image sub windows')
            closeAllImageWindowsButton.triggered.connect(self.closeAllImageWindows)
            self.fileMenu.addAction(closeAllImageWindowsButton)
        
            closeAllSubWindowsButton = QAction('&Close All Sub Windows', self)
            closeAllSubWindowsButton.setShortcut('Ctrl+X')
            closeAllSubWindowsButton.setStatusTip('Closes all sub windows')
            closeAllSubWindowsButton.triggered.connect(self.closeAllSubWindows)
            self.fileMenu.addAction(closeAllSubWindowsButton)
        except Exception as e:
            print('Error in function WEASEL.buildFileMenu: ' + str(e))


    def buildToolsMenu(self):
        try:
            bothImagesAndSeries = True
            self.viewImageButton = QAction('&View Image', self)
            self.viewImageButton.setShortcut('Ctrl+V')
            self.viewImageButton.setStatusTip('View DICOM Image or series')
            self.viewImageButton.triggered.connect(self.viewImage)
            self.viewImageButton.setData(bothImagesAndSeries)
            self.viewImageButton.setEnabled(False)
            self.toolsMenu.addAction(self.viewImageButton)

            self.viewMetaDataButton = QAction('&View Metadata', self)
            self.viewMetaDataButton.setShortcut('Ctrl+M')
            self.viewMetaDataButton.setStatusTip('View DICOM Image or series metadata')
            self.viewMetaDataButton.triggered.connect(self.viewMetadata)
            self.viewMetaDataButton.setData(bothImagesAndSeries)
            self.viewMetaDataButton.setEnabled(False)
            self.toolsMenu.addAction(self.viewMetaDataButton)

        
            self.deleteImageButton = QAction('&Delete Image', self)
            self.deleteImageButton.setShortcut('Ctrl+D')
            self.deleteImageButton.setStatusTip('Delete a DICOM Image or series')
            self.deleteImageButton.triggered.connect(self.deleteImage)
            self.deleteImageButton.setData(bothImagesAndSeries)
            self.deleteImageButton.setEnabled(False)
            self.toolsMenu.addAction(self.deleteImageButton)
        
            self.copySeriesButton = QAction('&Copy Series', self)
            self.copySeriesButton.setShortcut('Ctrl+C')
            self.copySeriesButton.setStatusTip('Copy a DICOM series') 
            bothImagesAndSeries = False
            self.copySeriesButton.setData(bothImagesAndSeries)
            self.copySeriesButton.triggered.connect(
                lambda:copyDICOM_Image.copySeries(self))
            self.copySeriesButton.setEnabled(False)
            self.toolsMenu.addAction(self.copySeriesButton)
        
            self.toolsMenu.addSeparator()
            self.binaryOperationsButton = QAction('&Binary Operations', self)
            self.binaryOperationsButton.setShortcut('Ctrl+B')
            self.binaryOperationsButton.setStatusTip(
                'Performs binary operations on two images')
            bothImagesAndSeries = False
            self.binaryOperationsButton.setData(bothImagesAndSeries)
            self.binaryOperationsButton.triggered.connect(
                self.displayBinaryOperationsWindow)
            self.binaryOperationsButton.setEnabled(False)
            self.toolsMenu.addAction(self.binaryOperationsButton)
        
            #Add items to the Tools menu as defined in
            #toolsMenu.xml
            self.addUserDefinedToolsMenuItems()
        
            self.toolsMenu.addSeparator()
            self.launchFerretButton = QAction(QIcon(FERRET_LOGO), '&FERRET', self)
            self.launchFerretButton.setShortcut('Ctrl+F')
            self.launchFerretButton.setStatusTip('Launches the FERRET application')
            self.launchFerretButton.triggered.connect(self.displayFERRET)
            self.launchFerretButton.setEnabled(True)
            self.toolsMenu.addAction(self.launchFerretButton)
        except Exception as e:
            print('Error in function WEASEL.buildToolsMenu: ' + str(e))


    def setupMenus(self):  
        """Builds the menus in the menu bar of the MDI"""
        logger.info("WEASEL setting up menus.")
        mainMenu = self.menuBar()
        self.fileMenu = mainMenu.addMenu('File')
        self.toolsMenu = mainMenu.addMenu('Tools')
        self.helpMenu = mainMenu.addMenu('Help')

        #File Menu
        self.buildFileMenu()

        #Tools Menu
        self.buildToolsMenu()


    def setupToolBar(self):  
        logger.info("WEASEL setting up toolbar.")
        self.launchFerretButton = QAction(QIcon(FERRET_LOGO), '&FERRET', self)
        self.launchFerretButton.triggered.connect(self.displayFERRET)
        self.toolBar = self.addToolBar("FERRET")
        self.toolBar.addAction(self.launchFerretButton)


    def ApplyStyleSheet(self):
        """Modifies the appearance of the GUI using CSS instructions"""
        try:
            self.setStyleSheet(styleSheet.TRISTAN_GREY)
            logger.info('WEASEL Style Sheet applied.')
        except Exception as e:
            print('Error in function WEASEL.ApplyStyleSheet: ' + str(e))
     

    def getScanDirectory(self):
        """Displays an open folder dialog window to allow the
        user to select the folder holding the DICOM files"""
        try:
            logger.info('WEASEL getScanDirectory called.')
            cwd = os.getcwd()
            scan_directory = QFileDialog.getExistingDirectory(
               self,
               'Select the directory containing the scan', 
               cwd, 
               QFileDialog.ShowDirsOnly)
            return scan_directory
        except Exception as e:
            print('Error in function WEASEL.getScanDirectory: ' + str(e))


    def displayMessageSubWindow(self, message, title="Loading DICOM files"):
        """
        Creates a subwindow that displays a message to the user. 
        """
        try:
            logger.info('WEASEL displayMessageSubWindow called.')
            for subWin in self.mdiArea.subWindowList():
                if subWin.objectName() == "Msg_Window":
                    subWin.close()
                    
            widget = QWidget()
            widget.setLayout(QVBoxLayout()) 
            self.msgSubWindow = QMdiSubWindow(self)
            self.msgSubWindow.setAttribute(Qt.WA_DeleteOnClose)
            self.msgSubWindow.setWidget(widget)
            self.msgSubWindow.setObjectName("Msg_Window")
            self.msgSubWindow.setWindowTitle(title)
            height, width = self.getMDIAreaDimensions()
            self.msgSubWindow.setGeometry(0,0,width*0.5,height*0.25)
            self.lblMsg = QLabel('<H4>' + message + '</H4>')
            widget.layout().addWidget(self.lblMsg)

            self.progBarMsg = QProgressBar(self)
            widget.layout().addWidget(self.progBarMsg)
            widget.layout().setAlignment(Qt.AlignTop)
            self.progBarMsg.hide()
            self.progBarMsg.setValue(0)

            self.mdiArea.addSubWindow(self.msgSubWindow)
            self.msgSubWindow.show()
            QApplication.processEvents()
        except Exception as e:
            print('Error in : WEASEL.displayMessageSubWindow' + str(e))
            logger.error('Error in : WEASEL.displayMessageSubWindow' + str(e))
    

    def buildTableView(self, dataset):
        """Builds a Table View displaying DICOM image metadata
        as Tag, name, VR & Value"""
        try:
            tableWidget = QTableWidget()
            tableWidget.setShowGrid(True)
            tableWidget.setColumnCount(4)

            #Create table header row
            headerItem = QTableWidgetItem(QTableWidgetItem("Tag\n")) 
            headerItem.setTextAlignment(Qt.AlignLeft)
            tableWidget.setHorizontalHeaderItem(0,headerItem)
            headerItem = QTableWidgetItem(QTableWidgetItem("Name \n")) 
            headerItem.setTextAlignment(Qt.AlignLeft)
            tableWidget.setHorizontalHeaderItem(1, headerItem)
            headerItem = QTableWidgetItem(QTableWidgetItem("VR \n")) 
            headerItem.setTextAlignment(Qt.AlignLeft)
            tableWidget.setHorizontalHeaderItem(2, headerItem)
            headerItem = QTableWidgetItem(QTableWidgetItem("Value\n")) 
            headerItem.setTextAlignment(Qt.AlignLeft)
            headerItem = tableWidget.setHorizontalHeaderItem(3 ,headerItem)
           
            #Create rows of metadata
            for data_element in dataset:
                #Exclude pixel data from metadata listing
                if data_element.name == 'Pixel Data':
                    continue
                rowPosition = tableWidget.rowCount()
                tableWidget.insertRow(rowPosition)
                tableWidget.setItem(rowPosition , 0, 
                                QTableWidgetItem(str(data_element.tag)))
                tableWidget.setItem(rowPosition , 1, 
                                QTableWidgetItem(data_element.name))
                tableWidget.setItem(rowPosition , 2, 
                                QTableWidgetItem(data_element.VR))
                tableWidget.setItem(rowPosition , 3, 
                                QTableWidgetItem(str(data_element.value)))

            #Resize columns to fit contents
            header = tableWidget.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

            return tableWidget
        except Exception as e:
            print('Error in : WEASEL.buildTableView' + str(e))
            logger.error('Error in : WEASEL.buildTableView' + str(e))


    def displayMetaDataSubWindow(self, tableTitle, dataset):
        """
        Creates a subwindow that displays a DICOM image's metadata. 
        """
        try:
            logger.info('WEASEL displayMetaDataSubWindow called.')
            title = "DICOM Image Metadata"
                    
            widget = QWidget()
            widget.setLayout(QVBoxLayout()) 
            self.metaDataSubWindow = QMdiSubWindow(self)
            self.metaDataSubWindow.setAttribute(Qt.WA_DeleteOnClose)
            self.metaDataSubWindow.setWidget(widget)
            self.metaDataSubWindow.setObjectName("metaData_Window")
            self.metaDataSubWindow.setWindowTitle(title)
            height, width = self.getMDIAreaDimensions()
            self.metaDataSubWindow.setGeometry(width * 0.4,0,width*0.6,height)
            lblImageName = QLabel('<H4>' + tableTitle + '</H4>')
            widget.layout().addWidget(lblImageName)

            DICOM_Metadata_Table_View = self.buildTableView(dataset) 
            
            widget.layout().addWidget(DICOM_Metadata_Table_View)

            self.mdiArea.addSubWindow(self.metaDataSubWindow)
            self.metaDataSubWindow.show()
        except Exception as e:
            print('Error in : WEASEL.displayMetaDataSubWindow' + str(e))
            logger.error('Error in : WEASEL.displayMetaDataSubWindow' + str(e))


    def setMsgWindowProgBarMaxValue(self, maxValue):
        self.progBarMsg.show()
        self.progBarMsg.setMaximum(maxValue)


    def setMsgWindowProgBarValue(self, value):
        self.progBarMsg.setValue(value)


    def closeMessageSubWindow(self):
        self.msgSubWindow.close()


    def makeDICOM_XML_File(self, scan_directory):
        """Creates an XML file that describes the contents of the scan folder,
        scan_directory.  Returns the full file path of the resulting XML file,
        which takes it's name from the scan folder."""
        try:
            logger.info("WEASEL makeDICOM_XML_File called.")
            if scan_directory:
                start_time=time.time()
                numFiles, numFolders = WriteXMLfromDICOM.get_files_info(scan_directory)
                if numFolders == 0:
                    folder = os.path.basename(scan_directory) + ' folder.'
                else:
                    folder = os.path.basename(scan_directory) + ' folder and {} '.format(numFolders) \
                        + 'subdirectory(s)'

                self.displayMessageSubWindow(
                    "Collecting {} DICOM files from the {}".format(numFiles, folder))
                scans, paths = WriteXMLfromDICOM.get_scan_data(scan_directory)
                self.displayMessageSubWindow("<H4>Reading data from each DICOM file</H4>")
                dictionary = WriteXMLfromDICOM.get_studies_series(scans)
                self.displayMessageSubWindow("<H4>Writing DICOM data to an XML file</H4>")
                xml = WriteXMLfromDICOM.open_dicom_to_xml(dictionary, scans, paths)
                self.displayMessageSubWindow("<H4>Saving XML file</H4>")
                fullFilePath = WriteXMLfromDICOM.create_XML_file(xml, scan_directory)
                self.msgSubWindow.close()
                end_time=time.time()
                xmlCreationTime = end_time - start_time 
                print('XML file creation time = {}'.format(xmlCreationTime))
                logger.info("WEASEL makeDICOM_XML_File returns {}."
                            .format(fullFilePath))
            return fullFilePath
        except Exception as e:
            print('Error in function makeDICOM_XML_File: ' + str(e))
            logger.error('Error in function makeDICOM_XML_File: ' + str(e))
 

    def existsDICOMXMLFile(self, scanDirectory):
        """This function returns True if an XML file of scan images already
        exists in the scan directory."""
        try:
            logger.info("WEASEL existsDICOMXMLFile called")
            flag = False
            with os.scandir(scanDirectory) as entries:
                    for entry in entries:
                        if entry.is_file():
                            if entry.name.lower() == \
                                os.path.basename(scanDirectory).lower() + ".xml":
                                flag = True
                                break
            return flag                   
        except Exception as e:
            print('Error in function existsDICOMXMLFile: ' + str(e))
            logger.error('Error in function existsDICOMXMLFile: ' + str(e))


    def loadDICOM(self):
        """This function is executed when the Load DICOM menu item is selected.
        It displays a folder dialog box.  After the user has selected the folder
        containing the DICOM file, an existing XML is searched for.  If one is 
        found then the user is given the option of using it, rather than build
        a new one from scratch.
        """
        try:
            logger.info("WEASEL loadDICOM called")
            self.closeAllSubWindows()

            #browse to DICOM folder and get DICOM folder name
            scan_directory = self.getScanDirectory()
            if scan_directory:
                #look inside DICOM folder for XML file with same name as DICOM folder
                if self.existsDICOMXMLFile(scan_directory):
                    #an XML file exists, so ask user if they wish to use it or create new one
                    buttonReply = QMessageBox.question(self, 
                        'Load DICOM images', 
                        'An XML file exists for this DICOM folder. Would you like to use it?', 
                            QMessageBox.Yes| QMessageBox.No, QMessageBox.Yes)
                    if buttonReply == QMessageBox.Yes:
                        XML_File_Path = scan_directory + '//' + os.path.basename(scan_directory) + '.xml'
                    else:
                        #the user wishes to create a new xml file,
                        #thus overwriting the old one
                        QApplication.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))
                        XML_File_Path = self.makeDICOM_XML_File(scan_directory)
                        QApplication.restoreOverrideCursor()
                else:
                    #if there is no XML file, create one
                    QApplication.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))
                    XML_File_Path = self.makeDICOM_XML_File(scan_directory)
                    QApplication.restoreOverrideCursor()

                QApplication.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))
                self.makeDICOMStudiesTreeView(XML_File_Path)
                QApplication.restoreOverrideCursor()

        except Exception as e:
            print('Error in function loadDICOM: ' + str(e))
            logger.error('Error in function loadDICOM: ' + str(e))
         

    def getMDIAreaDimensions(self):
        return self.mdiArea.height(), self.mdiArea.width() 


    def makeDICOMStudiesTreeView(self, XML_File_Path):
        """Uses an XML file that describes a DICOM file structure to build a
        tree view showing a visual representation of that file structure."""
        try:
            logger.info("WEASEL makeDICOMStudiesTreeView called")
            if os.path.exists(XML_File_Path):
                self.DICOM_XML_FilePath = XML_File_Path
                self.DICOMfolderPath, _ = os.path.split(XML_File_Path)
                start_time=time.time()
                self.objXMLReader.parseXMLFile(
                    self.DICOM_XML_FilePath)
                end_time=time.time()
                XMLParseTime = end_time - start_time
                print('XML Parse Time = {}'.format(XMLParseTime))

                start_time=time.time()
                numStudies, numSeries, numImages, numTreeViewItems \
                    = self.objXMLReader.getNumberItemsInTreeView()

                QApplication.processEvents()
                widget = QWidget()
                widget.setLayout(QVBoxLayout()) 
                subWindow = QMdiSubWindow(self)
                subWindow.setWidget(widget)
                subWindow.setObjectName("tree_view")
                subWindow.setWindowTitle("DICOM Study Structure")
                height, width = self.getMDIAreaDimensions()
                subWindow.setGeometry(0, 0, width * 0.4, height)
                self.mdiArea.addSubWindow(subWindow)

                self.lblLoading = QLabel('<H4>You are loading {} study(s), with {} series containing {} images</H4>'
                 .format(numStudies, numSeries, numImages))
                self.lblLoading.setWordWrap(True)

                widget.layout().addWidget(self.lblLoading)
                self.progBar = QProgressBar(self)
                widget.layout().addWidget(self.progBar)
                widget.layout().setAlignment(Qt.AlignTop)
                self.progBar.show()
                self.progBar.setMaximum(numTreeViewItems)
                self.progBar.setValue(0)
                subWindow.show()

                QApplication.processEvents()
                self.treeView = QTreeWidget()
                self.treeView.setUniformRowHeights(True)
                self.treeView.setColumnCount(4)
                self.treeView.setHeaderLabels(["DICOM Files", "Date", "Time", "Path"])
                
                treeWidgetItemCounter = 0 
                studies = self.objXMLReader.getStudies()
                for study in studies:
                    studyID = study.attrib['id']
                    studyBranch = QTreeWidgetItem(self.treeView)
                    treeWidgetItemCounter += 1
                    self.progBar.setValue(treeWidgetItemCounter)
                    studyBranch.setText(0, "Study - {}".format(studyID))
                    studyBranch.setFlags(studyBranch.flags() & ~Qt.ItemIsSelectable)
                    studyBranch.setExpanded(True)
                    self.seriesBranchList = []
                    for series in study:
                        seriesID = series.attrib['id']
                        seriesBranch = QTreeWidgetItem(studyBranch)
                        self.seriesBranchList.append(seriesBranch)
                        treeWidgetItemCounter += 1
                        self.progBar.setValue(treeWidgetItemCounter)
                        #seriesBranch.setFlags(seriesBranch.flags() | Qt.ItemIsUserCheckable)
                        seriesBranch.setText(0, "Series - {}".format(seriesID))
                        seriesBranch.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                        #Expand this series branch, so that the 3 resizeColumnToContents
                        #commands can work
                        seriesBranch.setExpanded(True)
                        for image in series:
                            #Extract filename from file path
                            if image.find('name').text:
                                imageName = os.path.basename(image.find('name').text)
                            else:
                                imageName = 'Name missing'
                            #print (imageName)
                            imageDate = image.find('date').text
                            imageTime = image.find('time').text
                            imagePath = image.find('name').text
                            imageLeaf = QTreeWidgetItem(seriesBranch)
                            treeWidgetItemCounter += 1
                            self.progBar.setValue(treeWidgetItemCounter)
                            imageLeaf.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                            #Uncomment the next 2 lines to put a checkbox in front of each image
                            #imageLeaf.setFlags(imageLeaf.flags() | Qt.ItemIsUserCheckable)
                            #imageLeaf.setCheckState(0, Qt.Unchecked)
                            imageLeaf.setText(0, 'Image - ' + imageName)
                            imageLeaf.setText(1, imageDate)
                            imageLeaf.setText(2, imageTime)
                            imageLeaf.setText(3, imagePath)
                self.treeView.resizeColumnToContents(0)
                self.treeView.resizeColumnToContents(1)
                self.treeView.resizeColumnToContents(2)
                #self.treeView.resizeColumnToContents(3)
                self.treeView.hideColumn(3)
                
                #Now collapse all series branches so as to hide the images
                for branch in self.seriesBranchList:
                    branch.setExpanded(False)
                self.treeView.itemSelectionChanged.connect(self.toggleToolButtons)
                self.treeView.itemDoubleClicked.connect(self.viewImage)
                self.treeView.itemClicked.connect(self.onTreeViewItemClicked)
                self.treeView.show()
                end_time=time.time()
                TreeViewTime = end_time - start_time
                print('Tree View create Time = {}'.format(TreeViewTime))
                
                self.lblLoading.clear()
                self.progBar.hide()
                self.progBar.reset()
                widget.layout().addWidget(self.treeView)   
        except Exception as e:
            print('Error in makeDICOMStudiesTreeView: ' + str(e)) 
            logger.error('Error in makeDICOMStudiesTreeView: ' + str(e)) 


    @QtCore.pyqtSlot(QTreeWidgetItem, int)
    def onTreeViewItemClicked(self, item, col):
        """When a DICOM study treeview item is clicked, this function
        populates the relevant class variables that store the following
        DICOM image data: study ID, Series ID, Image name, image file path"""
        logger.info("WEASEL onTreeViewItemClicked called")
        selectedText = item.text(0)
        if 'study' in selectedText.lower():
            studyID = selectedText.replace('Study -', '').strip()
            self.selectedStudy = studyID
            self.selectedSeries = ''
            self.selectedImagePath = ''
            self.selectedImageName = ''
            self.statusBar.showMessage('Study - ' + studyID + ' selected.')
        elif 'series' in selectedText.lower():
            seriesID = selectedText.replace('Series -', '').strip()
            studyID = item.parent().text(0).replace('Study -', '').strip()
            self.selectedStudy = studyID
            self.selectedSeries = seriesID
            self.selectedImagePath = ''
            self.selectedImageName = ''
            fullSeriesID = studyID + ': ' + seriesID + ': no image selected.'
            self.statusBar.showMessage('Study and series - ' +  fullSeriesID)
        elif 'image' in selectedText.lower():
            imageID = selectedText.replace('Image -', '')
            imagePath =item.text(3)
            seriesID = item.parent().text(0).replace('Series -', '').strip()
            studyID = item.parent().parent().text(0).replace('Study -', '').strip()
            self.selectedStudy = studyID
            self.selectedSeries = seriesID
            self.selectedImagePath = imagePath.strip()
            self.selectedImageName = imageID.strip()
            fullImageID = studyID + ': ' + seriesID + ': '  + imageID
            self.statusBar.showMessage('Image - ' + fullImageID + ' selected.')


    def closeAllSubWindows(self):
        """Closes all the sub windows open in the MDI"""
        logger.info("WEASEL closeAllSubWindows called")
        self.mdiArea.closeAllSubWindows()
        self.treeView = None

        
    def displayFERRET(self):
        """
        Displays FERRET in a sub window 
        """
        try:
            logger.info("WEASEL displayFERRET called")
            self.closeAllSubWindows()
            self.subWindow = QMdiSubWindow(self)
            self.subWindow.setAttribute(Qt.WA_DeleteOnClose)
            self.subWindow.setWindowFlags(Qt.CustomizeWindowHint | 
                                          Qt.WindowCloseButtonHint)
            
            ferretWidget = ferret(self.subWindow, self.statusBar)
            self.subWindow.setWidget(ferretWidget.returnFerretWidget())
            
            self.subWindow.setWindowTitle('FERRET')
            self.subWindow.setWindowIcon(QIcon(FERRET_LOGO))
            self.mdiArea.addSubWindow(self.subWindow)
            self.subWindow.showMaximized()
        except Exception as e:
            print('Error in displayFERRET: ' + str(e))
            logger.error('Error in makeDICOMStudiesTreeView: ' + str(e)) 


    def setUpViewBoxForImage(self, imageViewer, layout):
        #viewBox = imageViewer.addViewBox()
        #viewBox.setAspectLocked(True)
        plotItem = imageViewer.addPlot() 
        plotItem.getViewBox().setAspectLocked() 
        img = pg.ImageItem(border='w')
        #viewBox.addItem(img)
        
        imv= pg.ImageView(view=plotItem, imageItem=img)
        imv.ui.roiBtn.hide()
        imv.ui.menuBtn.hide()
        layout.addWidget(imv)
        return img, imv, plotItem


    def setUpROITool(self, viewBox, layout, img):
        
        lblROIMeanValue = QLabel("<h4>ROI Mean Value:</h4>")
        lblROIMeanValue.show()
        layout.addWidget(lblROIMeanValue)

        lblPixelValue = QLabel("<h4>Pixel Value:</h4>")
        lblPixelValue.show()
        layout.addWidget(lblPixelValue)

        polyLineROI = pg.PolyLineROI([[80, 60], [90, 30], [60, 40]], 
                                     pen=pg.mkPen(pg.mkColor(9, 169, 188),
                                        width=3,
                                        style=QtCore.Qt.SolidLine), 
                                     closed=True)
        polyLineROI.setPos(0,0)
        viewBox.addItem(polyLineROI)
        polyLineROI.sigRegionChanged.connect(
            lambda: self.updateROIMeanValue(polyLineROI, 
                                           img.image, 
                                           img, 
                                           lblROIMeanValue))

        btnResetROI = QPushButton('Reset ROI')
        btnResetROI.clicked.connect(lambda: self.resetROI(polyLineROI))
        layout.addWidget(btnResetROI)
        return  lblPixelValue, polyLineROI, lblROIMeanValue,


    def displayPixelArray(self, pixelArray, 
                          lblImageMissing, lblPixelValue,
                          imv, multiImage=False, deleteButton=None):
        #create dummy button to prevent runtime error
        try:
            if deleteButton is None:
                deleteButton = QPushButton()
                deleteButton.hide()

            #Check that pixel array holds an image & display it
            if pixelArray is None:
                lblImageMissing.show()
                if multiImage:
                    deleteButton.hide()
                imv.setImage(np.array([[0,0,0],[0,0,0]]))  
            else:
                minimumValue = np.amin(pixelArray) if (np.median(pixelArray) - iqr(pixelArray, rng=(
                    1, 99))/2) < np.amin(pixelArray) else np.median(pixelArray) - iqr(pixelArray, rng=(1, 99))/2
                maximumValue = np.amax(pixelArray) if (np.median(pixelArray) + iqr(pixelArray, rng=(
                    1, 99))/2) > np.amax(pixelArray) else np.median(pixelArray) + iqr(pixelArray, rng=(1, 99))/2
                imv.setImage(pixelArray) #autoHistogramRange=False, levels=(minimumValue, maximumValue)
                lblImageMissing.hide()   
  
                imv.getView().scene().sigMouseMoved.connect(
                   lambda pos: self.getPixelValue(pos, imv, pixelArray, lblPixelValue))
                if multiImage:
                    deleteButton.show()
        except Exception as e:
            print('Error in displayPixelArray: ' + str(e))
            logger.error('Error in displayPixelArray: ' + str(e)) 


    def getPixelValue(self, pos, imv, pixelArray, lblPixelValue):
        try:
            #print ("Image position: {}".format(pos))
            container = imv.getView()
            if container.sceneBoundingRect().contains(pos): 
                mousePoint = container.getViewBox().mapSceneToView(pos) 
                x_i = math.floor(mousePoint.x())
                y_i = math.floor(mousePoint.y()) 
                z_i = imv.currentIndex + 1
                if (len(np.shape(pixelArray)) == 2) and y_i > 0 and y_i < pixelArray.shape [ 0 ] \
                    and x_i > 0 and x_i < pixelArray.shape [ 1 ]: 
                    lblPixelValue.setText(
                        "<h4>Pixel Value = {} @ X: {}, Y: {}</h4>"
                   .format (round(pixelArray[ x_i, y_i ], 3), x_i, y_i))
                elif (len(np.shape(pixelArray)) == 3) and z_i > 0 and z_i < pixelArray.shape [ 0 ] \
                    and y_i > 0 and y_i < pixelArray.shape [ 1 ] \
                    and x_i > 0 and x_i < pixelArray.shape [ 2 ]: 
                    lblPixelValue.setText(
                        "<h4>Pixel Value = {} @ X: {}, Y: {}, Z: {}</h4>"
                    .format (round(pixelArray[ z_i, y_i, x_i ], 3), x_i, y_i, z_i))
                else:
                    lblPixelValue.setText("<h4>Pixel Value:</h4>")
            else:
                lblPixelValue.setText("<h4>Pixel Value:</h4>")
                   
        except Exception as e:
            print('Error in getPixelValue: ' + str(e))
            logger.error('Error in getPixelValue: ' + str(e))


    def displayImageSubWindow(self, pixelArray, imagePath):
        """
        Creates a subwindow that displays the DICOM image contained in pixelArray. 
        """
        try:
            logger.info("WEASEL displayImageSubWindow called")
            imageViewer, layout, lblImageMissing, subWindow = \
                self.setUpImageViewerSubWindow()
            windowTitle = self.getDICOMFileData()
            subWindow.setWindowTitle(windowTitle)
            img, imv, viewBox = self.setUpViewBoxForImage(imageViewer, layout)
            

            #chkBoxSyncROI = QCheckBox("Synchronise ROIs in other windows with this one")
            #chkBoxSyncROI.setToolTip("Check to synchronise ROIs in other windows with this one")
            #layout.addWidget(chkBoxSyncROI)
            

            lblPixelValue, _ , _ = self.setUpROITool(viewBox, layout, img)
           
           
            self.displayPixelArray(pixelArray, 
                                   lblImageMissing,
                                   lblPixelValue,
                                 imv)  
        except Exception as e:
            print('Error in Weasel.displayImageSubWindow: ' + str(e))
            logger.error('Error in Weasel.displayImageSubWindow: ' + str(e)) 


    def resetROI(self, polyLineROI):
        polyLineROI.setPos(0,0)
        polyLineROI.setPoints([[80, 60], [90, 30], [60, 40]])


    def synchroniseROIs(self, chkBox):
        """Synchronises the ROIs in all the open image subwindows"""
        logger.info("WEASEL synchroniseROIs")
        if chkBox.isChecked():
            for subWin in self.mdiArea.subWindowList():
                if (subWin.objectName() == 'tree_view' 
                    or subWin.objectName() == 'Binary_Operation'
                    or subWin.objectName() == 'Msg_Window'
                    or subWin.objectName() == 'metaData_Window'):
                    continue
                print ('subwindow object name ', subWin.objectName())
                for item in subWin.widget().children():
                    print ('item', item)
                    for child in item.children():
                        print ('child of item    ', child)
               
                    
                QApplication.processEvents()


    def updateROIMeanValue(self, roi, pixelArray, imgItem, lbl):
        try:
            #As image's axis order is set to
            #'row-major', then the axes are specified 
            #in (y, x) order, axes=(1,0)
            arrRegion = roi.getArrayRegion(pixelArray, imgItem, axes=(1,0), returnMappedCoords=False)
            roiMean = round(np.mean(arrRegion), 3)
            lbl.setText("<h4>ROI Mean Value = {}</h4>".format(str(roiMean)))
            if len(arrRegion) <4:
                print(arrRegion)
           # _, coords = roi.getArrayRegion(pixelArray, imgItem, 
            #                                returnMappedCoords=True)
            
            
        except Exception as e:
            print('Error in Weasel.updateROIMeanValue: ' + str(e))
            logger.error('Error in Weasel.updateROIMeanValue: ' + str(e)) 
        

    def setUpImageViewerSubWindow(self):
        pg.setConfigOptions(imageAxisOrder='row-major')
        subWindow = QMdiSubWindow(self)
        subWindow.setObjectName = 'image_viewer'
        subWindow.setAttribute(Qt.WA_DeleteOnClose)
        subWindow.setWindowFlags(Qt.CustomizeWindowHint | 
                                      Qt.WindowCloseButtonHint | 
                                      Qt.WindowMinimizeButtonHint)
        
        
        height, width = self.getMDIAreaDimensions()
        subWindow.setGeometry(0,0,width*0.3,height*0.5)
        self.mdiArea.addSubWindow(subWindow)
        
        layout = QVBoxLayout()
        imageViewer = pg.GraphicsLayoutWidget()
        widget = QWidget()
        widget.setLayout(layout)
        subWindow.setWidget(widget)
        
        lblImageMissing = QLabel("<h4>Image Missing</h4>")
        lblImageMissing.hide()
        layout.addWidget(lblImageMissing)
        subWindow.show()
        return imageViewer, layout, lblImageMissing, subWindow


    def displayMultiImageSubWindow(self, imageList, studyName, 
                     seriesName, sliderPosition = -1):
        """
        Creates a subwindow that displays all the DICOM images in a series. 
        A slider allows the user to navigate  through the images.  A delete
        button allows the user to delete the image they are viewing.
        """
        try:
            logger.info("WEASEL displayMultiImageSubWindow called")
            imageViewer, layout, lblImageMissing, subWindow = \
                self.setUpImageViewerSubWindow()
            
            #Study ID & Series ID are stored locally on the
            #sub window in case the user wishes to delete an
            #image in the series.  They may have several series
            #open at once, so the selected series on the treeview
            #may not the same as that from which the image is
            #being deleted.
            lblHiddenStudyID = QLabel(studyName)
            lblHiddenStudyID.hide()
            lblHiddenSeriesID = QLabel(seriesName)
            lblHiddenSeriesID.hide()
            btnDeleteDICOMFile = QPushButton('Delete DICOM Image')
            btnDeleteDICOMFile.setToolTip(
            'Deletes the DICOM image being viewed')
            btnDeleteDICOMFile.hide()
            btnDeleteDICOMFile.clicked.connect(lambda:
                                               self.deleteImageInMultiImageViewer(
                                      imageList[imageSlider.value() - 1], 
                                      lblHiddenStudyID.text(), 
                                      lblHiddenSeriesID.text(),
                                      imageSlider.value()))
            
            layout.addWidget(lblHiddenSeriesID)
            layout.addWidget(lblHiddenStudyID)
            layout.addWidget(btnDeleteDICOMFile)
           
            img, imv, viewBox = self.setUpViewBoxForImage(imageViewer, layout)           
           
            lblPixelValue, roiTool, lblROIMeanValue = self.setUpROITool(viewBox, layout, img)

            imageSlider = QSlider(Qt.Horizontal)
            imageSlider.setMinimum(1)
            imageSlider.setMaximum(len(imageList))
            if sliderPosition == -1:
                imageSlider.setValue(1)
            else:
                imageSlider.setValue(sliderPosition)
            imageSlider.setSingleStep(1)
            imageSlider.setTickPosition(QSlider.TicksBothSides)
            imageSlider.setTickInterval(1)
            layout.addWidget(imageSlider)
            imageSlider.valueChanged.connect(
                  lambda: self.imageSliderMoved(seriesName, 
                                                imageList, 
                                                imageSlider.value(),
                                                lblImageMissing,
                                                lblPixelValue,
                                                btnDeleteDICOMFile,
                                                imv,
                                                subWindow))
            imageSlider.valueChanged.connect(
                  lambda: self.updateROIMeanValue(roiTool, 
                                               img.image, 
                                               img, 
                                               lblROIMeanValue))
            #print('Num of images = {}'.format(len(imageList)))
            #Display the first image in the viewer
            self.imageSliderMoved(seriesName, 
                                  imageList,
                                  imageSlider.value(),
                                  lblImageMissing,
                                  lblPixelValue,
                                  btnDeleteDICOMFile,
                                  imv,
                                  subWindow)
        except Exception as e:
            print('Error in displayMultiImageSubWindow: ' + str(e))
            logger.error('Error in displayMultiImageSubWindow: ' + str(e))


    def deleteImageInMultiImageViewer(self, currentImagePath, 
                                      studyID, seriesID,
                                      lastSliderPosition):
        """When the Delete button is clicked on the multi image viewer,
        this function deletes the physical image and removes the 
        reference to it in the XML file."""
        try:
            logger.info("WEASEL deleteImageInMultiImageViewer called")
            imageName = os.path.basename(currentImagePath)
            #print ('study id {} series id {}'.format(studyID, seriesID))
            buttonReply = QMessageBox.question(self, 
                'Delete DICOM image', "You are about to delete image {}".format(imageName), 
                QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)

            if buttonReply == QMessageBox.Ok:
                #Delete physical file
                os.remove(currentImagePath)
                #Remove deleted image from the list
                self.imageList.remove(currentImagePath)

                #Refresh the multi-image viewer to remove deleted image
                #First close it
                self.closeSubWindow(seriesID)
                
                if len(self.imageList) == 0:
                    #Only redisplay the multi-image viewer if there
                    #are still images in the series to display
                    #The image list is empty, so do not redisplay
                    #multi image viewer 
                    pass   
                elif len(self.imageList) == 1:
                    #There is only one image left in the display
                    self.displayMultiImageSubWindow(self.imageList, studyID, seriesID)
                elif len(self.imageList) + 1 == lastSliderPosition:    
                     #we are deleting the nth image in a series of n images
                     #so move the slider back to penultimate image in list 
                    self.displayMultiImageSubWindow(self.imageList, 
                                      studyID, seriesID, len(self.imageList))
                else:
                    #We are deleting an image at the start of the list
                    #or in the body of the list. Move slider forwards to 
                    #the next image in the list.
                    self.displayMultiImageSubWindow(self.imageList, 
                                      studyID, seriesID, lastSliderPosition)
     
                #Now update XML file
                #Get the series containing this image and count the images it contains
                #If it is the last image in a series then remove the
                #whole series from XML file
                #If it is not the last image in a series
                #just remove the image from the XML file 
                images = self.objXMLReader.getImageList(studyID, seriesID)
                if len(images) == 1:
                    #only one image, so remove the series from the xml file
                    #need to get study (parent) containing this series (child)
                    #then remove child from parent
                    self.objXMLReader.removeSeriesFromXMLFile(studyID, seriesID)
                elif len(images) > 1:
                    #more than 1 image in the series, 
                    #so just remove the image from the xml file
                    ##need to get the series (parent) containing this image (child)
                    ##then remove child from parent
                    self.objXMLReader.removeOneImageFromSeries(
                        studyID, seriesID, currentImagePath)
                #Update tree view with xml file modified above
                self.refreshDICOMStudiesTreeView()
        except Exception as e:
            print('Error in deleteImageInMultiImageViewer: ' + str(e))
            logger.error('Error in deleteImageInMultiImageViewer: ' + str(e))


    def imageSliderMoved(self, seriesName, imageList, imageNumber,
                        lblImageMissing, lblPixelValue, 
                        btnDeleteDICOMFile, imv,
                        subWindow):
        """On the Multiple Image Display sub window, this
        function is called when the image slider is moved. 
        It causes the next image in imageList to be displayed"""
        try:
            logger.info("WEASEL imageSliderMoved called")
            #imageNumber = self.imageSlider.value()
            currentImageNumber = imageNumber - 1
            if currentImageNumber >= 0:
                currentImagePath = imageList[currentImageNumber]
                pixelArray = readDICOM_Image.returnPixelArray(currentImagePath)
                self.displayPixelArray(pixelArray, 
                                       lblImageMissing,
                                       lblPixelValue,
                                       imv,
                                       multiImage=True,  
                                       deleteButton=btnDeleteDICOMFile) 

                subWindow.setWindowTitle(seriesName + ' - ' 
                         + os.path.basename(currentImagePath))
        except Exception as e:
            print('Error in imageSliderMoved: ' + str(e))
            logger.error('Error in imageSliderMoved: ' + str(e))


    def viewImage(self):
        """Creates a subwindow that displays a DICOM image. Either executed using the 
        'View Image' Menu item in the Tools menu or by double clicking the Image name 
        in the DICOM studies tree view."""
        try:
            logger.info("WEASEL viewImage called")
            if self.isAnImageSelected():
                imagePath = self.selectedImagePath
                pixelArray = readDICOM_Image.returnPixelArray(imagePath)
                self.displayImageSubWindow(pixelArray, imagePath)
            elif self.isASeriesSelected():
                studyID = self.selectedStudy 
                seriesID = self.selectedSeries
                self.imageList = self.objXMLReader.getImagePathList(studyID, seriesID)
                self.displayMultiImageSubWindow(self.imageList, studyID, seriesID)
        except Exception as e:
            print('Error in viewImage: ' + str(e))
            logger.error('Error in viewImage: ' + str(e))


    def viewMetadata(self):
        """Creates a subwindow that displays a DICOM image's metadata. """
        try:
            logger.info("WEASEL viewMetadata called")
            if self.isAnImageSelected():
                imagePath = self.selectedImagePath
                imageName = self.selectedImageName
                dataset = readDICOM_Image.getDicomDataset(imagePath)
                self.displayMetaDataSubWindow("Metadata for image {}".format(imageName), 
                                              dataset)
            elif self.isASeriesSelected():
                studyID = self.selectedStudy 
                seriesID = self.selectedSeries
                imageList = self.objXMLReader.getImagePathList(studyID, seriesID)
                firstImagePath = imageList[0]
                dataset = readDICOM_Image.getDicomDataset(firstImagePath)
                self.displayMetaDataSubWindow("Metadata for series {}".format(seriesID), 
                                              dataset)
        except Exception as e:
            print('Error in viewMetadata: ' + str(e))
            logger.error('Error in viewMetadata: ' + str(e))


    def getImagePathList(self, studyID, seriesID):
        return self.objXMLReader.getImagePathList(studyID, seriesID)

    def insertNewBinOpImageInXMLFile(self, newImageFileName, suffix):
        """This function inserts information regarding a new image 
        created by a binary operation on 2 images in the DICOM XML file
       """
        try:
            logger.info("WEASEL insertNewBinOpImageInXMLFile called")
            studyID = self.selectedStudy 
            seriesID = self.selectedSeries
            #returns new series ID
            return self.objXMLReader.insertNewBinOpsImageInXML(
                newImageFileName, studyID, seriesID, suffix)
        except Exception as e:
            print('Error in Weasel.insertNewBinOpImageInXMLFile: ' + str(e))
            logger.error('Error in Weasel.insertNewBinOpImageInXMLFile: ' + str(e))


    def insertNewImageInXMLFile(self, newImageFileName, suffix):
        """This function inserts information regarding a new image 
         in the DICOM XML file
       """
        try:
            logger.info("WEASEL insertNewImageInXMLFile called")
            studyID = self.selectedStudy 
            seriesID = self.selectedSeries
            imagePath = self.selectedImagePath
            #returns new series ID or existing series ID
            #as appropriate
            return self.objXMLReader.insertNewImageInXML(imagePath,
                   newImageFileName, studyID, seriesID, suffix)
            
        except Exception as e:
            print('Error in insertNewImageInXMLFile: ' + str(e))
            logger.error('Error in insertNewImageInXMLFile: ' + str(e))


    def getNewSeriesName(self, studyID, dataset, suffix):
        """This function uses recursion to find the next available
        series name.  A new series name is created by adding a suffix
        at the end of an existing series name. """
        try:
            seriesID = dataset.SeriesDescription + "_" + str(dataset.SeriesNumber)
            imageList = self.objXMLReader.getImageList(studyID, seriesID)
            if imageList:
                #A series of images already exists 
                #for the series called seriesID
                #so make another new series ID 
                #by adding the suffix to the previous
                #new series ID
                dataset.SeriesDescription = dataset.SeriesDescription + suffix
                return self.getNewSeriesName(studyID, dataset, suffix)
            else:
                logger.info("WEASEL getNewSeriesName returns seriesID {}".format(seriesID))
                return seriesID
        except Exception as e:
            print('Error in Weasel.getNewSeriesName: ' + str(e))
            print('Error in Weasel.getNewSeriesName: ' + str(e))


    def insertNewSeriesInXMLFile(self, origImageList, newImageList, suffix):
        """Creates a new series to hold the series of New images"""
        try:
            logger.info("WEASEL insertNewSeriesInXMLFile called")
            #Get current study & series IDs
            studyID = self.selectedStudy 
            seriesID = self.selectedSeries 
            #Get a new series ID
            dataset = readDICOM_Image.getDicomDataset(newImageList[0])
            newSeriesID = self.getNewSeriesName(studyID, dataset, suffix)
            self.objXMLReader.insertNewSeriesInXML(origImageList, 
                     newImageList, studyID, newSeriesID, seriesID, suffix)
            self.statusBar.showMessage('New series created: - ' + newSeriesID)
            return  newSeriesID

        except Exception as e:
            print('Error in Weasel.insertNewSeriesInXMLFile: ' + str(e))
            logger.error('Error in Weasel.insertNewImageInXMLFile: ' + str(e))


    def closeSubWindow(self, objectName):
        """Closes a particular sub window in the MDI"""
        logger.info("WEASEL closeSubWindow called for {}".format(objectName))
        for subWin in self.mdiArea.subWindowList():
            if subWin.objectName() == objectName:
                QApplication.processEvents()
                subWin.close()
                QApplication.processEvents()
                break

    def tileAllSubWindows(self):
        logger.info("WEASEL.tileAllSubWindow called")
        height, width = self.getMDIAreaDimensions()
        for subWin in self.mdiArea.subWindowList():
            if subWin.objectName() == 'tree_view':
                subWin.setGeometry(0, 0, width * 0.4, height)
            elif subWin.objectName() == 'Binary_Operation':
                subWin.setGeometry(0,0,width*0.5,height*0.5)
            elif subWin.objectName() == 'metaData_Window':
                subWin.setGeometry(width * 0.4,0,width*0.6,height)
            elif subWin.objectName() == 'image_viewer':
                subWin.setGeometry(width * 0.4,0,width*0.3,height*0.5)
        #self.mdiArea.tileSubWindows()


    def closeAllImageWindows(self):
        """Closes all the sub windows in the MDI except for
        the sub window displaying the DICOM file tree view"""
        logger.info("WEASEL closeAllImageWindows called")
        for subWin in self.mdiArea.subWindowList():
            if subWin.objectName() == 'tree_view':
                continue
            subWin.close()
            QApplication.processEvents()
               

    def displayBinaryOperationsWindow(self):
        """Displays the sub window for performing binary operations
        on 2 images"""
        try:
            logger.info("WEASEL displayBinaryOperationsWindow called")
            self.subWindow = QMdiSubWindow(self)
            self.subWindow.setAttribute(Qt.WA_DeleteOnClose)
            self.subWindow.setWindowFlags(Qt.CustomizeWindowHint
                  | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
            layout = QGridLayout()
            widget = QWidget()
            widget.setLayout(layout)
            self.subWindow.setWidget(widget)
            pg.setConfigOptions(imageAxisOrder='row-major')

            imageViewer1 = pg.GraphicsLayoutWidget()
            viewBox1 = imageViewer1.addViewBox()
            viewBox1.setAspectLocked(True)
            self.img1 = pg.ImageItem(border='w')
            viewBox1.addItem(self.img1)
            self.imv1 = pg.ImageView(view=viewBox1, imageItem=self.img1)
            self.imv1.ui.roiBtn.hide()
            self.imv1.ui.menuBtn.hide()

            imageViewer2 = pg.GraphicsLayoutWidget()
            viewBox2 = imageViewer2.addViewBox()
            viewBox2.setAspectLocked(True)
            self.img2 = pg.ImageItem(border='w')
            viewBox2.addItem(self.img2)
            self.imv2 = pg.ImageView(view=viewBox2, imageItem=self.img2)
            self.imv2.ui.roiBtn.hide()
            self.imv2.ui.menuBtn.hide()

            imageViewer3 = pg.GraphicsLayoutWidget()
            viewBox3 = imageViewer3.addViewBox()
            viewBox3.setAspectLocked(True)
            self.img3 = pg.ImageItem(border='w')
            viewBox3.addItem(self.img3)
            self.imv3 = pg.ImageView(view=viewBox3, imageItem=self.img3)
            self.imv3.ui.roiBtn.hide()
            self.imv3.ui.menuBtn.hide()

            studyID = self.selectedStudy 
            seriesID = self.selectedSeries
            self.lblImageMissing1 = QLabel("<h4>Image Missing</h4>")
            self.lblImageMissing2 = QLabel("<h4>Image Missing</h4>")
            self.lblImageMissing1.hide()
            self.lblImageMissing2.hide()

            self.btnSave = QPushButton('Save')
            self.btnSave.setEnabled(False)
            self.btnSave.clicked.connect(self.saveNewDICOMFileFromBinOp)

            studyID = self.selectedStudy 
            seriesID = self.selectedSeries
            imagePathList = self.objXMLReader.getImagePathList(studyID, 
                                                               seriesID)
            #form a list of image file names without extensions
            imageNameList = [os.path.splitext(os.path.basename(image))[0] 
                             for image in imagePathList]
            self.image_Name_Path_Dict = dict(zip(
                imageNameList, imagePathList))
            self.imageList1 = QComboBox()
            self.imageList2 = QComboBox()
            self.imageList1.currentIndexChanged.connect(
                lambda:self.displayImageForBinOp(1, self.image_Name_Path_Dict))
            self.imageList1.currentIndexChanged.connect(
                self.enableBinaryOperationsCombo)
            self.imageList1.currentIndexChanged.connect(
                lambda:self.doBinaryOperation(self.image_Name_Path_Dict))
            
            self.imageList2.currentIndexChanged.connect(
                lambda:self.displayImageForBinOp(2, self.image_Name_Path_Dict))
            self.imageList2.currentIndexChanged.connect(
                self.enableBinaryOperationsCombo)
            self.imageList2.currentIndexChanged.connect(
                lambda:self.doBinaryOperation(self.image_Name_Path_Dict))

            self.binaryOpsList = QComboBox()
            self.binaryOpsList.currentIndexChanged.connect(
                lambda:self.doBinaryOperation(self.image_Name_Path_Dict))
            self.imageList1.addItems(imageNameList)
            self.imageList2.addItems(imageNameList)
            self.binaryOpsList.addItems(
                binaryOperationDICOM_Image.listBinaryOperations)

            layout.addWidget(self.btnSave, 0, 2)
            layout.addWidget(self.imageList1, 1, 0)
            layout.addWidget(self.imageList2, 1, 1)
            layout.addWidget(self.binaryOpsList, 1, 2)
            layout.addWidget(self.lblImageMissing1, 2, 0)
            layout.addWidget(self.lblImageMissing2, 2, 1)
            #layout.addWidget(imageViewer1, 3, 0)
            #layout.addWidget(imageViewer2, 3, 1)
            #layout.addWidget(imageViewer3, 3, 2)
            layout.addWidget(self.imv1, 3, 0)
            layout.addWidget(self.imv2, 3, 1)
            layout.addWidget(self.imv3, 3, 2)
                
            self.subWindow.setObjectName('Binary_Operation')
            windowTitle = 'Binary Operations'
            self.subWindow.setWindowTitle(windowTitle)
            height, width = self.getMDIAreaDimensions()
            self.subWindow.setGeometry(0,0,width*0.5,height*0.5)
            self.mdiArea.addSubWindow(self.subWindow)
            self.subWindow.show()
        except Exception as e:
            print('Error in displayBinaryOperationsWindow: ' + str(e))
            logger.error('Error in displayBinaryOperationsWindow: ' + str(e))

    
    def saveNewDICOMFileFromBinOp(self):
        """TO DO"""
        try:
            logger.info("WEASEL saveNewDICOMFileFromBinOp called")
            suffix = '_binOp'
            imageName1 = self.imageList1.currentText()
            imagePath1 = self.image_Name_Path_Dict[imageName1]
            imageName2 = self.imageList2.currentText()
            imagePath2 = self.image_Name_Path_Dict[imageName2]
            
            binaryOperation = self.binaryOpsList.currentText()
            prefix = binaryOperationDICOM_Image.getBinOperationFilePrefix(
                                     binaryOperation)
            
            newImageFileName = prefix + '_' + imageName1 \
                + '_' + imageName2 
            newImageFilePath = os.path.dirname(imagePath1) + '\\' + \
                newImageFileName + '.dcm'
            #print(newImageFilePath)
            #Save pixel array to a file
            saveDICOM_Image.saveDicomOutputResult(newImageFilePath, imagePath1, self.binOpArray, "_"+binaryOperation+suffix, list_refs_path=[imagePath2])
            newSeriesID = self.insertNewBinOpImageInXMLFile(newImageFilePath, suffix)
            #print(newSeriesID)
            self.refreshDICOMStudiesTreeView(newSeriesID)
        except Exception as e:
            print('Error in saveNewDICOMFileFromBinOp: ' + str(e))
            logger.error('Error in saveNewDICOMFileFromBinOp: ' + str(e))


    def doBinaryOperation(self, imageDict):
        """TO DO"""
        try:
            #Get file path of image1
            imageName = self.imageList1.currentText()
            if imageName != '':
                imagePath1 = imageDict[imageName]

            #Get file path of image2
            imageName = self.imageList2.currentText()
            if imageName != '':
                imagePath2 = imageDict[imageNamelti]

            #Get binary operation to be performed
            binOp = self.binaryOpsList.currentText()
            if binOp != 'Select binary Operation' \
                and binOp != '':
                self.btnSave.setEnabled(True)
                self.binOpArray = binaryOperationDICOM_Image.returnPixelArray(
                    imagePath1, imagePath2, binOp)
                minimumValue = np.amin(self.binOpArray) if (np.median(self.binOpArray) - iqr(self.binOpArray, rng=(
                    1, 99))/2) < np.amin(self.binOpArray) else np.median(self.binOpArray) - iqr(self.binOpArray, rng=(1, 99))/2
                maximumValue = np.amax(self.binOpArray) if (np.median(self.binOpArray) + iqr(self.binOpArray, rng=(
                    1, 99))/2) > np.amax(self.binOpArray) else np.median(self.binOpArray) + iqr(self.binOpArray, rng=(1, 99))/2
                self.img3.setImage(self.binOpArray, autoHistogramRange=False, levels=(minimumValue, maximumValue)) 
            else:
                self.btnSave.setEnabled(False)
        except Exception as e:
            print('Error in doBinaryOperation: ' + str(e))
            logger.error('Error in doBinaryOperation: ' + str(e))


    def enableBinaryOperationsCombo(self):
        """TO DO"""
        if self.lblImageMissing1.isHidden() and \
            self.lblImageMissing2.isHidden():
            self.binaryOpsList.setEnabled(True)
        else:
            self.binaryOpsList.setEnabled(False)
            self.btnSave.setEnabled(False)


    def displayImageForBinOp(self, imageNumber, imageDict):
        """TO DO"""
        try:
            objImageMissingLabel = getattr(self, 'lblImageMissing' + str(imageNumber))
            objImage = getattr(self, 'img' + str(imageNumber))
            objComboBox = getattr(self, 'imageList' + str(imageNumber))

            #get name of selected image
            imageName = objComboBox.currentText()
            imagePath = imageDict[imageName]
            pixelArray = readDICOM_Image.returnPixelArray(imagePath)
            if pixelArray is None:
                objImageMissingLabel.show()
                objImage.setImage(np.array([[0,0,0],[0,0,0]])) 
            else:
                objImageMissingLabel.hide()
                minimumValue = np.amin(pixelArray) if (np.median(pixelArray) - iqr(pixelArray, rng=(
                    1, 99))/2) < np.amin(pixelArray) else np.median(pixelArray) - iqr(pixelArray, rng=(1, 99))/2
                maximumValue = np.amax(pixelArray) if (np.median(pixelArray) + iqr(pixelArray, rng=(
                    1, 99))/2) > np.amax(pixelArray) else np.median(pixelArray) + iqr(pixelArray, rng=(1, 99))/2
                objImage.setImage(pixelArray, autoHistogramRange=False, levels=(minimumValue, maximumValue))  
        except Exception as e:
            print('Error in displayImageForBinOp: ' + str(e))
            logger.error('Error in displayImageForBinOp: ' + str(e))


    def deleteImage(self):
        """TO DO"""
        """This method deletes an image or a series of images by 
        deleting the physical file(s) and then removing their entries
        in the XML file."""
        try:
            studyID = self.selectedStudy
            seriesID = self.selectedSeries
            if self.isAnImageSelected():
                imageName = self.selectedImageName
                imagePath = self.selectedImagePath
                buttonReply = QMessageBox.question(self, 
                  'Delete DICOM image', "You are about to delete image {}".format(imageName), 
                  QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                if buttonReply == QMessageBox.Ok:
                    #Delete physical file if it exists
                    if os.path.exists(imagePath):
                        os.remove(imagePath)
                    #If this image is displayed, close its subwindow
                    self.closeSubWindow(imagePath)
                    #Is this the last image in a series?
                    #Get the series containing this image and count the images it contains
                    #If it is the last image in a series then remove the
                    #whole series from XML file
                    #No it is not the last image in a series
                    #so just remove the image from the XML file 
                    images = self.objXMLReader.getImageList(studyID, seriesID)
                    if len(images) == 1:
                        #only one image, so remove the series from the xml file
                        #need to get study (parent) containing this series (child)
                        #then remove child from parent
                        self.objXMLReader.removeSeriesFromXMLFile(studyID, seriesID)
                    elif len(images) > 1:
                        #more than 1 image in the series, 
                        #so just remove the image from the xml file
                        self.objXMLReader.removeOneImageFromSeries(
                            studyID, seriesID, imagePath)
                    #Update tree view with xml file modified above
                    self.refreshDICOMStudiesTreeView()
            elif self.isASeriesSelected():
                buttonReply = QMessageBox.question(self, 
                  'Delete DICOM series', "You are about to delete series {}".format(seriesID), 
                  QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                if buttonReply == QMessageBox.Ok:
                    #Delete each physical file in the series
                    #Get a list of names of images in that series
                    imageList = self.objXMLReader.getImagePathList(studyID, 
                                                                   seriesID) 
                    #Iterate through list of images and delete each image
                    for imagePath in imageList:
                        if os.path.exists(imagePath):
                            os.remove(imagePath)
                    #Remove the series from the XML file
                    self.objXMLReader.removeSeriesFromXMLFile(studyID, seriesID)
                    self.closeSubWindow(seriesID)
                self.refreshDICOMStudiesTreeView()
        except Exception as e:
            print('Error in deleteImage: ' + str(e))
            logger.error('Error in deleteImage: ' + str(e))


    def isAnImageSelected(self):
        """Returns True is a single image is selected in the DICOM
        tree view, else returns False"""
        try:
            logger.info("WEASEL isAnImageSelected called.")
            selectedItem = self.treeView.currentItem()
            if selectedItem:
                if 'image' in selectedItem.text(0).lower():
                    return True
                else:
                    return False
            else:
               return False
        except Exception as e:
            print('Error in isAnImageSelected: ' + str(e))
            logger.error('Error in isAnImageSelected: ' + str(e))
            

    def isASeriesSelected(self):
        """Returns True is a series is selected in the DICOM
        tree view, else returns False"""
        try:
            logger.info("WEASEL isASeriesSelected called.")
            selectedItem = self.treeView.currentItem()
            if selectedItem:
                if 'series' in selectedItem.text(0).lower():
                    return True
                else:
                    return False
            else:
               return False
        except Exception as e:
            print('Error in isASeriesSelected: ' + str(e))
            logger.error('Error in isASeriesSelected: ' + str(e))


    def toggleToolButtons(self):
        """TO DO"""
        try:
            logger.info("WEASEL toggleToolButtons called.")
            tools = self.toolsMenu.actions()
            for tool in tools:
                if not tool.isSeparator():
                    if not(tool.data() is None):
                        #Assume not all tools will act on an image
                         #Assume all tools act on a series   
                        if self.isASeriesSelected():
                             tool.setEnabled(True)
                        elif self.isAnImageSelected():
                            if tool.data():
                                tool.setEnabled(True)
                            else:
                                tool.setEnabled(False) 
        except Exception as e:
            print('Error in toggleToolButtons: ' + str(e))
            logger.error('Error in toggleToolButtons: ' + str(e))


    def getDICOMFileData(self):
        """When a DICOM image is selected in the tree view, this function
        returns its description in the form - study number: series number: image name"""
        try:
            logger.info("WEASEL getDICOMFileData called.")
            selectedImage = self.treeView.selectedItems()
            if selectedImage:
                imageNode = selectedImage[0]
                seriesNode  = imageNode.parent()
                imageName = imageNode.text(0)
                series = seriesNode.text(0)
                studyNode = seriesNode.parent()
                study = studyNode.text(0)
                fullImageName = study + ': ' + series + ': '  + imageName
                return fullImageName
            else:
                return ''
        except Exception as e:
            print('Error in getDICOMFileData: ' + str(e))
            logger.error('Error in getDICOMFileData: ' + str(e))


    def expandTreeViewBranch(self, branchText = ''):
        """TO DO"""
        try:
            logger.info("WEASEL expandTreeViewBranch called.")
            for branch in self.seriesBranchList:
                seriesID = branch.text(0).replace('Series -', '')
                seriesID = seriesID.strip()
                if seriesID == branchText:
                    branch.setExpanded(True)
                else:
                    branch.setExpanded(False)
        except Exception as e:
            print('Error in expandTreeViewBranch: ' + str(e))
            logger.error('Error in expandTreeViewBranch: ' + str(e))


    def refreshDICOMStudiesTreeView(self, newSeriesName = ''):
        """Uses an XML file that describes a DICOM file structure to build a
        tree view showing a visual representation of that file structure."""
        try:
            logger.info("WEASEL refreshDICOMStudiesTreeView called.")
            #Load and parse updated XML file
            self.objXMLReader.parseXMLFile(
                    self.DICOM_XML_FilePath)
            self.treeView.clear()
            self.treeView.setColumnCount(3)
            self.treeView.setHeaderLabels(["DICOM Files", "Date", "Time", "Path"])
            studies = self.objXMLReader.getStudies()
            for study in studies:
                studyID = study.attrib['id']
                studyBranch = QTreeWidgetItem(self.treeView)
                studyBranch.setText(0, "Study - {}".format(studyID))
                studyBranch.setFlags(studyBranch.flags() & ~Qt.ItemIsSelectable)
                studyBranch.setExpanded(True)
                self.seriesBranchList.clear()
                for series in study:
                    seriesID = series.attrib['id']
                    seriesBranch = QTreeWidgetItem(studyBranch)
                    self.seriesBranchList.append(seriesBranch)
                    seriesBranch.setFlags(seriesBranch.flags() | Qt.ItemIsUserCheckable)
                    seriesBranch.setText(0, "Series - {}".format(seriesID))
                    seriesBranch.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    seriesBranch.setExpanded(True)
                    for image in series:
                        #Extract filename from file path
                        imageName = os.path.basename(image.find('name').text)
                        imageDate = image.find('date').text
                        imageTime = image.find('time').text
                        imagePath = image.find('name').text
                        imageLeaf = QTreeWidgetItem(seriesBranch)
                        imageLeaf.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                        imageLeaf.setFlags(imageLeaf.flags() | Qt.ItemIsUserCheckable)
                        #Uncomment the next line to put a checkbox in front of each image
                        #imageLeaf.setCheckState(0, Qt.Unchecked)
                        imageLeaf.setText(0, ' Image - ' +imageName)
                        imageLeaf.setText(1, imageDate)
                        imageLeaf.setText(2, imageTime)
                        imageLeaf.setText(3, imagePath)
            self.treeView.resizeColumnToContents(0)
            self.treeView.resizeColumnToContents(1)
            self.treeView.resizeColumnToContents(2)
            #Now collapse all series branches so as to hide the images
            #except the new series branch that has been created
            self.expandTreeViewBranch(newSeriesName)
            #If no tree view items are now selected,
            #disable items in the Tools menu.
            self.toggleToolButtons()
            self.treeView.hideColumn(3)
            self.treeView.show()
        except Exception as e:
            print('Error in refreshDICOMStudiesTreeView: ' + str(e))
            logger.error('Error in refreshDICOMStudiesTreeView: ' + str(e))
      

def main():
    app = QApplication(sys . argv )
    winMDI = Weasel()
    winMDI.showMaximized()
    sys.exit(app.exec())

if __name__ == '__main__':
        main()