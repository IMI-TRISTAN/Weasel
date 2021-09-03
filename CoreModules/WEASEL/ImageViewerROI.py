from PyQt5 import QtCore 
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QIcon, QCursor
from PyQt5.QtCore import (Qt, pyqtSignal)
from PyQt5.QtWidgets import (QApplication,
                            QFileDialog,                            
                            QMessageBox, 
                            QWidget, 
                            QGridLayout, 
                            QVBoxLayout, 
                            QHBoxLayout, 
                            QMdiSubWindow, 
                            QGroupBox, 
                            QDoubleSpinBox,
                            QPushButton,  
                            QLabel,  
                            QSlider, 
                            QCheckBox,
                            QSpacerItem,
                            QComboBox)

import os
import scipy
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
from scipy.ndimage.morphology import binary_dilation, binary_closing
from scipy.stats import iqr
import CoreModules.WEASEL.ReadDICOM_Image as ReadDICOM_Image
import CoreModules.WEASEL.SaveDICOM_Image as SaveDICOM_Image
import CoreModules.WEASEL.TreeView as treeView
import CoreModules.WEASEL.DisplayImageCommon as displayImageCommon
import CoreModules.WEASEL.MessageWindow as messageWindow
import Trash.InputDialog as inputDialog # obsolete - replace by user_input
import CoreModules.WEASEL.InterfaceDICOMXMLFile as interfaceDICOMXMLFile
from CoreModules.FreeHandROI.GraphicsView import GraphicsView
from CoreModules.FreeHandROI.ROI_Storage import ROIs 
import CoreModules.FreeHandROI.Resources as icons
from CoreModules.WEASEL.ImageSliders import ImageSliders as imageSliders
from CoreModules.WEASEL.ImageLevelsSpinBoxes import ImageLevelsSpinBoxes as imageLevelsSpinBoxes

import logging
logger = logging.getLogger(__name__)

#Subclassing QSlider so that the direction (Forward, Backward) of 
#slider travel is returned to the calling function
class Slider(QSlider):
    Nothing, Forward, Backward = 0, 1, -1
    directionChanged = pyqtSignal(int)
    def __init__(self, parent=None):
        QSlider.__init__(self, parent)
        self._direction = Slider.Nothing
        self.last = self.value()/self.maximum()
        self.valueChanged.connect(self.onValueChanged)

    def onValueChanged(self, value):
        current = value/self.maximum()
        direction = Slider.Forward if self.last < current else Slider.Backward
        if self._direction != direction:
            self.directionChanged.emit(direction)
            self._direction = direction
        self.last = current

    def direction(self):
        return self._direction


