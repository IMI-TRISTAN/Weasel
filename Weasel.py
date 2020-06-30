
from PyQt5 import QtCore 
from PyQt5.QtCore import  Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import (QAction, QApplication, QFileDialog,                            
        QMdiArea, QMessageBox, QWidget, QGridLayout, QVBoxLayout, QSpinBox,
        QMdiSubWindow, QGroupBox, QMainWindow, QHBoxLayout, QDoubleSpinBox,
        QPushButton, QStatusBar, QLabel, QAbstractSlider, QHeaderView,
        QTreeWidgetItem, QGridLayout, QSlider, QCheckBox, QLayout, 
        QProgressBar, QComboBox, QTableWidget, QTableWidgetItem, QFrame)
from PyQt5.QtGui import QCursor, QIcon, QColor

#import pyqtgraph as pg import statement for pip installed version of pyqtGraph
import os
import sys
import time
import re
import struct
import numpy as np
import math
import scipy
from scipy.stats import iqr
import logging
import pathlib
import importlib
import matplotlib.pyplot as plt
from matplotlib import cm


#Add folders CoreModules  Developer/ModelLibrary to the Module Search Path. 
#path[0] is the current working directory
#pathlib.Path().absolute() is the current directory where the script is located. 
#It doesn't matter if it's Python SYS or Windows SYS
sys.path.append(os.path.join(sys.path[0],'Developer//WEASEL//Tools//'))
sys.path.append(os.path.join(sys.path[0],
        'Developer//WEASEL//Tools//FERRET_Files//'))
sys.path.append(os.path.join(sys.path[0],'CoreModules'))
sys.path.append(os.path.join(sys.path[0],'CoreModules//WEASEL//'))
import CoreModules.readDICOM_Image as readDICOM_Image
import CoreModules.saveDICOM_Image as saveDICOM_Image

import Developer.WEASEL.Tools.binaryOperationDICOM_Image as binaryOperationDICOM_Image
import CoreModules.styleSheet as styleSheet
from Developer.WEASEL.Tools.FERRET import FERRET as ferret
from CoreModules.weaselXMLReader import WeaselXMLReader
import CoreModules.imagingTools as imagingTools
import CoreModules.WEASEL.TreeView  as treeView
import CoreModules.WEASEL.Menus  as menus
import CoreModules.WEASEL.ToolBar  as toolBar
import Developer.WEASEL.Tools
#access pyqtGraph from the source code imported into this project
import CoreModules.pyqtgraph as pg 

__version__ = '1.0'
__author__ = 'Steve Shillitoe'

listColours = ['gray', 'cividis',  'magma', 'plasma', 'viridis', 
                            'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
            'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
            'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn',
            'binary', 'gist_yarg', 'gist_gray', 'bone', 'pink',
            'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
            'hot', 'afmhot', 'gist_heat', 'copper',
            'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
            'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic',
            'twilight', 'twilight_shifted', 'hsv',
            'flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern',
            'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg',
            'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar', 'custom']

