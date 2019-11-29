
from PyQt5 import QtCore
from PyQt5.QtCore import  Qt
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog, QMainWindow, QLabel,
        QMdiArea, QMessageBox, QWidget, QVBoxLayout, QMdiSubWindow, QPushButton, 
        QTreeWidget, QTreeWidgetItem, QGridLayout, QSlider)
from PyQt5.QtGui import QCursor


import xml.etree.ElementTree as ET 
from xml.dom import minidom
import pyqtgraph as pg
import os
import sys
import re
import styleSheet
import viewDICOM_Image
import invertDICOM_Image
import WriteXMLfromDICOM 

__version__ = '1.0'
__author__ = 'Steve Shillitoe'

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        """Creates the MDI container."""
        QMainWindow.__init__(self, parent)
        self.setGeometry(0, 0, 2500, 1400)
        self.setWindowTitle("DICOM Prototype")
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        self.centralwidget.setLayout(QVBoxLayout(self.centralwidget))
        self.mdiArea = QMdiArea(self.centralwidget)
        self.mdiArea.tileSubWindows()
        self.centralwidget.layout().addWidget(self.mdiArea)
        self.setupMenus()
        
        #self.ApplyStyleSheet()
      

    def setupMenus(self):  
        """Builds the menus in the menu bar of the MDI"""
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        toolsMenu = mainMenu.addMenu('Tools')
        helpMenu = mainMenu.addMenu('Help')

        loadDICOMFromFolderButton = QAction('Load DICOM from scan folder', self)
        loadDICOMFromFolderButton.setShortcut('Ctrl+F')
        loadDICOMFromFolderButton.setStatusTip('Load DICOM images from a scan folder')
        loadDICOMFromFolderButton.triggered.connect(self.loadDICOM_Data_From_DICOM_Folder)
        fileMenu.addAction(loadDICOMFromFolderButton)

        loadDICOMFromXMLButton = QAction('Load DICOM from XML file', self)
        loadDICOMFromXMLButton.setShortcut('Ctrl+X')
        loadDICOMFromXMLButton.setStatusTip('Load DICOM images from an XML file')
        loadDICOMFromXMLButton.triggered.connect(self.loadDICOM_Data_From_DICOM_XML_File)
        fileMenu.addAction(loadDICOMFromXMLButton)

        closeAllSubWindowsButton = QAction('Close All Sub Windows', self)
        closeAllSubWindowsButton.setShortcut('Ctrl+C')
        closeAllSubWindowsButton.setStatusTip('Closes all sub windows')
        closeAllSubWindowsButton.triggered.connect(self.closeAllSubWindows)
        fileMenu.addAction(closeAllSubWindowsButton)

        self.viewImageButton = QAction('View Image', self)
        self.viewImageButton.setShortcut('Ctrl+V')
        self.viewImageButton.setStatusTip('View DICOM Image or series')
        self.viewImageButton.triggered.connect(self.viewImage)
        self.viewImageButton.setEnabled(False)
        toolsMenu.addAction(self.viewImageButton)

        self.invertImageButton = QAction('Invert Image', self)
        self.invertImageButton.setShortcut('Ctrl+I')
        self.invertImageButton.setStatusTip('Invert a DICOM Image or series')
        self.invertImageButton.triggered.connect(self.invertImage)
        self.invertImageButton.setEnabled(False)
        toolsMenu.addAction(self.invertImageButton)

        self.deleteImageButton = QAction('Delete Image', self)
        self.deleteImageButton.setShortcut('Ctrl+D')
        self.deleteImageButton.setStatusTip('Delete a DICOM Image or series')
        self.deleteImageButton.triggered.connect(self.deleteImage)
        self.deleteImageButton.setEnabled(False)
        toolsMenu.addAction(self.deleteImageButton)


    def ApplyStyleSheet(self):
        """Modifies the appearance of the GUI using CSS instructions"""
        try:
            self.setStyleSheet(styleSheet.TRISTAN_GREY)
        except Exception as e:
            print('Error in function ApplyStyleSheet: ' + str(e))
     

    def getScanDirectory(self):
        try:
            cwd = os.getcwd()
            scan_directory = QFileDialog.getExistingDirectory(
               self,
               'Select the directory containing the scan', 
               cwd, 
               QFileDialog.ShowDirsOnly)
            return scan_directory
        except Exception as e:
            print('Error in function getScanDirectory: ' + str(e))


    def getDICOM_XMLFile(self):
        try:
            defaultPath = os.getcwd()
            fullFilePath, _ = QFileDialog.getOpenFileName(parent=self, 
                caption="Select the XML file holding DICOM data.", 
                directory=defaultPath,
                filter="*.xml")
            return fullFilePath
        except Exception as e:
            print('Error in function getDICOM_XMLFile: ' + str(e))


    def makeDICOM_XML_File(self):
        try:
            scan_directory = self.getScanDirectory()
            if scan_directory:
                number_files, number_folders = WriteXMLfromDICOM.get_files_info(scan_directory)
                scans, paths = WriteXMLfromDICOM.get_scan_data(scan_directory)
                dictionary = WriteXMLfromDICOM.get_studies_series(scans)
                xml = WriteXMLfromDICOM.open_dicom_to_xml(dictionary, scans, paths)
                fullFilePath = WriteXMLfromDICOM.create_XML_file(xml, scan_directory)
            return fullFilePath
        except Exception as e:
            print('Error in function makeDICOM_XML_File: ' + str(e))
    

    def loadDICOM_Data_From_DICOM_Folder(self):
        try:
            QApplication.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))
            XML_File_Path = self.makeDICOM_XML_File()
            self.makeDICOMStudiesTreeView(XML_File_Path)
            QApplication.restoreOverrideCursor()
        except Exception as e:
            QApplication.restoreOverrideCursor()
            print('Error in function loadDICOM_Data_From_DICOM_Folder: ' + str(e))


    def loadDICOM_Data_From_DICOM_XML_File(self):
        try:
            QApplication.setOverrideCursor(QCursor(QtCore.Qt.WaitCursor))
            XML_File_Path = self.getDICOM_XMLFile()
            self.makeDICOMStudiesTreeView(XML_File_Path)
            QApplication.restoreOverrideCursor()
        except Exception as e:
            QApplication.restoreOverrideCursor()
            print('Error in function loadDICOM_Data_From_DICOM_File: ' + str(e))


    def makeDICOMStudiesTreeView(self, XML_File_Path):
        """Uses an XML file that describes a DICOM file structure to build a
        tree view showing a visual representation of that file structure."""
        try:
            if os.path.exists(XML_File_Path):
                self.DICOM_XML_FilePath = XML_File_Path
                self.DICOMfolderPath, _ = os.path.split(XML_File_Path)
                #print(self.DICOMfolderPath)
                self.XMLtree = ET.parse(XML_File_Path)
                self.root = self.XMLtree.getroot()

                self.treeView = QTreeWidget()
                self.treeView.setColumnCount(3)
                self.treeView.setHeaderLabels(["DICOM Files", "Date", "Time"])
                
                # Uncomment to test XML file loaded OK
                #print(ET.tostring(self.root, encoding='utf8').decode('utf8'))
                studies = self.root.findall('./study')
                for study in studies:
                    studyID = study.attrib['id']
                    studyBranch = QTreeWidgetItem(self.treeView)
                    studyBranch.setText(0, "Study {}".format(studyID))
                    studyBranch.setFlags(studyBranch.flags() & ~Qt.ItemIsSelectable)
                    studyBranch.setExpanded(True)
                    for series in study:
                        seriesID = series.attrib['id']
                        seriesBranch = QTreeWidgetItem(studyBranch)
                        #seriesBranch.setFlags(seriesBranch.flags() | Qt.ItemIsUserCheckable)
                        seriesBranch.setText(0, "Series {}".format(seriesID))
                        seriesBranch.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                        #Expand this series branch, so that the 3 resizeColumnToContents
                        #commands can work
                        seriesBranch.setExpanded(True)
                        for image in series:
                            #Extract filename from file path
                            imageName = os.path.basename(image.find('name').text)
                            imageDate = image.find('date').text
                            imageTime = image.find('time').text
                            imageLeaf = QTreeWidgetItem(seriesBranch)
                            #imageLeaf.setText(0, 'Image ')
                            imageLeaf.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                            #Uncomment the next 2 lines to put a checkbox in front of each image
                            #imageLeaf.setFlags(imageLeaf.flags() | Qt.ItemIsUserCheckable)
                            #imageLeaf.setCheckState(0, Qt.Unchecked)
                            imageLeaf.setText(0, 'Image - ' + imageName)
                            imageLeaf.setText(1, imageDate)
                            imageLeaf.setText(2, imageTime)
                            self.treeView.resizeColumnToContents(0)
                            self.treeView.resizeColumnToContents(1)
                            self.treeView.resizeColumnToContents(2)
                        #Now collapse the series branch so as to hide the images
                        seriesBranch.setExpanded(False)
                        
                self.treeView.itemSelectionChanged.connect(self.toggleToolButtons)
                self.treeView.itemDoubleClicked.connect(self.viewImage)
                self.treeView.show()
        
                widget = QWidget()
                widget.setLayout(QVBoxLayout()) 
                widget.layout().addWidget(self.treeView)
        
                subWindow = QMdiSubWindow(self)
                subWindow.setWidget(widget)
                subWindow.setObjectName("New_Window")
                subWindow.setWindowTitle("DICOM Study Structure")
                subWindow.setGeometry(0,0,800,1300)
                self.mdiArea.addSubWindow(subWindow)
                subWindow.show()
        except Exception as e:
            print('Error in makeDICOMStudiesTreeView: ' + str(e))


    def closeAllSubWindows(self):
        self.mdiArea.closeAllSubWindows()
        self.treeView = None

    def displayImageSubWindow(self, pixelArray):
        """
        Creates a subwindow that displays the DICOM image contained in pixelArray. 
        """
        try:
            subWindow = QMdiSubWindow(self)
            subWindow.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
            imageViewer = pg.GraphicsLayoutWidget()
            subWindow.setWidget(imageViewer)
            viewBox = imageViewer.addViewBox()
            viewBox.setAspectLocked(True)
            img = pg.ImageItem(border='w')
            viewBox.addItem(img)
            img.setImage(pixelArray)   
            subWindow.setObjectName("Image_Window")
            windowTitle = self.getDICOMFileData()
            subWindow.setWindowTitle(windowTitle)
            subWindow.setGeometry(0,0,800,600)
            self.mdiArea.addSubWindow(subWindow)
            subWindow.show()
        except Exception as e:
            print('Error in displayImageSubWindow: ' + str(e))


    def displayMultiImageSubWindow(self, imageList, seriesName):
        """
        Creates a subwindow that displays all the DICOM images in a series. 
        """
        try:
            self.subWindow = QMdiSubWindow(self)
            self.subWindow.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
            layout = QVBoxLayout()
            imageViewer = pg.GraphicsLayoutWidget()
            widget = QWidget()
            widget.setLayout(layout)
            self.subWindow.setWidget(widget)
            layout.addWidget(imageViewer)
            viewBox = imageViewer.addViewBox()
            viewBox.setAspectLocked(True)
            self.img = pg.ImageItem(border='w')
            viewBox.addItem(self.img)

            self.imageSlider = QSlider(Qt.Horizontal)
            self.imageSlider.setMinimum(1)
            self.imageSlider.setMaximum(len(imageList))
            self.imageSlider.setValue(1)
            self.imageSlider.setSingleStep(1)
            self.imageSlider.setTickPosition(QSlider.TicksBothSides)
            self.imageSlider.setTickInterval(1)
            self.imageSlider.valueChanged.connect(
                  lambda: self.imageSliderChanged(seriesName, imageList))
            #print('Num of images = {}'.format(len(imageList)))
            layout.addWidget(self.imageSlider)
            #Display first image
            imagePath = self.DICOMfolderPath + "\\" + imageList[0]
            pixelArray = viewDICOM_Image.returnPixelArray(imagePath)
            self.img.setImage(pixelArray)   
            self.subWindow.setObjectName("MultiImage_Window")
            
            self.subWindow.setWindowTitle(seriesName + ' - ' + imageList[0])
            self.subWindow.setGeometry(0,0,800,600)
            self.mdiArea.addSubWindow(self.subWindow)
            self.subWindow.show()
        except Exception as e:
            print('Error in displayMultiImageSubWindow: ' + str(e))


    def imageSliderChanged(self, seriesName, imageList):
      try:
        imageNumber = self.imageSlider.value()
        imagePath = self.DICOMfolderPath + "\\" + imageList[imageNumber - 1]
        pixelArray = viewDICOM_Image.returnPixelArray(imagePath)
        self.img.setImage(pixelArray)  
        self.subWindow.setWindowTitle(seriesName + ' - ' + imageList[imageNumber - 1])
      except Exception as e:
            print('Error in imageSliderChanged: ' + str(e))


    def viewImage(self):
        """Creates a subwindow that displays a DICOM image. Either executed using the 
        'View Image' Menu item in the Tools menu or by double clicking the Image name 
        in the DICOM studies tree view."""
        try:
            if self.isImageSelected():
                imagePath = self.DICOMfolderPath + "\\" + self.getDICOMFileName()
                pixelArray = viewDICOM_Image.returnPixelArray(imagePath)
                self.displayImageSubWindow(pixelArray)
            elif self.isSeriesSelected():
                #Get Series ID & Study ID
                studyNumber, seriesNumber = \
                    self.getStudyAndSeriesNumbersFromSeries(self.treeView.selectedItems())
                seriesName = self.treeView.currentItem().text(0)
                #Get list of image names
                xPath = './study[@id=' + chr(34) + studyNumber + chr(34) + \
                ']/series[@id=' + chr(34) + seriesNumber + chr(34) + ']/image'
                #print(xPath)
                images = self.root.findall(xPath)
                imageList = [image.find('name').text for image in images] 
                self.displayMultiImageSubWindow(imageList, seriesName)
        except Exception as e:
            print('Error in viewImage: ' + str(e))


    def insertInvertedImageInXMLFile(self, selectedImage, invertedImageFileName):
        try:
            studyNumber, seriesNumber = self.getStudyAndSeriesNumbersForImage(selectedImage)
            #First determine if a series with parentID=seriesNumber exists
            xPath = './study[@id=' + chr(34) + studyNumber + chr(34) + \
                ']/series[@parentID=' + chr(34) + seriesNumber + chr(34) + ']'
            series = self.root.find(xPath)
            imageName = self.getDICOMFileName()
                    
            if series is None:
                #Need to create a new series to hold this inverted image
                #Get maximum series number in current study
                studyXPath ='./study[@id=' + chr(34) + studyNumber + chr(34) + ']/series[last()]'
                lastSeries = self.root.find(studyXPath)
                lastSeriesID = lastSeries.attrib['id']
                #print('series id = {}'. format(lastSeriesID))
                nextSeriesID = str(int(lastSeriesID) + 1)
                #Get study branch
                xPath = './study[@id=' + chr(34) + studyNumber + chr(34) + ']'
                currentStudy = self.root.find(xPath)
                newAttributes = {'id':nextSeriesID, 'parentID':seriesNumber}
                   
                #Add new series to study to hold inverted images
                newSeries = ET.SubElement(currentStudy, 'series', newAttributes)
                    
                comment = ET.Comment('This series holds inverted images')
                newSeries.append(comment)
                #Get image date & time
                imageTime, imageDate = self.getImageDateTime(imageName, studyNumber, seriesNumber)
                    
                #print("image time {}, date {}".format(imageTime, imageDate))
                #Now add image element
                newInvertedImage = ET.SubElement(newSeries,'image')
                #Add child nodes of the image element
                nameInvertedImage = ET.SubElement(newInvertedImage, 'name')
                nameInvertedImage.text = invertedImageFileName
                timeInvertedImage = ET.SubElement(newInvertedImage, 'time')
                timeInvertedImage.text = imageTime
                dateInvertedImage = ET.SubElement(newInvertedImage, 'date')
                dateInvertedImage.text = imageDate
                self.XMLtree.write(self.DICOM_XML_FilePath)
            else:
                #A series already exists to hold inverted images from
                #the current parent series
                imageTime, imageDate = self.getImageDateTime(imageName, studyNumber, seriesNumber)
                newInvertedImage = ET.SubElement(series,'image')
                #Add child nodes of the image element
                nameInvertedImage = ET.SubElement(newInvertedImage, 'name')
                nameInvertedImage.text = invertedImageFileName
                timeInvertedImage = ET.SubElement(newInvertedImage, 'time')
                timeInvertedImage.text = imageTime
                dateInvertedImage = ET.SubElement(newInvertedImage, 'date')
                dateInvertedImage.text = imageDate
                self.XMLtree.write(self.DICOM_XML_FilePath)
        except Exception as e:
            print('Error in insertInvertedImageInXMLFile: ' + str(e))
    

    def insertInvertedSeriesInXMLFile(self, origImageList, invertedImageList):
        """Creates a new series to hold the series of inverted images"""
        try:
            #Get current study & series IDs
            studyNumber, seriesNumber = \
                    self.getStudyAndSeriesNumbersFromSeries(self.treeView.selectedItems())
            #Need to create a new series to hold this series of inverted images 
            #Get maximum series number in current study
            studyXPath ='./study[@id=' + chr(34) + studyNumber + chr(34) + ']/series[last()]'
            lastSeries = self.root.find(studyXPath)
            lastSeriesID = lastSeries.attrib['id']
            #print('series id = {}'. format(lastSeriesID))
            nextSeriesID = str(int(lastSeriesID) + 1)
     
            #Get study branch
            xPath = './study[@id=' + chr(34) + studyNumber + chr(34) + ']'
            currentStudy = self.root.find(xPath)
            newAttributes = {'id':nextSeriesID, 'parentID':seriesNumber}
                   
            #Add new series to study to hold inverted images
            newSeries = ET.SubElement(currentStudy, 'series', newAttributes)
                    
            comment = ET.Comment('This series holds a whole series of inverted images')
            newSeries.append(comment)
            #Get image date & time from original image
            for index, image in enumerate(origImageList):
                imageTime, imageDate = self.getImageDateTime(image, studyNumber, seriesNumber)       
                newInvertedImage = ET.SubElement(newSeries,'image')
                #Add child nodes of the image element
                nameInvertedImage = ET.SubElement(newInvertedImage, 'name')
                nameInvertedImage.text = invertedImageList[index]
                timeInvertedImage = ET.SubElement(newInvertedImage, 'time')
                timeInvertedImage.text = imageTime
                dateInvertedImage = ET.SubElement(newInvertedImage, 'date')
                dateInvertedImage.text = imageDate

            self.XMLtree.write(self.DICOM_XML_FilePath)
            return 'series ' + nextSeriesID

        except Exception as e:
            print('Error in insertInvertedSeriesInXMLFile: ' + str(e))


    def invertImage(self):
        """Creates a subwindow that displays an inverted DICOM image. Executed using the 
        'Invert Image' Menu item in the Tools menu."""
        try:
            if self.isImageSelected():
                imagePath = self.DICOMfolderPath + "\\" + self.getDICOMFileName()
                pixelArray, invertedImageFileName = \
                    invertDICOM_Image.returnPixelArray(imagePath)
                self.displayImageSubWindow(pixelArray)

                #Record inverted image in XML file
                selectedImage = self.treeView.selectedItems()
                self.insertInvertedImageInXMLFile(selectedImage, invertedImageFileName)
                #Update tree view with xml file modified above
                self.refreshDICOMStudiesTreeView()
            elif self.isSeriesSelected():
                #Get Series ID & Study ID
                studyNumber, seriesNumber = \
                    self.getStudyAndSeriesNumbersFromSeries(self.treeView.selectedItems())
                seriesName = self.treeView.currentItem().text(0)
                #Get list of image names
                xPath = './study[@id=' + chr(34) + studyNumber + chr(34) + \
                ']/series[@id=' + chr(34) + seriesNumber + chr(34) + ']/image'
                #print(xPath)
                images = self.root.findall(xPath)
                imageList = [image.find('name').text for image in images] 
                #Iterate through list of images and invert each image
                invertedImageList = []
                for image in imageList:
                    imagePath = self.DICOMfolderPath + "\\" + image
                    _, invertedImageFileName = \
                    invertDICOM_Image.returnPixelArray(imagePath)
                    invertedImageList.append(invertedImageFileName)

                newSeriesName= self.insertInvertedSeriesInXMLFile(imageList, invertedImageList)
                self.displayMultiImageSubWindow(invertedImageList, newSeriesName)
                self.refreshDICOMStudiesTreeView()
        except Exception as e:
            print('Error in invertImage: ' + str(e))
    

    def deleteImage(self):
        """Creates a subwindow that displays an inverted DICOM image. Executed using the 
        'Invert Image' Menu item in the Tools menu."""
        try:
            if self.isImageSelected():
                imageName = self.getDICOMFileName()
                imagePath = self.DICOMfolderPath + "\\" + imageName
                buttonReply = QMessageBox.question(self, 
                  'Delete DICOM image', "You are about to delete image {}".format(imageName), 
                  QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                if buttonReply == QMessageBox.Ok:
                    #Delete physical file
                    os.remove(imagePath)
                    #Is this the last image in a series?
                    #It is the last image in a series so delete 
                    #whole series from XML file
                    #No it is not the last image in a series
                    #so just remove the image from the XML file
                    #Update tree view with xml file modified above
                    self.refreshDICOMStudiesTreeView()
            elif self.isSeriesSelected():
                seriesName = self.treeView.currentItem().text(0)
                buttonReply = QMessageBox.question(self, 
                  'Delete DICOM series', "You are about to delete series {}".format(seriesName), 
                  QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                if buttonReply == QMessageBox.Ok:
                    #Delete each physical file in the series
                    #Get list of image names
                    #Get Series ID & Study ID
                    studyNumber, seriesNumber = \
                    self.getStudyAndSeriesNumbersFromSeries(self.treeView.selectedItems())
                    xPath = './study[@id=' + chr(34) + studyNumber + chr(34) + \
                    ']/series[@id=' + chr(34) + seriesNumber + chr(34) + ']/image'
                    #print(xPath)
                    images = self.root.findall(xPath)
                    imageList = [image.find('name').text for image in images] 
                    #Iterate through list of images and delete each image
                    for image in imageList:
                        imagePath = self.DICOMfolderPath + "\\" + image
                        os.remove(imagePath)
                    #Remove the series from the XML file
                


                
                   

                
                self.refreshDICOMStudiesTreeView()
        except Exception as e:
            print('Error in deleteImage: ' + str(e))


    def getStudyAndSeriesNumbersForImage(self, selectedImage):
        """This function assumes a series name takes the
        form 'series' space number, where number is an integer
        with one or more digits; 
        e.g., 'series 44' and returns the number as a string.
        
        Same assumption is made for the study name."""
        try: 
            if selectedImage:
                #Extract series name from the selected image
                imageNode = selectedImage[0]
                seriesNode  = imageNode.parent()
                seriesName = seriesNode.text(0) 
                #Extract series number from the full series name
                numberList = re.findall(r'\d+', seriesName)
                seriesNumber = numberList[0]

                studyNode = seriesNode.parent()
                studyName = studyNode.text(0)
                #Extract study number from the full study name
                numberList = re.findall(r'\d+', studyName)
                studyNumber = numberList[0]
                return studyNumber, seriesNumber
            else:
                return None, None
        except Exception as e:
            print('Error in getStudyAndSeriesNumbersForImage: ' + str(e))


    def getStudyAndSeriesNumbersFromSeries(self, selectedSeries):
        """This function assumes a series name takes the
        form 'series' space number, where number is an integer
        with one or more digits; 
        e.g., 'series 44' and returns the number as a string.
        
        Same assumption is made for the study name."""
        try: 
            if selectedSeries:
                #Extract series name from the selected image
                seriesNode = selectedSeries[0]
                seriesName = seriesNode.text(0) 
                #Extract series number from the full series name
                numberList = re.findall(r'\d+', seriesName)
                seriesNumber = numberList[0]

                studyNode = seriesNode.parent()
                studyName = studyNode.text(0)
                #Extract study number from the full study name
                numberList = re.findall(r'\d+', studyName)
                studyNumber = numberList[0]
                return studyNumber, seriesNumber
            else:
                return None, None
        except Exception as e:
            print('Error in getStudyAndSeriesNumbersForImage: ' + str(e))


    def getImageDateTime(self, imageName, studyNumber, seriesNumber):
        try:
            #Get reference to image element time of the image
            xPath = './study[@id=' + chr(34) + studyNumber + chr(34) + \
                    ']/series[@id=' + chr(34) + seriesNumber + chr(34) + ']' + \
                    '/image[name=' + chr(34) + imageName + chr(34) +']/time'
            imageTime = self.root.find(xPath)
            
            xPath = './study[@id=' + chr(34) + studyNumber + chr(34) + \
                    ']/series[@id=' + chr(34) + seriesNumber + chr(34) + ']' + \
                    '/image[name=' + chr(34) + imageName + chr(34) +']/date'
            imageDate = self.root.find(xPath)

            return imageTime.text, imageDate.text           
        except Exception as e:
            print('Error in getImageDateTime: ' + str(e))


    def isImageSelected(self):
        try:
            selectedItem = self.treeView.currentItem()
            if 'image' in selectedItem.text(0).lower():
                return True
            else:
                return False
        except Exception as e:
            print('Error in isImageSelected: ' + str(e))
    

    def isSeriesSelected(self):
        try:
            selectedItem = self.treeView.currentItem()
            if 'series' in selectedItem.text(0).lower():
                return True
            else:
                return False
        except Exception as e:
            print('Error in isSeriesSelected: ' + str(e))


    def toggleToolButtons(self):
        try:
            if self.isImageSelected() or self.isSeriesSelected():
                self.viewImageButton.setEnabled(True)
                self.invertImageButton.setEnabled(True)
                self.deleteImageButton.setEnabled(True)
            else:
                self.viewImageButton.setEnabled(False)
                self.invertImageButton.setEnabled(False)
                self.deleteImageButton.setEnabled(False)
        except Exception as e:
            print('Error in toggleToolButtons: ' + str(e))


    def getDICOMFileData(self):
        """When a DICOM image is selected in the tree view, this function
        returns its description in the form - study number: series number: image name"""
        try:
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


    def getDICOMFileName(self):
        """Returns the name of a DICOM image file"""
        try:
            selectedImage = self.treeView.selectedItems()
            if selectedImage:
                imageNode = selectedImage[0]
                imageName = imageNode.text(0)
                imageName = imageName.replace('Image - ', '')
                imageName = imageName.strip()
                return imageName
        except Exception as e:
            print('Error in getDICOMFileName: ' + str(e))


    def refreshDICOMStudiesTreeView(self):
        """Uses an XML file that describes a DICOM file structure to build a
        tree view showing a visual representation of that file structure."""
        try:
            self.XMLtree = ET.parse(self.DICOM_XML_FilePath)
            self.root = self.XMLtree.getroot()
            self.treeView.clear()
            self.treeView.setColumnCount(3)
            self.treeView.setHeaderLabels(["DICOM Files", "Date", "Time"])
                
            # Uncomment to test XML file loaded OK
            #print(ET.tostring(self.root, encoding='utf8').decode('utf8'))
            studies = self.root.findall('./study')
            for study in studies:
                studyID = study.attrib['id']
                studyBranch = QTreeWidgetItem(self.treeView)
                studyBranch.setText(0, "Study {}".format(studyID))
                studyBranch.setFlags(studyBranch.flags() & ~Qt.ItemIsSelectable)
                studyBranch.setExpanded(True)
                for series in study:
                    seriesID = series.attrib['id']
                    seriesBranch = QTreeWidgetItem(studyBranch)
                    seriesBranch.setFlags(seriesBranch.flags() | Qt.ItemIsUserCheckable)
                    seriesBranch.setText(0, "Series {}".format(seriesID))
                    seriesBranch.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    seriesBranch.setExpanded(True)
                    for image in series:
                        imageName = image.find('name').text
                        imageDate = image.find('date').text
                        imageTime = image.find('time').text
                        imageLeaf = QTreeWidgetItem(seriesBranch)
                        imageLeaf.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                        imageLeaf.setFlags(imageLeaf.flags() | Qt.ItemIsUserCheckable)
                        #Uncomment the next line to put a checkbox in front of each image
                        #imageLeaf.setCheckState(0, Qt.Unchecked)
                        imageLeaf.setText(0, ' Image - ' +imageName)
                        imageLeaf.setText(1, imageDate)
                        imageLeaf.setText(2, imageTime)
                        imageLeaf.setExpanded(True)

            self.treeView.resizeColumnToContents(0)
            self.treeView.resizeColumnToContents(1)
            self.treeView.resizeColumnToContents(2)
            
            self.treeView.show()
        except Exception as e:
            print('Error in refreshDICOMStudiesTreeView: ' + str(e))


def main():
    app = QApplication([])
    winMDI = MainWindow()
    winMDI.show()
    sys.exit(app.exec())

if __name__ == '__main__':
        main()