class ImageViewerROI(QMdiSubWindow):
    """This class creates a subwindow for viewing an image or series of images with
    the facility to draw a ROI on the image.  It also has multiple
    sliders for browsing series of images."""

    def __init__(self,  pointerToWeasel, subjectID, 
                 studyID, seriesID, imagePathList): 
        try:
            super().__init__()
            self.subjectID = subjectID
            self.studyID = studyID
            self.seriesID = seriesID
            self.imagePathList = imagePathList
            self.selectedImagePath = ""
            self.imageNumber = -1
            self.weasel = pointerToWeasel
            #A list of the sorted image sliders, 
            #updated as they are added and removed 
            #from the subwindow
            self.listSortedImageSliders = [] 
            
            if singleImageSelected:
                self.isSeries = False
                self.isImage = True
                self.selectedImagePath = imagePathList
            else:
                self.isSeries = True
                self.isImage = False

            self.setWindowFlags(Qt.CustomizeWindowHint | 
                                          Qt.WindowCloseButtonHint | 
                                          Qt.WindowMinimizeButtonHint |
                                          Qt.WindowMaximizeButtonHint)
        
            height, width = self.weasel.getMDIAreaDimensions()
            self.subWindowWidth = width
            #Set dimensions of the subwindow to fit the MDI area
            self.setGeometry(0, 0, width, height)
            #Add subwindow to MDI
            self.weasel.mdiArea.addSubWindow(self)
                
            self.setUpMainLayout() 

            self.setUpTopRowLayout()

            self.setUpGraphicsViewLayout()
            
            self.setUpImageDataLayout()

            self.setUpLevelsSpinBoxes()

            self.setUpImageSliders()

            self.setUpZoomSlider()

            self.setUpImageDataWidgets()


    def setUpMainLayout(self):
        try:
            self.mainVerticalLayout = QVBoxLayout()
            self.widget = QWidget()
            self.widget.setLayout(self.mainVerticalLayout)
            self.setWidget(self.widget)
        except Exception as e:
            print('Error in ImageViewer.setUpMainLayout: ' + str(e))
            logger.error('Error in ImageViewer.setUpMainLayout: ' + str(e))


    def setUpRoiToolsLayout(self):
        self.roiToolsLayout = QHBoxLayout()
        self.roiToolsLayout.setContentsMargins(0, 2, 0, 0)
        self.roiToolsLayout.setSpacing(0)
        self.roiToolsGroupBox = QGroupBox("ROIs")
        self.roiToolsGroupBox.setLayout(self.roiToolsLayout)


    def setUpROIDropDownList(self):
        self.cmbROIs = QComboBox()
        self.lblCmbROIs =  QLabel("ROIs")
        self.cmbROIs.setDuplicatesEnabled(False)
        self.cmbROIs.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbROIs.addItem("region1")
        self.cmbROIs.setCurrentIndex(0)
        self.cmbROIs.setStyleSheet('QComboBox {font: 12pt Arial}')
        self.cmbROIs.setToolTip("Displays a list of ROIs created")
        self.cmbROIs.setEditable(True)
        self.cmbROIs.setInsertPolicy(QComboBox.InsertAtCurrent)


    def connectSlotToSignalForROITools(self):
        self.btnDeleteROI.clicked.connect(self.graphicsView.deleteROI)
        self.btnNewROI.clicked.connect(self.graphicsView.newROI)
        self.btnResetROI.clicked.connect(self.graphicsView.resetROI)
        self.btnSaveROI.clicked.connect(self.saveROI)
        self.btnLoad.clicked.connect(self.loadROI)
        self.btnErase.clicked.connect(lambda checked: self.eraseROI(checked))
        self.btnDraw.clicked.connect(lambda checked: self.drawROI(checked))
        self.btnZoom.clicked.connect(lambda checked: self.zoomImage(checked))
        self.cmbROIs.currentIndexChanged.connect(
            lambda: self.reloadImageInNewImageItem(cmbROIs, graphicsView, pixelValueTxt,                          
                                   roiMeanTxt, roiStdDevTxt, self, buttonList, 
                                   btnDraw, btnErase, 
                                  zoomSlider, zoomLabel, imageSlider))
        
        self.cmbROIs.editTextChanged.connect(lambda text: self.roiNameChanged(cmbROIs, graphicsView, text))


    def saveROI(self):
        try:
            # Save Current ROI
            regionName = self.cmbROIs.currentText()
            logger.info("DisplayImageDrawROI.saveROI called")
            maskList = self.graphicsView.dictROIs.dictMasks[regionName] # Will return a list of boolean masks
            maskList = [np.transpose(np.array(mask, dtype=np.int)) for mask in maskList] # Convert each 2D boolean to 0s and 1s
            suffix = str("_ROI_"+ regionName)
            if len(maskList) > 1:
                inputPath = [i[3] for i in self.weasel.checkedImageList]
                #inputPath = self.imageList
            else:
                inputPath = [self.selectedImagePath]
            # Saving Progress message
            messageWindow.displayMessageSubWindow(self.weasel,
                "<H4>Saving ROIs into a new DICOM Series ({} files)</H4>".format(len(inputPath)),
                "Export ROIs")
            messageWindow.setMsgWindowProgBarMaxValue(self.weasel, len(inputPath))
            (subjectID, studyID, seriesID) = self.objXMLReader.getImageParentIDs(inputPath[0])
            seriesID = str(int(self.objXMLReader.getStudy(subjectID, studyID)[-1].attrib['id'].split('_')[0]) + 1)
            seriesUID = SaveDICOM_Image.generateUIDs(ReadDICOM_Image.getDicomDataset(inputPath[0]), seriesID)
            #outputPath = []
            #for image in inputPath:
            for index, path in enumerate(inputPath):
                #outputPath.append(SaveDICOM_Image.returnFilePath(image, suffix))
                messageWindow.setMsgWindowProgBarValue(self.weasel, index)
                outputPath = SaveDICOM_Image.returnFilePath(path, suffix)
                SaveDICOM_Image.saveNewSingleDicomImage(outputPath, path, maskList[index], suffix, series_id=seriesID, series_uid=seriesUID, parametric_map="SEG")
                treeSeriesID = interfaceDICOMXMLFile.insertNewImageInXMLFile(self.weasel, path, outputPath, suffix)
            #SaveDICOM_Image.saveDicomNewSeries(outputPath, inputPath, maskList, suffix, parametric_map="SEG") # Consider Enhanced DICOM for parametric_map
            #seriesID = interfaceDICOMXMLFile.insertNewSeriesInXMLFile(self, inputPath, outputPath, suffix)
            messageWindow.setMsgWindowProgBarValue(self.weasel, len(inputPath))
            messageWindow.closeMessageSubWindow(self.weasel)
            treeView.refreshDICOMStudiesTreeView(self.weasel, newSeriesName=treeSeriesID)
            QMessageBox.information(self.weasel, "Export ROIs", "Image Saved")
        except Exception as e:
                print('Error in DisplayImageDrawROI.saveROI: ' + str(e))
                logger.error('Error in DisplayImageDrawROI.saveROI: ' + str(e)) 


    def loadROI(self):
        try:
            logger.info("DisplayImageDrawROI.loadROI called")
            # The following workflow is assumed:
            #   1. The user first loads a series of DICOM images
            #   2. Then the user loads the series of ROIs that are superimposed upon the images

            # Prompt Windows to select Series
            paramDict = {"Series":"listview"}
            helpMsg = "Select a Series with ROI"
            #studyID = self.selectedStudy
            study = self.objXMLReader.getStudy(self.subjectID, self.studyID)
            listSeries = [series.attrib['id'] for series in study] # if 'ROI' in series.attrib['id']]
            inputDlg = inputDialog.ParameterInputDialog(paramDict, title= "Load ROI", helpText=helpMsg, lists=[listSeries])
            listParams = inputDlg.returnListParameterValues()
            if inputDlg.closeInputDialog() == False:
                # for series ID in listParams[0]: # more than 1 ROI may be selected
                seriesID = listParams[0][0] # Temporary, only the first ROI
                imagePathList = self.objXMLReader.getImagePathList(self.subjectID, self.studyID, seriesID)
                if self.isASeriesChecked:
                    targetPath = [i[3] for i in self.checkedImageList]
                    #targetPath = self.imageList
                else:
                    targetPath = [self.selectedImagePath]
                maskInput = ReadDICOM_Image.returnSeriesPixelArray(imagePathList)
                maskInput[maskInput != 0] = 1
                maskList = [] # Output Mask
                # Consider DICOM Tag SegmentSequence[:].SegmentLabel as some 3rd software do
                if hasattr(ReadDICOM_Image.getDicomDataset(imagePathList[0]), "ContentDescription"):
                    region = ReadDICOM_Image.getSeriesTagValues(imagePathList, "ContentDescription")[0][0]
                else:
                    region = "new_region_label"
                # Affine re-adjustment
                for index, dicomFile in enumerate(targetPath):
                    messageWindow.displayMessageSubWindow(self.weasel,
                    "<H4>Loading selected ROI into target image {}</H4>".format(index + 1),
                    "Load ROIs")
                    messageWindow.setMsgWindowProgBarMaxValue(self.weasel, len(targetPath))
                    messageWindow.setMsgWindowProgBarValue(self.weasel, index + 1)
                    dataset_original = ReadDICOM_Image.getDicomDataset(dicomFile)
                    tempArray = np.zeros(np.shape(ReadDICOM_Image.getPixelArray(dataset_original)))
                    horizontalFlag = None
                    verticalFlag = None
                    for maskFile in imagePathList:
                        dataset = ReadDICOM_Image.getDicomDataset(maskFile)
                        maskArray = ReadDICOM_Image.getPixelArray(dataset)
                        maskArray[maskArray != 0] = 1
                        affineResults = ReadDICOM_Image.mapMaskToImage(maskArray, dataset, dataset_original)
                        if affineResults:
                            try:
                                coords = zip(*affineResults)
                                tempArray[tuple(coords)] = list(np.ones(len(affineResults)).flatten())
                                #if len(np.unique([idx[0] for idx in affineResults])) == 1 and len(np.unique([idx[1] for idx in affineResults])) != 1: horizontalFlag = True
                                #if len(np.unique([idx[1] for idx in affineResults])) == 1 and len(np.unique([idx[0] for idx in affineResults])) != 1: verticalFlag = True
                            except:
                                pass
                    # Will need an Enhanced MRI as example  
                    #if ~hasattr(dataset_original, 'PerFrameFunctionalGroupsSequence'):
                        #if horizontalFlag == True:
                            #struct_elm = np.ones((int(dataset_original.SliceThickness / dataset.PixelSpacing[0]), 1)) # Change /2 value here
                            #tempArray = binary_dilation(tempArray, structure=struct_elm).astype(int)
                            #tempArray = binary_closing(tempArray, structure=struct_elm).astype(int)
                        #elif verticalFlag == True:
                            #struct_elm = np.ones((1, int(dataset_original.SliceThickness / dataset.PixelSpacing[1]))) # Change /2 value here
                            #tempArray = binary_dilation(tempArray, structure=struct_elm).astype(int)
                            #tempArray = binary_closing(tempArray, structure=struct_elm).astype(int)
                    maskList.append(tempArray)
                    messageWindow.setMsgWindowProgBarValue(self.weasel, index + 2)
                messageWindow.closeMessageSubWindow(self.weasel)

                # Faster approach - 3D and no dilation
                #maskList = np.zeros(np.shape(ReadDICOM_Image.returnSeriesPixelArray(targetPath)))
                #dataset_original = ReadDICOM_Image.getDicomDataset(targetPath)
                #dataset = ReadDICOM_Image.getDicomDataset(imagePathList[0])
                #affineResults = ReadDICOM_Image.mapMaskToImage(maskInput, dataset, dataset_original)
                #if affineResults:
                    #try:
                        #coords = zip(*affineResults)
                        #maskList[tuple(coords)] = list(np.ones(len(affineResults)).flatten())
                    #except:
                        #pass
            
                # First populate the ROI_Storage data structure in a loop
                for imageNumber in range(len(maskList)):
                    self.graphicsView.dictROIs.addRegion(region, 
                                                         np.array(maskList[imageNumber]).astype(bool), 
                                                         imageNumber + 1)

                # Second populate the dropdown list of region names
                self.cmbROIs.blockSignals(True)
                #remove previous contents of ROI dropdown list
                self.cmbROIs.clear()  
                self.cmbROIs.addItems(self.graphicsView.dictROIs.getListOfRegions())
                self.cmbROIs.blockSignals(False)

                # Redisplay the current image to show the mask
                #mask = graphicsView.dictROIs.getMask(region, 1)
                #graphicsView.graphicsItem.reloadMask(mask)
                self.cmbROIs.setCurrentIndex(self.cmbROIs.count() - 1)
        except Exception as e:
                print('Error in DisplayImageDrawROI.loadROI: ' + str(e))
                logger.error('Error in DisplayImageDrawROI.loadROI: ' + str(e)) 


    def eraseROI(self, checked):
        logger.info("DisplayImageDrawROI.eraseROI called.")
        if checked:
            self.setButtonsToDefaultStyle(self.buttonList)
            self.graphicsView.eraseROI()
            self.btnErase.setStyleSheet("background-color: red")
        else:
            QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
            self.graphicsView.graphicsItem.eraseEnabled = False
            self.btnErase.setStyleSheet(
             "background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #CCCCBB, stop: 1 #FFFFFF)"
             )


    def setButtonsToDefaultStyle(self):
        logger.info("DisplayImageDrawRIO.setButtonsToDefaultStyle called")
        try:
            logger.info("DisplayImageDrawROI.setButtonsToDefaultStyle called.")
            QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
            if len(self.buttonList) > 0:
                for button in self.buttonList:
                    button.setStyleSheet(
                     "background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #CCCCBB, stop: 1 #FFFFFF)"
                     )
        except Exception as e:
                print('Error in DisplayImageDrawROI.setButtonsToDefaultStyle: ' + str(e))
                logger.error('Error in DisplayImageDrawROI.setButtonsToDefaultStyle: ' + str(e))  

    
    def drawROI(self, checked):
        logger.info("DisplayImageDrawROI.drawROI called.")
        if checked:
            self.setButtonsToDefaultStyle()
            self.graphicsView.drawROI()
            self.btnDraw.setStyleSheet("background-color: red")
        else:
            QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
            self.graphicsView.graphicsItem.drawEnabled = False
            self.btnDraw.setStyleSheet(
             "background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #CCCCBB, stop: 1 #FFFFFF)"
             )


    def zoomImage(self, checked):
        logger.info("DisplayImageDrawROI.zoomImage called.")
        if checked:
            self.setButtonsToDefaultStyle()
            self.graphicsView.setZoomEnabled(True)
            self.graphicsView.graphicsItem.drawEnabled = False
            self.graphicsView.graphicsItem.eraseEnabled = False
            self.btnZoom.setStyleSheet("background-color: red")
        else:
            QApplication.setOverrideCursor(QCursor(Qt.ArrowCursor))
            self.graphicsView.setZoomEnabled(False)
            self.btnZoom.setStyleSheet(
             "background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #CCCCBB, stop: 1 #FFFFFF)"
             )

    
    def reloadImageInNewImageItem(cmbROIs, graphicsView, pixelValueTxt,  
                                roiMeanTxt, roiStdDevTxt, self, buttonList, 
                              btnDraw, btnErase, zoomSlider, zoomLabel,
                              imageSlider=None ):
        try:
            logger.info("DisplayImageDrawROI.reloadImageInNewImageItem called")
            self.graphicsView.dictROIs.setPreviousRegionName(cmbROIs.currentText())

            #if imageSlider:  to do
         #       imageNumber = imageSlider.value()
          #  else:
            imageNumber = 1

            pixelArray = ReadDICOM_Image.returnPixelArray(self.selectedImagePath)
            mask = self.graphicsView.dictROIs.getMask(self.cmbROIs.currentText(), imageNumber)
            self.graphicsView.setImage(pixelArray, mask, self.selectedImagePath)
            self.displayROIMeanAndStd()  
            self.setUpImageEventHandlers(self, graphicsView, pixelValueTxt, 
                                    roiMeanTxt, roiStdDevTxt, 
                                    btnDraw, btnErase, 
                                    cmbROIs, buttonList, zoomSlider, zoomLabel, imageSlider)
        except Exception as e:
               print('Error in DisplayImageDrawROI.reloadImageInNewImageItem: ' + str(e))
               logger.error('Error in DisplayImageDrawROI.reloadImageInNewImageItem: ' + str(e))


    def getRoiMeanAndStd(self, mask, pixelArray):
        logger.info("DisplayImageDrawROI.getRoiMeanAndStd called")
        mean = round(np.mean(np.extract(np.transpose(mask), pixelArray)), 6)
        std = round(np.std(np.extract(np.transpose(mask), pixelArray)), 6)
        return mean, std


    def displayROIMeanAndStd(self):
        logger.info("DisplayImageDrawROI.displayROIMeanAndStd called")
        #if imageSlider:
        #    imageNumber = imageSlider.value()
        #else:
        imageNumber = 1
        pixelArray = ReadDICOM_Image.returnPixelArray(self.selectedImagePath)
        regionName = self.cmbROIs.currentText()
        mask = self.graphicsView.dictROIs.getMask(regionName, imageNumber)
        if mask is not None:
            mean, std = self.getRoiMeanAndStd(mask, pixelArray)
            self.roiMeanTxt.setText(str(mean))
            self.roiStdDevTxt.setText(str(std))
        else:
            self.roiMeanTxt.clear()
            self.roiStdDevTxt.clear()


    def setUpImageEventHandlers(self):
        logger.info("DisplayImageDrawROI.setUpImageEventHandlers called.")
        try:
            self.graphicsView.graphicsItem.sigMouseHovered.connect(
            lambda mouseOverImage:displayImageDataUnderMouse(mouseOverImage))

            graphicsView.graphicsItem.sigMaskCreated.connect(self.storeMaskData)

            graphicsView.graphicsItem.sigMaskCreated.connect(self.displayROIMeanAndStd)

            graphicsView.graphicsItem.sigMaskEdited.connect(self.replaceMask)

            graphicsView.graphicsItem.sigMaskEdited.connect(self.storeMaskData)

            graphicsView.sigContextMenuDisplayed.connect(self.setButtonsToDefaultStyle)

            graphicsView.sigReloadImage.connect(lambda:reloadImageInNewImageItem(cmbROIs, graphicsView, 
                                                pixelValueTxt,  
                                                roiMeanTxt, roiStdDevTxt, self, buttonList, 
                                                btnDraw, btnErase, zoomSlider, 
                                        zoomLabel, imageSlider ))

            graphicsView.sigROIDeleted.connect(lambda:deleteROITidyUp(self, cmbROIs, graphicsView, 
                        pixelValueTxt,  
                    roiMeanTxt, roiStdDevTxt, buttonList, btnDraw, btnErase,  
                        zoomSlider, zoomLabel, imageSlider))

            graphicsView.sigSetDrawButtonRed.connect(lambda setRed:setDrawButtonColour(setRed, btnDraw, btnErase))

            graphicsView.sigSetEraseButtonRed.connect(lambda setRed:setEraseButtonColour(setRed, btnDraw, btnErase))

            graphicsView.sigROIChanged.connect(self.setButtonsToDefaultStyle)
            graphicsView.sigROIChanged.connect(lambda:updateROIName(graphicsView, cmbROIs))
            graphicsView.sigNewROI.connect(lambda newROIName:addNewROItoDropDownList(newROIName, cmbROIs))
            graphicsView.sigUpdateZoom.connect(lambda increment:updateZoomSlider(zoomSlider, zoomLabel, increment))
        except Exception as e:
                print('Error in DisplayImageDrawROI.setUpImageEventHandlers: ' + str(e))
                logger.error('Error in DisplayImageDrawROI.setUpImageEventHandlers: ' + str(e)) 

    
    def displayImageDataUnderMouse(mouseOverImage):
        logger.info("DisplayImageDrawROI.displayImageDataUnderMouse called")
        #print("mousePointerOverImage={}".format(mousePointerOverImage))
        if mouseOverImage:
            xCoord = self.graphicsView.graphicsItem.xMouseCoord
            yCoord = self.graphicsView.graphicsItem.yMouseCoord
            pixelValue = self.graphicsView.graphicsItem.pixelValue
            strValue = str(pixelValue)
            #if imageSlider:
            #    imageNumber = imageSlider.value()
            #else:
            imageNumber = 1
            strPosition = ' @ X:' + str(xCoord) + ', Y:' + str(yCoord) + ', Z:' + str(imageNumber)
            self.pixelValueTxt.setText('= ' + strValue + strPosition)
        else:
             self.pixelValueTxt.setText('')


    def storeMaskData(self):
        logger.info("DisplayImageDrawROI.storeMaskData called")
        regionName = self.cmbROIs.currentText()
        #if imageSlider:
        #    imageNumber = imageSlider.value()
        #else:
        imageNumber = 1
        mask = self.graphicsView.graphicsItem.getMaskData()
        self.graphicsView.dictROIs.addRegion(regionName, mask, imageNumber)


    def replaceMask(self):
        logger.info("DisplayImageDrawROI.replaceMask called")
        regionName = self.cmbROIs.currentText()
        #if imageSlider:
        #    imageNumber = imageSlider.value()
        #else:
        imageNumber = 1
        mask = self.graphicsView.graphicsItem.getMaskData()
        self.graphicsView.dictROIs.replaceMask(regionName, mask, imageNumber)


    def setUpROIButtons(self):
        try:
            logger.info("DisplayImageDrawROI.setUpPixelDataWidget called.")
            self.buttonList = []
            self.setUpROIDropDownList()

            self.btnDeleteROI = QPushButton() 
            self.btnDeleteROI.setToolTip('Delete the current ROI')
            self.btnDeleteROI.setIcon(QIcon(QPixmap(icons.DELETE_ICON)))
        
            self.btnNewROI = QPushButton() 
            self.btnNewROI.setToolTip('Add a new ROI')
            self.btnNewROI.setIcon(QIcon(QPixmap(icons.NEW_ICON)))

            self.btnResetROI = QPushButton()
            self.btnResetROI.setToolTip('Clears the ROI from the image')
            self.btnResetROI.setIcon(QIcon(QPixmap(icons.RESET_ICON)))

            self.btnSaveROI = QPushButton()
            self.btnSaveROI.setToolTip('Saves the ROI in DICOM format')
            self.btnSaveROI.setIcon(QIcon(QPixmap(icons.SAVE_ICON)))

            self.btnLoad = QPushButton()
            self.btnLoad.setToolTip('Loads existing ROIs')
            self.btnLoad.setIcon(QIcon(QPixmap(icons.LOAD_ICON)))

            self.btnErase = QPushButton()
            self.buttonList.append(btnErase)
            self.btnErase.setToolTip("Erase the ROI")
            self.btnErase.setCheckable(True)
            self.btnErase.setIcon(QIcon(QPixmap(icons.ERASOR_CURSOR)))

            self.btnDraw = QPushButton()
            self.buttonList.append(btnDraw)
            self.btnDraw.setToolTip("Draw an ROI")
            self.btnDraw.setCheckable(True)
            self.btnDraw.setIcon(QIcon(QPixmap(icons.PEN_CURSOR)))

            self.btnZoom = QPushButton()
            self.buttonList.append(btnZoom)
            self.btnZoom.setToolTip("Zoom In-Left Mouse Button/Zoom Out-Right Mouse Button")
            self.btnZoom.setCheckable(True)
            self.btnZoom.setIcon(QIcon(QPixmap(icons.MAGNIFYING_GLASS_CURSOR)))

            self.connectSlotToSignalForROITools()
            
            self.roiToolsLayout.addWidget(self.btnNewROI, alignment=Qt.AlignLeft)
            self.roiToolsLayout.addWidget(self.btnResetROI,  alignment=Qt.AlignLeft)
            self.roiToolsLayout.addWidget(self.btnDeleteROI,  alignment=Qt.AlignLeft)
            self.roiToolsLayout.addWidget(self.btnSaveROI,  alignment=Qt.AlignLeft)
            self.roiToolsLayout.addWidget(self.btnLoad,  alignment=Qt.AlignLeft)
            self.roiToolsLayout.addWidget(self.btnDraw,  alignment=Qt.AlignLeft)
            self.roiToolsLayout.addWidget(self.btnErase, alignment=Qt.AlignLeft)
            self.roiToolsLayout.addWidget(self.btnZoom,  alignment=Qt.AlignLeft)
            self.roiToolsLayout.addStretch(20)
            
        except Exception as e:
               print('Error in DisplayImageDrawROI.setUpROIButtons: ' + str(e))
               logger.error('Error in DisplayImageDrawROI.setUpROIButtons: ' + str(e)) 

            






















    def setUpImageLevelsLayout(self):
        self.imageLevelsLayout= QHBoxLayout()
        self.imageLevelsLayout.setContentsMargins(0, 2, 0, 0)
        self.imageLevelsLayout.setSpacing(0)
        self.imageLevelsGroupBox = QGroupBox()
        self.imageLevelsGroupBox.setLayout(imageLevelsLayout)


    def setUpTopRowLayout(self):
        try:
            self.topRowMainLayout = QHBoxLayout()
            
            self.setUpRoiToolsLayout()
            
            self.setUpImageLevelsLayout()
            
            self.topRowMainLayout.addWidget(self.roiToolsGroupBox)
            self.topRowMainLayout.addWidget(self.imageLevelsGroupBox)
        
            self.mainVerticalLayout.addLayout(self.topRowMainLayout)

            self.lblImageMissing = QLabel("<h4>Image Missing</h4>")
            self.lblImageMissing.hide()
            self.mainVerticalLayout.addWidget(self.lblImageMissing)
        except Exception as e:
            print('Error in ImageViewerROI.setUpTopRowLayout: ' + str(e))
            logger.error('Error in ImageViewerROI.setUpTopRowLayout: ' + str(e))


    def setUpGraphicsViewLayout(self):
        self.graphicsViewLayout = QHBoxLayout()
        self.graphicsViewLayout.setContentsMargins(0, 0, 0, 0)
        self.graphicsViewLayout.setSpacing(0)
        self.graphicsView = GraphicsView()
        self.graphicsViewLayout.addWidget(self.graphicsView)
        self.mainVerticalLayout.addLayout(self.graphicsViewLayout)


    def setUpImageDataLayout(self):
        self.imageDataLayout = QHBoxLayout()
        self.imageDataLayout.setContentsMargins(0, 0, 0, 0)
        self.imageDataLayout.setSpacing(0)
        self.imageDataGroupBox = QGroupBox()
        self.imageDataGroupBox.setLayout(self.imageDataLayout)
        self.mainVerticalLayout.addWidget(self.imageDataGroupBox)


    def setUpImageDataWidgets(self):
        try:
            logger.info("ImageViewerROI.setUpImageDataWidgets called.")
        
            self.pixelValueLabel = QLabel("Pixel Value")
            self.pixelValueLabel.setAlignment(Qt.AlignRight)
            self.pixelValueLabel.setStyleSheet("padding-right:1; margin-right:1;")

            self.pixelValueTxt = QLabel()
            self.pixelValueTxt.setIndent(0)
            self.pixelValueTxt.setAlignment(Qt.AlignLeft)
            self.pixelValueTxt.setStyleSheet("color : red; padding-left:1; margin-left:1;")

            self.roiMeanLabel = QLabel("ROI Mean")
            self.roiMeanLabel.setStyleSheet("padding-right:1; margin-right:1;")
            self.roiMeanTxt = QLabel()
            self.roiMeanTxt.setStyleSheet("color : red; padding-left:1; margin-left:1;")

            self.roiStdDevLabel = QLabel("ROI Sdev.")
            self.roiStdDevLabel.setStyleSheet("padding-right:1; margin-right:1;")

            self.roiStdDevTxt = QLabel()
            self.roiStdDevTxt.setStyleSheet("color : red; padding-left:1; margin-left:1;")

            self.zoomLabel = QLabel("Zoom:")
            self.zoomLabel.setStyleSheet("padding-right:1; margin-right:1;")
            self.zoomValueLabel.setStyleSheet("color : red; padding-left:1; margin-left:1;")
        
            self.imageDataLayout.addWidget(pixelValueLabel, Qt.AlignRight)
            self.imageDataLayout.addWidget(pixelValueTxt, Qt.AlignLeft)
            self.imageDataLayout.addWidget(roiMeanLabel, Qt.AlignLeft) 
            self.imageDataLayout.addWidget(roiMeanTxt, Qt.AlignLeft) 
            self.imageDataLayout.addWidget(roiStdDevLabel, Qt.AlignLeft)
            self.imageDataLayout.addWidget(roiStdDevTxt, Qt.AlignLeft)
            self.imageDataLayout.addWidget(zoomLabel, Qt.AlignLeft)
            self.imageDataLayout.addWidget(zoomValueLabel, Qt.AlignLeft)
            self.imageDataLayout.addStretch(10)
    
        except Exception as e:
                print('Error in ImageViewerROI.setUpImageDataWidgets: ' + str(e))
                logger.error('Error in ImageViewerROI.setUpImageDataWidgets: ' + str(e))


    def setUpLevelsSpinBoxes(self):
        try:
            spinBoxObject = imageLevelsSpinBoxes()
            self.imageLevelsLayout.addLayout(spinBoxObject.getCompositeComponent())
            self.spinBoxIntensity, self.spinBoxContrast = spinBoxObject.getSpinBoxes() 
            self.spinBoxIntensity.valueChanged.connect(self.updateImageLevels)
            self.spinBoxContrast.valueChanged.connect(self.updateImageLevels)
        except Exception as e:
            print('Error in ImageViewerROI.setUpLevelsSpinBoxes: ' + str(e))
            logger.error('Error in ImageViewerROI.setUpLevelsSpinBoxes: ' + str(e))


    def updateImageLevels(self):
        logger.info("ImageViewerROI.updateImageLevels called.")
        try:
            #if imageSlider:  To Do
            #    imageNumber = imageSlider.value()
            #else:
            #    imageNumber = 1
            intensity = self.spinBoxIntensity.value()
            contrast = self.spinBoxContrast.value()
            mask = self.graphicsView.dictROIs.getMask(self.cmbROIs.currentText(), imageNumber)
            graphicsView.graphicsItem.updateImageLevels(intensity, contrast, mask)
        except Exception as e:
            print('Error in ImageViewerROI.updateImageLevels when imageNumber={}: '.format(imageNumber) + str(e))
            logger.error('Error in ImageViewerROI.updateImageLevels: ' + str(e))


    def setUpImageSliders(self):
        try:
            #create an instance of the ImageSliders class
            self.slidersWidget = imageSliders(self.weasel, 
                                             self.subjectID, 
                                             self.studyID, 
                                             self.seriesID, 
                                             self.imagePathList)

            self.mainVerticalLayout.addLayout(
                    self.slidersWidget.getCustomSliderWidget())

            #This is how an object created from the ImageSliders class communicates
            #with an object created from the ImageViewer class via the former's
            #sliderMoved event, which passes the image path of the image being viewed
            #to ImageViewer's displayPixelArrayOfImageInSeries function for display.
            self.slidersWidget.sliderMoved.connect(lambda imagePath: 
                                                   self.displayPixelArrayOfImageInSeries(imagePath))
            #Display the first image in the viewer
            self.slidersWidget.displayFirstImage()
        except Exception as e:
            print('Error in ImageViewer.setUpImageSliders: ' + str(e))
            logger.error('Error in ImageViewer.setUpImageSliders: ' + str(e))


    def setUpZoomSlider(self):
        try:
            self.zoomSlider = Slider(Qt.Vertical)
            self.zoomLabel = QLabel("<H4>100%</H4>")
            self.zoomSlider.setMinimum(0)
            self.zoomSlider.setMaximum(20)
            self.zoomSlider.setSingleStep(1)
            self.zoomSlider.setTickPosition(QSlider.TicksBothSides)
            self.zoomSlider.setTickInterval(1)
            self.zoomSlider.valueChanged.connect(lambda: 
                  self.graphicsView.zoomImage(self.zoomSlider.direction()))
        except Exception as e:
                print('Error in ImageViewerROI.setUpZoomSlider: ' + str(e))
                logger.error('Error in ImageViewerROI.setUpZoomSlider: ' + str(e))  