DEFAULT_IMAGE_FILE_PATH_NAME = 'C:\DICOM_Image.png'
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
        self.currentImagePath = ''
        self.statusBar = QStatusBar()
        self.centralwidget.layout().addWidget(self.statusBar)
        self.selectedStudy = ''
        self.selectedSeries = ''
        #self.selectedImagePath = ''
        self.selectedImageName = ''
        self.overRideSavedColourmapAndLevels = False #Set to True if the user checks the Apply Selection tick box
        self.applyUserSelection = False
        self.userSelectionList = []
        
         # XML reader object to process XML configuration file
        self.objXMLReader = WeaselXMLReader() 
        logger.info("WEASEL GUI created successfully.")

        menus.setupMenus(self)
        toolBar.setupToolBar(self)
        self.ApplyStyleSheet()

 
    def ApplyStyleSheet(self):
        """Modifies the appearance of the GUI using CSS instructions"""
        try:
            self.setStyleSheet(styleSheet.TRISTAN_GREY)
            logger.info('WEASEL Style Sheet applied.')
        except Exception as e:
            print('Error in function WEASEL.ApplyStyleSheet: ' + str(e))
  
            
    def getMDIAreaDimensions(self):
        return self.mdiArea.height(), self.mdiArea.width() 


    def closeAllSubWindows(self):
        """Closes all the sub windows open in the MDI"""
        logger.info("WEASEL closeAllSubWindows called")
        self.mdiArea.closeAllSubWindows()
        self.treeView = None    
    

    


    def setMsgWindowProgBarMaxValue(self, maxValue):
        self.progBarMsg.show()
        self.progBarMsg.setMaximum(maxValue)


    def setMsgWindowProgBarValue(self, value):
        self.progBarMsg.setValue(value)


    def closeMessageSubWindow(self):
        self.msgSubWindow.close()


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
            logger.error('Error in displayFERRET: ' + str(e)) 


    def blockHistogramSignals(self, imgView, block):
        histogramObject = imgView.getHistogramWidget().getHistogram()
        histogramObject.blockSignals(block)


    def setUpViewBoxForImage(self, imageViewer, layout, spinBoxCentre = None, spinBoxWidth = None):
        try:
            logger.info("WEASEL.setUpViewBoxForImage called")
            #viewBox = imageViewer.addViewBox()
            #viewBox.setAspectLocked(True)
            plotItem = imageViewer.addPlot() 
            plotItem.getViewBox().setAspectLocked() 
            img = pg.ImageItem(border='w')
            
            imv= pg.ImageView(view=plotItem, imageItem=img)
            if spinBoxCentre and spinBoxWidth:
                histogramObject = imv.getHistogramWidget().getHistogram()
                histogramObject.sigLevelsChanged.connect(lambda: self.getHistogramLevels(imv, spinBoxCentre, spinBoxWidth))
            imv.ui.roiBtn.hide()
            imv.ui.menuBtn.hide()
            layout.addWidget(imv)
 
            return img, imv, plotItem
        except Exception as e:
            print('Error in setUpViewBoxForImag: ' + str(e))
            logger.error('Error in setUpViewBoxForImag: ' + str(e))


    def getHistogramLevels(self, imv, spinBoxCentre, spinBoxWidth):
        minLevel, maxLevel = imv.getLevels()
        width = maxLevel - minLevel
        centre = minLevel + (width/2)
        #spinBoxCentre.blockSignals(True)
        #spinBoxWidth.blockSignals(True)
        spinBoxCentre.setValue(centre)
        spinBoxWidth.setValue(width)
        #spinBoxCentre.blockSignals(False)
       # spinBoxWidth.blockSignals(False)
        

    def updateDICOM(self, seriesIDLabel, studyIDLabel, cmbColours, spinBoxIntensity, spinBoxContrast):
        try:
            seriesID = seriesIDLabel.text()
            studyID = studyIDLabel.text()
            colourMap = cmbColours.currentText()
            if self.overRideSavedColourmapAndLevels:
                levels = [spinBoxIntensity.value(), spinBoxContrast.value()]
                saveDICOM_Image.updateDicomSeriesOneColour(self, seriesID, studyID, colourMap, levels)
            if self.applyUserSelection:
                saveDICOM_Image.updateDicomSeriesManyColours(self, seriesID, studyID, colourMap)
        except Exception as e:
            print('Error in Weasel.updateDICOM: ' + str(e))
            logger.error('Error in Weasel.updateDICOM: ' + str(e))


    def setPgColourMap(self, cm_name, imv, cmbColours=None, lut=None):
        try:
            if cm_name == None:
                cm_name = 'gray'

            if cmbColours:
                self.displayColourTableInComboBox(cmbColours, cm_name)   
        
            if cm_name == 'custom':
                colors = lut
            else:
                cmMap = cm.get_cmap(cm_name)
                colourClassName = cmMap.__class__.__name__
                if colourClassName == 'ListedColormap':
                    colors = cmMap.colors
                elif colourClassName == 'LinearSegmentedColormap':
                    numberOfValues = np.sqrt(len(imv.image.flatten()))
                    colors = cmMap(np.linspace(0, 1, numberOfValues))

            positions = np.linspace(0, 1, len(colors))
            pgMap = pg.ColorMap(positions, colors)
            imv.setColorMap(pgMap)        
        except Exception as e:
            print('Error in setPgColourMap: ' + str(e))
            logger.error('Error in setPgColourMap: ' + str(e))


    def applyColourTableAndLevelsToSeries(self, imv, cmbColours, chkBox=None): 
        try:
            colourTable = cmbColours.currentText()
            if colourTable == 'custom':
                colourTable = 'gray'                
                self.displayColourTableInComboBox(cmbColours, 'gray')   

            self.setPgColourMap(colourTable, imv)
            if chkBox.isChecked():
                self.overRideSavedColourmapAndLevels = True
                self.applyUserSelection = False
            else:
                self.overRideSavedColourmapAndLevels = False
                #self.applyUserSelection = True

        except Exception as e:
            print('Error in WEASEL.applyColourTableAndLevelsToSeries: ' + str(e))
            logger.error('Error in WEASEL.applyColourTableAndLevelsToSeries: ' + str(e))              
        

    def exportImage(self, imv, cmbColours):
        try:
            colourTable = cmbColours.currentText()
            imageName = os.path.basename(self.selectedImagePath) + '.png'
            fileName, _ = QFileDialog.getSaveFileName(caption="Enter a file name", 
                                                       directory=imageName, 
                                                       filter="*.png")
            minLevel, maxLevel = imv.getLevels()
            if fileName:
                self.exportImageViaMatplotlib(imv.getImageItem().image,
                                              fileName, 
                                              colourTable,
                                              minLevel,
                                              maxLevel)
        except Exception as e:
            print('Error in WEASEL.exportImage: ' + str(e))
            logger.error('Error in WEASEL.exportImage: ' + str(e))


    def exportImageViaMatplotlib(self, pixelArray, fileName, cm_name, minLevel, maxLevel):
        try:
            axisOrder = pg.getConfigOption('imageAxisOrder') 
            if axisOrder =='row-major':
                #rotate image 90 degree so as to match the screen image
                pixelArray = scipy.ndimage.rotate(pixelArray, 270)
            cmap = plt.get_cmap(cm_name)
            pos = plt.imshow(pixelArray,  cmap=cmap)
            plt.clim(int(minLevel), int(maxLevel))
            cBar = plt.colorbar()
            cBar.minorticks_on()
            plt.savefig(fname=fileName)
            plt.close()
            QMessageBox.information(self, "Export Image", "Image Saved")
        except Exception as e:
            print('Error in WEASEL.exportImageViaMatplotlib: ' + str(e))
            logger.error('Error in WEASEL.exportImageViaMatplotlib: ' + str(e))


    def clearUserSelection(self, imageSlider):
        self.applyUserSelection = False
        #reset list of image lists that hold user selected colour table, min and max levels
        for image in self.userSelectionList:
            image[1] = 'default'
            image[2] = -1
            image[3] = -1
         #reload current image to display it without user selected 
         #colour table and levels.
         #This is done by advancing the slider and then moving it i 
         #to the original image
        if imageSlider:
            imageNumber = imageSlider.value()
            if imageNumber == 1:
                tempNumber = imageNumber + 1
            else:
                tempNumber = imageNumber - 1

            imageSlider.setValue(tempNumber)
            imageSlider.setValue(imageNumber)
                    

    def changeSpinBoxLevels(self, imv, spinBoxIntensity, spinBoxContrast, chkBox=None):
        try:
            centre = spinBoxIntensity.value()
            width = spinBoxContrast.value()
            halfWidth = width/2

            minLevel = centre - halfWidth
            maxLevel = centre + halfWidth
            #print("centre{}, width{}, minLevel{}, maxLevel{}".format(centre, width, minLevel, maxLevel))
            imv.setLevels(minLevel, maxLevel)
            imv.show()

            if chkBox:
                if chkBox.isChecked() == False:
                    self.applyUserSelection = True
            
                    if self.selectedImagePath:
                        self.selectedImageName = os.path.basename(self.selectedImagePath)
                    else:
                        #Workaround for the fact that when the first image is displayed,
                        #somehow self.selectedImageName looses its value.
                        self.selectedImageName = os.path.basename(self.imageList[0])
                    
                    for imageNumber, image in enumerate(self.userSelectionList):
                        if image[0] == self.selectedImageName:
                            #Associate the levels with the image being viewed
                            self.userSelectionList[imageNumber][2] =  centre
                            self.userSelectionList[imageNumber][3] =  width
                            break
        except Exception as e:
            print('Error in WEASEL.changeSpinBoxLevels: ' + str(e))
            logger.error('Error in WEASEL.changeSpinBoxLevels: ' + str(e))


    def setUpColourTools(self, layout, imv,
            imageOnlySelected,
            lblHiddenImagePath,
            lblHiddenSeriesID,
            lblHiddenStudyID, spinBoxIntensity, spinBoxContrast,             
            imageSlider = None, showReleaseButton = False):
        try:
            groupBoxColour = QGroupBox('Colour Table')
            groupBoxLevels = QGroupBox('Levels')
            gridLayoutColour = QGridLayout()
            levelsLayout = QGridLayout()
            groupBoxColour.setLayout(gridLayoutColour)
            groupBoxLevels.setLayout(levelsLayout)
            layout.addWidget(groupBoxColour)

            chkApply = QCheckBox("Apply Selection to whole series")
            chkApply.stateChanged.connect(lambda:self.applyColourTableAndLevelsToSeries(imv, 
                                                                                        cmbColours, 
                                                                                        chkApply))
            chkApply.setToolTip(
                    "Tick to apply colour table and levels selected by the user to the whole series")

            cmbColours = QComboBox()
            cmbColours.setToolTip('Select a colour table to apply to the image')
            cmbColours.blockSignals(True)
            cmbColours.addItems(listColours)
            cmbColours.setCurrentIndex(0)
            cmbColours.blockSignals(False)
            cmbColours.currentIndexChanged.connect(lambda:
                      self.applyColourTableAndLevelsToSeries(imv, cmbColours, chkApply))

            btnUpdate = QPushButton('Update') 
            btnUpdate.setToolTip('Update DICOM with the new colour table')

            if imageOnlySelected:
                #only a single image is being viewed
                 btnUpdate.clicked.connect(lambda:saveDICOM_Image.updateSingleDicomImage
                                          (self, 
                                           spinBoxIntensity, spinBoxContrast,
                                           lblHiddenImagePath.text(),
                                                 lblHiddenSeriesID.text(),
                                                 lblHiddenStudyID.text(),
                                                 cmbColours.currentText(),
                                                 lut=None))
            else:
                btnUpdate.clicked.connect(lambda:self.updateDICOM(lblHiddenSeriesID,lblHiddenStudyID,cmbColours,
                                                                  spinBoxIntensity, spinBoxContrast))
            
  
            btnExport = QPushButton('Export') 
            btnExport.setToolTip('Exports the image to an external graphic file.')
            btnExport.clicked.connect(lambda:self.exportImage(imv, cmbColours))

            #Levels 
            lblIntensity = QLabel("Centre (Intensity)")
            lblContrast = QLabel("Width (Contrast)")
            lblIntensity.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            lblContrast.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            
            spinBoxIntensity.setMinimum(-100000.00)
            spinBoxContrast.setMinimum(-100000.00)
            spinBoxIntensity.setMaximum(100000.00)
            spinBoxContrast.setMaximum(100000.00)
            spinBoxIntensity.setWrapping(True)
            spinBoxContrast.setWrapping(True)

            if imageOnlySelected:
                spinBoxIntensity.valueChanged.connect(lambda: self.changeSpinBoxLevels(
                imv,spinBoxIntensity, spinBoxContrast))
                spinBoxContrast.valueChanged.connect(lambda: self.changeSpinBoxLevels(
                imv,spinBoxIntensity, spinBoxContrast))
            else:
                spinBoxIntensity.valueChanged.connect(lambda: self.changeSpinBoxLevels(
                    imv,spinBoxIntensity, spinBoxContrast, chkApply))
                spinBoxContrast.valueChanged.connect(lambda: self.changeSpinBoxLevels(
                    imv,spinBoxIntensity, spinBoxContrast, chkApply ))

            levelsLayout.addWidget(lblIntensity, 0,0)
            levelsLayout.addWidget(spinBoxIntensity, 0, 1)
            levelsLayout.addWidget(lblContrast, 0,2)
            levelsLayout.addWidget(spinBoxContrast, 0,3)
            gridLayoutColour.addWidget(cmbColours,0,0)

            if showReleaseButton:
                gridLayoutColour.addWidget(chkApply,0,1)
                btnReset = QPushButton('Reset') 
                btnReset.setToolTip('Return to colour tables and levels in the DICOM file')
                btnReset.clicked.connect(lambda: self.clearUserSelection(imageSlider))
                gridLayoutColour.addWidget(btnReset,0,2)
                gridLayoutColour.addWidget(btnUpdate,1,1)
                gridLayoutColour.addWidget(btnExport,1,2)
                gridLayoutColour.addWidget(groupBoxLevels, 2, 0, 1, 3)
                cmbColours.activated.connect(lambda:
                      self.updateUserSelectedColourTable(cmbColours, chkApply, spinBoxIntensity, spinBoxContrast))
            else:
                gridLayoutColour.addWidget(btnUpdate,0,1)
                gridLayoutColour.addWidget(btnExport,0,2)
                gridLayoutColour.addWidget(groupBoxLevels, 1, 0, 1, 3)

            return cmbColours
        except Exception as e:
            print('Error in WEASEL.setUpColourTools: ' + str(e))
            logger.error('Error in WEASEL.setUpColourTools: ' + str(e))


    def setUpLabels(self, layout):
        logger.info("WEASEL.setUpLabels called")
        gridLayout = QGridLayout()
        layout.addLayout(gridLayout)
       
        lblROIMeanValue = QLabel("<h4>ROI Mean Value:</h4>")
        lblROIMeanValue.show()
        gridLayout.addWidget(lblROIMeanValue, 0, 0)
        
        lblPixelValue = QLabel("<h4>Pixel Value:</h4>")
        lblPixelValue.show()
        gridLayout.addWidget(lblPixelValue, 0, 1)
        return lblPixelValue, lblROIMeanValue


    def setUpROITools(self, viewBox, layout, img, lblROIMeanValue):
        try:
            groupBoxROI = QGroupBox('ROI')
            gridLayoutROI = QGridLayout()
            groupBoxROI.setLayout(gridLayoutROI)
            layout.addWidget(groupBoxROI)

            btnCircleROI = QPushButton('Circle') 
            btnCircleROI.setToolTip('Creates/Resets a circular ROI')
            btnCircleROI.clicked.connect(lambda: 
                   self.createCircleROI(viewBox, img, lblROIMeanValue))
        
            btnEllipseROI = QPushButton('Ellipse') 
            btnEllipseROI.setToolTip('Creates/Resets an ellipical ROI')
            btnEllipseROI.clicked.connect(lambda: 
                   self.createEllipseROI(viewBox, img, lblROIMeanValue))

            btnMultiRectROI = QPushButton('Multi-Rect') 
            btnMultiRectROI.setToolTip(
                'Creates/Resets a chain of rectangular ROIs connected by handles')
            btnMultiRectROI.clicked.connect(lambda: 
                   self.createMultiRectROI(viewBox, img, lblROIMeanValue))

            btnPolyLineROI = QPushButton('PolyLine')
            btnPolyLineROI.setToolTip(
                'Allows the user to draw paths of multiple line segments')
            btnPolyLineROI.clicked.connect(lambda: 
                   self.createPolyLineROI(viewBox, img, lblROIMeanValue))

            btnRectROI = QPushButton('Rectangle') 
            btnRectROI.setToolTip('Creates/Resets a rectangular ROI')
            btnRectROI.clicked.connect(lambda: 
                   self.createRectangleROI(viewBox, img, lblROIMeanValue))

            #btnDrawROI = QPushButton('Draw') 
            #btnDrawROI.setToolTip('Allows the user to draw around a ROI')

            btnRemoveROI = QPushButton('Clear')
            btnRemoveROI.setToolTip('Clears the ROI from the image')
            btnRemoveROI.clicked.connect(lambda: self.removeROI(viewBox, 
                                                       lblROIMeanValue))

            btnSaveROI = QPushButton('Save')
            btnSaveROI.setToolTip('Saves the ROI in DICOM format')
            #btnSaveROI.clicked.connect(lambda: self.resetROI(viewBox))

            gridLayoutROI.addWidget(btnCircleROI,0,0)
            gridLayoutROI.addWidget(btnEllipseROI,0,1)
            gridLayoutROI.addWidget(btnMultiRectROI,0,2)
            gridLayoutROI.addWidget(btnPolyLineROI,0,3)
            gridLayoutROI.addWidget(btnRectROI,1,0)
            #gridLayoutROI.addWidget(btnDrawROI,1,1)
            gridLayoutROI.addWidget(btnRemoveROI,1,1)
            gridLayoutROI.addWidget(btnSaveROI,1,2)
        except Exception as e:
            print('Error in setUpROITools: ' + str(e))
            logger.error('Error in setUpROITools: ' + str(e))


    def addROIToViewBox(self, objROI, viewBox, img, lblROIMeanValue):
        try:
            logger.info("WEASEL.addROIToViewBox called")
            viewBox.addItem(objROI)
            objROI.sigRegionChanged.connect(
                lambda: self.updateROIMeanValue(objROI, 
                                               img.image, 
                                               img, 
                                               lblROIMeanValue))
        except Exception as e:
            print('Error in addROIToViewBox: ' + str(e))
            logger.error('Error in addROIToViewBox: ' + str(e))


    def createMultiRectROI(self, viewBox, img, lblROIMeanValue):
        try:
            logger.info("WEASEL.createMultiRectROI called")
            #Remove existing ROI if there is one
            self.removeROI(viewBox, lblROIMeanValue)
            objROI = pg.MultiRectROI([[20, 90], [50, 60], [60, 90]],
                                 pen=pg.mkPen(pg.mkColor('r'),
                                           width=5,
                                          style=QtCore.Qt.SolidLine), 
                                 width=5,
                               removable=True)
            self.addROIToViewBox(objROI, viewBox, img, lblROIMeanValue)
        except Exception as e:
            print('Error in createMultiRectROI: ' + str(e))
            logger.error('Error in createMultiRectROI: ' + str(e))


    def createPolyLineROI(self, viewBox, img, lblROIMeanValue):
        try:
            logger.info("WEASEL.createPolyLineROI called")
            #Remove existing ROI if there is one
            self.removeROI(viewBox, lblROIMeanValue)
            objROI = pg.PolyLineROI([[80, 60], [90, 30], [60, 40]],
                                 pen=pg.mkPen(pg.mkColor('r'),
                                           width=5,
                                          style=QtCore.Qt.SolidLine), 
                                 closed=True,
                                 removable=True)
            self.addROIToViewBox(objROI, viewBox, img, lblROIMeanValue)
        except Exception as e:
            print('Error in createPolyLineROI: ' + str(e))
            logger.error('Error in createPolyLineROI: ' + str(e))


    def createRectangleROI(self, viewBox, img, lblROIMeanValue):
        try:
            logger.info("WEASEL.createRectangleROI called")
            #Remove existing ROI if there is one
            self.removeROI(viewBox, lblROIMeanValue)
            objROI = pg.RectROI(
                                [20, 20], 
                                [20, 20],
                                 pen=pg.mkPen(pg.mkColor('r'),
                                           width=4,
                                          style=QtCore.Qt.SolidLine), 
                               removable=True)
            self.addROIToViewBox(objROI, viewBox, img, lblROIMeanValue)
        except Exception as e:
            print('Error in createRectangleRO: ' + str(e))
            logger.error('Error in createRectangleRO: ' + str(e))


    def createCircleROI(self, viewBox, img, lblROIMeanValue):
        try:
            logger.info("WEASEL.createCircleROI called")
            #Remove existing ROI if there is one
            self.removeROI(viewBox, lblROIMeanValue)
            objROI = pg.CircleROI([20, 20], 
                                  [20, 20],  
                                  pen=pg.mkPen(pg.mkColor('r'),
                                           width=4,
                                          style=QtCore.Qt.SolidLine),
                                  removable=True)
            self.addROIToViewBox(objROI, viewBox, img, lblROIMeanValue)
        except Exception as e:
            print('Error in createCircleROI: ' + str(e))
            logger.error('Error in createCircleROI: ' + str(e))


    def createEllipseROI(self, viewBox, img, lblROIMeanValue):
        try:
            logger.info("WEASEL.createEllipseROI called")
            #Remove existing ROI if there is one
            self.removeROI(viewBox, lblROIMeanValue)
            objROI = pg.EllipseROI(
                                [20, 20], 
                                [30, 20], 
                                pen=pg.mkPen(pg.mkColor('r'),
                                           width=4,
                                          style=QtCore.Qt.SolidLine),
                                removable=True)
            self.addROIToViewBox(objROI, viewBox, img, lblROIMeanValue)
        except Exception as e:
            print('Error in createEllipseROI: ' + str(e))
            logger.error('Error in createEllipseROI: ' + str(e))


    def getROIOject(self, viewBox):
        try:
            logger.info("WEASEL.getROIOject called")
            for item in viewBox.items:
                if 'graphicsItems.ROI' in str(type(item)):
                    return item
                    break
        except Exception as e:
            print('Error in getROIOject: ' + str(e))
            logger.error('Error in getROIOject: ' + str(e))
        
        
    def removeROI(self, viewBox, lblROIMeanValue):
        try:
            logger.info("WEASEL.removeROI called")
            objROI = self.getROIOject(viewBox)
            viewBox.removeItem(objROI) 
            lblROIMeanValue.setText("<h4>ROI Mean Value:</h4>")
        except Exception as e:
            print('Error in removeROI: ' + str(e))
            logger.error('Error in removeROI: ' + str(e))           


    def displayPixelArray(self, pixelArray, currentImageNumber,
                          lblImageMissing, lblPixelValue,
                          spinBoxIntensity, spinBoxContrast,
                          imv, colourTable, cmbColours, lut=None,
                          multiImage=False, deleteButton=None):
        try:
            logger.info("displayPixelArray called")
            if deleteButton is None:
                #create dummy button to prevent runtime error
                deleteButton = QPushButton()
                deleteButton.hide()

            #Check that pixel array holds an image & display it
            if pixelArray is None:
                lblImageMissing.show()
                if multiImage:
                    deleteButton.hide()
                imv.setImage(np.array([[0,0,0],[0,0,0]]))  
            else:
                if self.overRideSavedColourmapAndLevels:
                    centre = spinBoxIntensity.value()
                    width = spinBoxContrast.value()
                    minimumValue = centre - (width/2)
                    maximumValue = centre + (width/2)
                elif self.applyUserSelection:
                    _, centre, width = self.returnUserSelection(currentImageNumber) 
                    if centre != -1:
                        minimumValue = centre - (width/2)
                        maximumValue = centre + (width/2)
                    else:
                        try:
                            dataset = readDICOM_Image.getDicomDataset(self.selectedImagePath)
                            slope = float(getattr(dataset, 'RescaleSlope', 1))
                            intercept = float(getattr(dataset, 'RescaleIntercept', 0))
                            centre = dataset.WindowCenter * slope + intercept
                            width = dataset.WindowWidth * slope
                            minimumValue = centre - width/2
                        except:
                            minimumValue = np.amin(pixelArray) if (np.median(pixelArray) - iqr(pixelArray, rng=(
                            1, 99))/2) < np.amin(pixelArray) else np.median(pixelArray) - iqr(pixelArray, rng=(1, 99))/2
                            centre = spinBoxIntensity.value()
                            width = spinBoxContrast.value()
       
                        try:
                            dataset = readDICOM_Image.getDicomDataset(self.selectedImagePath)
                            slope = float(getattr(dataset, 'RescaleSlope', 1))
                            intercept = float(getattr(dataset, 'RescaleIntercept', 0))
                            centre = dataset.WindowCenter * slope + intercept
                            width = dataset.WindowWidth * slope
                            maximumValue = centre + width/2
                        except:
                            maximumValue = np.amax(pixelArray) if (np.median(pixelArray) + iqr(pixelArray, rng=(
                            1, 99))/2) > np.amax(pixelArray) else np.median(pixelArray) + iqr(pixelArray, rng=(1, 99))/2
                            centre = spinBoxIntensity.value()
                            width = spinBoxContrast.value()
                else:
                    try:
                        dataset = readDICOM_Image.getDicomDataset(self.selectedImagePath)
                        slope = float(getattr(dataset, 'RescaleSlope', 1))
                        intercept = float(getattr(dataset, 'RescaleIntercept', 0))
                        centre = dataset.WindowCenter * slope + intercept
                        width = dataset.WindowWidth * slope
                        maximumValue = centre + width/2
                        minimumValue = centre - width/2
                    except:
                        minimumValue = np.amin(pixelArray) if (np.median(pixelArray) - iqr(pixelArray, rng=(
                        1, 99))/2) < np.amin(pixelArray) else np.median(pixelArray) - iqr(pixelArray, rng=(1, 99))/2
                        maximumValue = np.amax(pixelArray) if (np.median(pixelArray) + iqr(pixelArray, rng=(
                        1, 99))/2) > np.amax(pixelArray) else np.median(pixelArray) + iqr(pixelArray, rng=(1, 99))/2
                        centre = minimumValue + (abs(maximumValue) - abs(minimumValue))/2
                        width = maximumValue - abs(minimumValue)

                spinBoxIntensity.setValue(centre)
                spinBoxContrast.setValue(width)
                self.blockHistogramSignals(imv, True)
                imv.setImage(pixelArray, autoHistogramRange=True, levels=(minimumValue, maximumValue))
                self.blockHistogramSignals(imv, False)
        
                #Add Colour Table or look up table To Image
                self.setPgColourMap(colourTable, imv, cmbColours, lut)

                lblImageMissing.hide()   
  
                imv.getView().scene().sigMouseMoved.connect(
                   lambda pos: self.getPixelValue(pos, imv, pixelArray, lblPixelValue))

                if multiImage:
                    deleteButton.show()
        except Exception as e:
            print('Error in displayPixelArray: ' + str(e))
            logger.error('Error in displayPixelArray: ' + str(e)) 


    def displayROIPixelArray(self, pixelArray, currentImageNumber,
                          lblImageMissing, lblPixelValue, colourTable,
                          imv):
        try:
            logger.info("displayROIPixelArray called")

            #Check that pixel array holds an image & display it
            if pixelArray is None:
                lblImageMissing.show()
                imv.setImage(np.array([[0,0,0],[0,0,0]]))  
            else:
                try:
                    dataset = readDICOM_Image.getDicomDataset(self.selectedImagePath)
                    slope = float(getattr(dataset, 'RescaleSlope', 1))
                    intercept = float(getattr(dataset, 'RescaleIntercept', 0))
                    centre = dataset.WindowCenter * slope + intercept
                    width = dataset.WindowWidth * slope
                    maximumValue = centre + width/2
                    minimumValue = centre - width/2
                except:
                    minimumValue = np.amin(pixelArray) if (np.median(pixelArray) - iqr(pixelArray, rng=(
                    1, 99))/2) < np.amin(pixelArray) else np.median(pixelArray) - iqr(pixelArray, rng=(1, 99))/2
                    maximumValue = np.amax(pixelArray) if (np.median(pixelArray) + iqr(pixelArray, rng=(
                    1, 99))/2) > np.amax(pixelArray) else np.median(pixelArray) + iqr(pixelArray, rng=(1, 99))/2

                
                imv.setImage(pixelArray, autoHistogramRange=True, levels=(minimumValue, maximumValue))
                self.setPgColourMap(colourTable, imv)
                lblImageMissing.hide()   
  
                imv.getView().scene().sigMouseMoved.connect(
                   lambda pos: self.getPixelValue(pos, imv, pixelArray, lblPixelValue))

        except Exception as e:
            print('Error in displayROIPixelArray: ' + str(e))
            logger.error('Error in displayROIPixelArray: ' + str(e)) 


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
            if roi is not None:
                arrRegion = roi.getArrayRegion(pixelArray, imgItem, 
                                axes=(1,0))
                #, returnMappedCoords=True
                #print('Mouse move')
                #print(arrRegion)
                #roiMean = round(np.mean(arrRegion[0]), 3)
                roiMean = round(np.mean(arrRegion), 3)
                lbl.setText("<h4>ROI Mean Value = {}</h4>".format(str(roiMean)))
                if len(arrRegion[0]) <4:
                    print(arrRegion[0])
                    print ('Coords={}'.format(arrRegion[1]))

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
        subWindow.setGeometry(0,0,width*0.6,height)
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


    def updateUserSelectedColourTable(self, cmbColours, chkBox, spinBoxIntensity, spinBoxContrast):
        if chkBox.isChecked() == False:
            self.applyUserSelection = True
            colourTable = cmbColours.currentText()
            #print(self.userSelectionList)
            if self.selectedImagePath:
                self.selectedImageName = os.path.basename(self.selectedImagePath)
            else:
                #Workaround for the fact that when the first image is displayed,
                #somehow self.selectedImageName looses its value.
                self.selectedImageName = os.path.basename(self.imageList[0])
            #print("self.selectedImageName={}".format(self.selectedImageName))
            imageNumber = -1
            for imageNumber, image in enumerate(self.userSelectionList):
                if image[0] == self.selectedImageName:
                    break
        
            #Associate the selected colour table, contrast & intensity with the image being viewed
            self.userSelectionList[imageNumber][1] =  colourTable
            #self.userSelectionList[imageNumber][2] =  spinBoxIntensity.value()
            #self.userSelectionList[imageNumber][3] =  spinBoxContrast.value()


    def returnImageNumber(self):
        imageNumber = -1
        for count, image in enumerate(self.userSelectionList, 0):
            if image[0] == self.selectedImageName:
                imageNumber = count
                break
        return imageNumber


    def updateUserSelectedLevels(self, spinBoxIntensity, spinBoxContrast):
        if self.applyUserSelection:
            imageNumber = self.returnImageNumber()
            if imageNumber != -1:
                self.userSelectionList[imageNumber][2] =  spinBoxIntensity.value()
                self.userSelectionList[imageNumber][3] =  spinBoxContrast.value()


    def returnUserSelection(self, imageNumber):
        colourTable = self.userSelectionList[imageNumber][1] 
        intensity = self.userSelectionList[imageNumber][2]
        contrast = self.userSelectionList[imageNumber][3] 
        return colourTable, intensity, contrast


    def displayImageSubWindow(self, derivedImagePath=None):
        """
        Creates a subwindow that displays the DICOM image contained in pixelArray. 
        """
        try:
            logger.info("WEASEL displayImageSubWindow called")
            pixelArray = readDICOM_Image.returnPixelArray(self.selectedImagePath)
            colourTable, lut = readDICOM_Image.getColourmap(self.selectedImagePath)
            imageViewer, layout, lblImageMissing, subWindow = \
                self.setUpImageViewerSubWindow()
            windowTitle = self.getDICOMFileData()
            subWindow.setWindowTitle(windowTitle)

            if derivedImagePath:
                lblHiddenImagePath = QLabel(derivedImagePath)
            else:
                lblHiddenImagePath = QLabel(self.selectedImagePath)
            lblHiddenImagePath.hide()
            lblHiddenStudyID = QLabel()
            lblHiddenStudyID.hide()
            lblHiddenSeriesID = QLabel()
            lblHiddenSeriesID.hide()
            
            layout.addWidget(lblHiddenSeriesID)
            layout.addWidget(lblHiddenStudyID)
            layout.addWidget(lblHiddenImagePath)

            spinBoxIntensity = QDoubleSpinBox()
            spinBoxContrast = QDoubleSpinBox()
            img, imv, viewBox = self.setUpViewBoxForImage(imageViewer, layout, spinBoxIntensity, spinBoxContrast)

            lblPixelValue = QLabel("<h4>Pixel Value:</h4>")
            lblPixelValue.show()
            layout.addWidget(lblPixelValue)
            
            cmbColours = self.setUpColourTools(layout, imv, True,  
                                                lblHiddenImagePath, lblHiddenSeriesID, lblHiddenStudyID, 
                                                spinBoxIntensity, spinBoxContrast)
            
            self.displayColourTableInComboBox(cmbColours, colourTable)
            self.displayPixelArray(pixelArray, 0,
                                    lblImageMissing,
                                    lblPixelValue,
                                    spinBoxIntensity, spinBoxContrast,
                                    imv, colourTable,
                                    cmbColours, lut)  
        except Exception as e:
            print('Error in Weasel.displayImageSubWindow: ' + str(e))
            logger.error('Error in Weasel.displayImageSubWindow: ' + str(e)) 


    def displayMultiImageSubWindow(self, imageList, studyName, 
                     seriesName, sliderPosition = -1):
        """
        Creates a subwindow that displays all the DICOM images in a series. 
        A slider allows the user to navigate  through the images.  A delete
        button allows the user to delete the image they are viewing.
        """
        try:
            logger.info("WEASEL displayMultiImageSubWindow called")
            self.overRideSavedColourmapAndLevels = False
            self.applyUserSelection = False
            imageViewer, layout, lblImageMissing, subWindow = \
                self.setUpImageViewerSubWindow()

            #set up list of lists to hold user selected colour table and level data
            self.userSelectionList = [[os.path.basename(imageName), 'default', -1, -1]
                                for imageName in imageList]
            
            
            #Study ID & Series ID are stored locally on the
            #sub window in case the user wishes to delete an
            #image in the series.  They may have several series
            #open at once, so the selected series on the treeview
            #may not the same as that from which the image is
            #being deleted.

            lblHiddenImagePath = QLabel('')
            lblHiddenImagePath.hide()
            lblHiddenStudyID = QLabel(studyName)
            lblHiddenStudyID.hide()
            lblHiddenSeriesID = QLabel(seriesName)
            lblHiddenSeriesID.hide()
            btnDeleteDICOMFile = QPushButton('Delete DICOM Image')
            btnDeleteDICOMFile.setToolTip(
            'Deletes the DICOM image being viewed')
            btnDeleteDICOMFile.hide()
         
         
            layout.addWidget(lblHiddenImagePath)
            layout.addWidget(lblHiddenSeriesID)
            layout.addWidget(lblHiddenStudyID)
            layout.addWidget(btnDeleteDICOMFile)

            spinBoxIntensity = QDoubleSpinBox()
            spinBoxContrast = QDoubleSpinBox()
            imageSlider = QSlider(Qt.Horizontal)

            img, imv, viewBox = self.setUpViewBoxForImage(imageViewer, layout, spinBoxIntensity, spinBoxContrast) 
            lblPixelValue = QLabel("<h4>Pixel Value:</h4>")
            lblPixelValue.show()
            layout.addWidget(lblPixelValue)
            cmbColours = self.setUpColourTools(layout, imv, False,  
                                               lblHiddenImagePath, lblHiddenSeriesID, lblHiddenStudyID, 
                                               spinBoxIntensity, spinBoxContrast,
                                               imageSlider, showReleaseButton=True)

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
            #imageSlider.valueChanged.connect(lambda:self.blockHistogramSignals(imv, True))
            imageSlider.valueChanged.connect(
                  lambda: self.imageSliderMoved(seriesName, 
                                                imageList, 
                                                imageSlider.value(),
                                                lblImageMissing,
                                                lblPixelValue,
                                                btnDeleteDICOMFile,
                                                imv, 
                                                spinBoxIntensity, spinBoxContrast,
                                                cmbColours,
                                                subWindow))
           
            #Display the first image in the viewer
            self.imageSliderMoved(seriesName, 
                                  imageList,
                                  imageSlider.value(),
                                  lblImageMissing,
                                  lblPixelValue,
                                  btnDeleteDICOMFile,
                                  imv, 
                                  spinBoxIntensity, spinBoxContrast,
                                  cmbColours,
                                  subWindow)
            
            btnDeleteDICOMFile.clicked.connect(lambda:
                                               self.deleteImageInMultiImageViewer(
                                      self.selectedImagePath, 
                                      lblHiddenStudyID.text(), 
                                      lblHiddenSeriesID.text(),
                                      imageSlider.value()))
            #imageSlider.sliderReleased.connect(lambda: self.blockHistogramSignals(imv, False))
        except Exception as e:
            print('Error in displayMultiImageSubWindow: ' + str(e))
            logger.error('Error in displayMultiImageSubWindow: ' + str(e))

    
    def displayImageROISubWindow(self, derivedImagePath=None):
        """
        Creates a subwindow that displays one DICOM image and allows the creation of an ROI on it 
        """
        try:
            logger.info("WEASEL displayImageROISubWindow called")
            pixelArray = readDICOM_Image.returnPixelArray(self.selectedImagePath)
            colourTable, lut = readDICOM_Image.getColourmap(self.selectedImagePath)

            imageViewer, layout, lblImageMissing, subWindow = \
                self.setUpImageViewerSubWindow()
            windowTitle = self.getDICOMFileData()
            subWindow.setWindowTitle(windowTitle)

            if derivedImagePath:
                lblHiddenImagePath = QLabel(derivedImagePath)
            else:
                lblHiddenImagePath = QLabel(self.selectedImagePath)
            lblHiddenImagePath.hide()
            lblHiddenStudyID = QLabel()
            lblHiddenStudyID.hide()
            lblHiddenSeriesID = QLabel()
            lblHiddenSeriesID.hide()
            
            layout.addWidget(lblHiddenSeriesID)
            layout.addWidget(lblHiddenStudyID)
            layout.addWidget(lblHiddenImagePath)

            img, imv, viewBox = self.setUpViewBoxForImage(imageViewer, layout)
            
            lblPixelValue, lblROIMeanValue = self.setUpLabels(layout)
           
            self.setUpROITools(viewBox, layout, img, lblROIMeanValue)
           
            self.displayROIPixelArray(pixelArray, 0,
                          lblImageMissing, lblPixelValue,
                           colourTable,
                          imv)

            #add second image
            img2 = pg.ImageItem(border='w')
            img2.setImage(np.array(pixelArray))
            img2.setZValue(10) # make sure this image is on top
            img2.setOpacity(0.5)
            imv.setImage(img2)
            #img2.scale(10, 10)

        except Exception as e:
            print('Error in Weasel.displayImageROISubWindow: ' + str(e))
            logger.error('Error in Weasel.displayImageROISubWindow: ' + str(e)) 


    def displayMultiImageROISubWindow(self, imageList, studyName, 
                     seriesName, sliderPosition = -1):
        """
        Creates a subwindow that displays all the DICOM images in a series. 
        A slider allows the user to navigate  through the images.  
        The user may create an ROI on the series of images.
        """
        try:
            logger.info("WEASEL displayMultiImageROISubWindow called")
            imageViewer, layout, lblImageMissing, subWindow = \
                self.setUpImageViewerSubWindow()

            #Study ID & Series ID are stored locally on the
            #sub window in case the user wishes to delete an
            #image in the series.  They may have several series
            #open at once, so the selected series on the treeview
            #may not the same as that from which the image is
            #being deleted.

            lblHiddenImagePath = QLabel('')
            lblHiddenImagePath.hide()
            lblHiddenStudyID = QLabel(studyName)
            lblHiddenStudyID.hide()
            lblHiddenSeriesID = QLabel(seriesName)
            lblHiddenSeriesID.hide()
           
            layout.addWidget(lblHiddenImagePath)
            layout.addWidget(lblHiddenSeriesID)
            layout.addWidget(lblHiddenStudyID)
           
            imageSlider = QSlider(Qt.Horizontal)

            img, imv, viewBox = self.setUpViewBoxForImage(imageViewer, layout) 
            lblPixelValue, lblROIMeanValue = self.setUpLabels(layout)
            
            self.setUpROITools(viewBox, layout, img, lblROIMeanValue)

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
                  lambda: self.imageROISliderMoved(seriesName, 
                                                   imageList, 
                                                   imageSlider.value(),
                                                   lblImageMissing, 
                                                   lblPixelValue, 
                                                   imv, subWindow))
            imageSlider.valueChanged.connect(
                  lambda: self.updateROIMeanValue(self.getROIOject(viewBox), 
                                               img.image, 
                                               img, 
                                               lblROIMeanValue))
            #print('Num of images = {}'.format(len(imageList)))
            #Display the first image in the viewer
            self.imageROISliderMoved(seriesName, 
                                    imageList, 
                                    imageSlider.value(),
                                    lblImageMissing, 
                                    lblPixelValue, 
                                    imv, subWindow)
            
        except Exception as e:
            print('Error in displayMultiImageROISubWindow: ' + str(e))
            logger.error('Error in displayMultiImageROISubWindow: ' + str(e))



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
                treeView.refreshDICOMStudiesTreeView(self)
        except Exception as e:
            print('Error in deleteImageInMultiImageViewer: ' + str(e))
            logger.error('Error in deleteImageInMultiImageViewer: ' + str(e))


    def displayColourTableInComboBox(self, cmbColours, colourTable):
        cmbColours.blockSignals(True)
        index = cmbColours.findText(colourTable)
        if index >= 0:
            cmbColours.setCurrentIndex(index)
        cmbColours.blockSignals(False)

    
    def imageROISliderMoved(self, seriesName, imageList, imageNumber,
                        lblImageMissing, lblPixelValue, 
                        imv, subWindow):
        """On the Multiple Image with ROI Display sub window, this
        function is called when the image slider is moved. 
        It causes the next image in imageList to be displayed"""
        try:
            logger.info("WEASEL imageROISliderMoved called")
            #imageNumber = self.imageSlider.value()
            currentImageNumber = imageNumber - 1
            if currentImageNumber >= 0:
                self.selectedImagePath = imageList[currentImageNumber]
                #print("imageSliderMoved before={}".format(self.selectedImagePath))
                pixelArray = readDICOM_Image.returnPixelArray(self.selectedImagePath)
                colourTable, lut = readDICOM_Image.getColourmap(self.selectedImagePath)

                self.displayROIPixelArray(pixelArray, currentImageNumber,
                          lblImageMissing, lblPixelValue, colourTable,
                          imv)
                
                subWindow.setWindowTitle(seriesName + ' - ' 
                         + os.path.basename(self.selectedImagePath))
               # print("imageSliderMoved after={}".format(self.selectedImagePath))
        except Exception as e:
            print('Error in imageROISliderMoved: ' + str(e))
            logger.error('Error in imageROISliderMoved: ' + str(e))


    def imageSliderMoved(self, seriesName, imageList, imageNumber,
                        lblImageMissing, lblPixelValue, 
                        btnDeleteDICOMFile, imv, 
                        spinBoxIntensity, spinBoxContrast,
                        cmbColours,
                        subWindow):
        """On the Multiple Image Display sub window, this
        function is called when the image slider is moved. 
        It causes the next image in imageList to be displayed"""
        try:
            logger.info("WEASEL imageSliderMoved called")
            #imageNumber = self.imageSlider.value()
            currentImageNumber = imageNumber - 1
            if currentImageNumber >= 0:
                self.selectedImagePath = imageList[currentImageNumber]
                #print("imageSliderMoved before={}".format(self.selectedImagePath))
                pixelArray = readDICOM_Image.returnPixelArray(self.selectedImagePath)
                lut = None
                if self.overRideSavedColourmapAndLevels:
                    colourTable = cmbColours.currentText()
                elif self.applyUserSelection:
                    colourTable, _, _ = self.returnUserSelection(currentImageNumber)  
                    if colourTable == 'default':
                        colourTable, lut = readDICOM_Image.getColourmap(self.selectedImagePath)
                    #print('apply User Selection, colour table {}, image number {}'.format(colourTable,currentImageNumber ))
                else:
                    colourTable, lut = readDICOM_Image.getColourmap(self.selectedImagePath)

                self.displayColourTableInComboBox(cmbColours, colourTable)

                self.displayPixelArray(pixelArray, currentImageNumber, 
                                       lblImageMissing,
                                       lblPixelValue,
                                       spinBoxIntensity, spinBoxContrast,
                                       imv, colourTable,
                                       cmbColours, lut,
                                       multiImage=True,  
                                       deleteButton=btnDeleteDICOMFile) 

                subWindow.setWindowTitle(seriesName + ' - ' 
                         + os.path.basename(self.selectedImagePath))
               # print("imageSliderMoved after={}".format(self.selectedImagePath))
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
                self.displayImageSubWindow()
            elif self.isASeriesSelected():
                studyID = self.selectedStudy 
                seriesID = self.selectedSeries
                self.imageList = self.objXMLReader.getImagePathList(studyID, seriesID)
                self.displayMultiImageSubWindow(self.imageList, studyID, seriesID)
        except Exception as e:
            print('Error in viewImage: ' + str(e))
            logger.error('Error in viewImage: ' + str(e))


    def viewROIImage(self):
        """Creates a subwindow that displays a DICOM image with ROI creation functionality. 
        Executed using the 'View Image with ROI' Menu item in the Tools menu."""
        try:
            logger.info("WEASEL viewROIImage called")
            if self.isAnImageSelected():
                self.displayImageROISubWindow()
            elif self.isASeriesSelected():
                studyID = self.selectedStudy 
                seriesID = self.selectedSeries
                self.imageList = self.objXMLReader.getImagePathList(studyID, seriesID)
                self.displayMultiImageROISubWindow(self.imageList, studyID, seriesID)
        except Exception as e:
            print('Error in viewROIImage: ' + str(e))
            logger.error('Error in viewROIImage: ' + str(e))

  

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
            self.imv1.ui.histogram.hide()
            self.imv1.ui.roiBtn.hide()
            self.imv1.ui.menuBtn.hide()

            imageViewer2 = pg.GraphicsLayoutWidget()
            viewBox2 = imageViewer2.addViewBox()
            viewBox2.setAspectLocked(True)
            self.img2 = pg.ImageItem(border='w')
            viewBox2.addItem(self.img2)
            self.imv2 = pg.ImageView(view=viewBox2, imageItem=self.img2)
            self.imv2.ui.histogram.hide()
            self.imv2.ui.roiBtn.hide()
            self.imv2.ui.menuBtn.hide()

            imageViewer3 = pg.GraphicsLayoutWidget()
            viewBox3 = imageViewer3.addViewBox()
            viewBox3.setAspectLocked(True)
            self.img3 = pg.ImageItem(border='w')
            viewBox3.addItem(self.img3)
            self.imv3 = pg.ImageView(view=viewBox3, imageItem=self.img3)
            self.imv3.ui.histogram.hide()
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
            treeView.refreshDICOMStudiesTreeView(self, newSeriesID)
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
                imagePath2 = imageDict[imageName]

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
                self.img3.setImage(self.binOpArray, autoHistogramRange=True, levels=(minimumValue, maximumValue)) 
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
                objImage.setImage(pixelArray, autoHistogramRange=True, levels=(minimumValue, maximumValue))  
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
                    treeView.refreshDICOMStudiesTreeView(self)
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
                treeView.refreshDICOMStudiesTreeView(self)
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


    #def toggleToolButtons(self):
    #    """TO DO"""
    #    try:
    #        logger.info("WEASEL toggleToolButtons called.")
    #        tools = self.toolsMenu.actions()
    #        for tool in tools:
    #            if not tool.isSeparator():
    #                if not(tool.data() is None):
    #                    #Assume not all tools will act on an image
    #                     #Assume all tools act on a series   
    #                    if self.isASeriesSelected():
    #                         tool.setEnabled(True)
    #                    elif self.isAnImageSelected():
    #                        if tool.data():
    #                            tool.setEnabled(True)
    #                        else:
    #                            tool.setEnabled(False) 
    #    except Exception as e:
    #        print('Error in toggleToolButtons: ' + str(e))
    #        logger.error('Error in toggleToolButtons: ' + str(e))


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


def main():
    app = QApplication(sys . argv )
    winMDI = Weasel()
    winMDI.showMaximized()
    sys.exit(app.exec())

if __name__ == '__main__':
        main()


        