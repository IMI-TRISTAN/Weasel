from PyQt5.QtCore import  Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import (QMessageBox, 
                            QFormLayout,
                            QHBoxLayout,
                            QVBoxLayout,
                            QPushButton,  
                            QLabel, 
                            QSlider, 
                            QListWidget,
                            QListWidgetItem,
                            QListView)

import numpy as np
import copy
import CoreModules.WEASEL.ReadDICOM_Image as ReadDICOM_Image
from DICOM.Classes import Series

import logging
logger = logging.getLogger(__name__)

listImageTypes = ["SliceLocation", "AcquisitionTime", "AcquisitionNumber", 
                  "FlipAngle", "InversionTime", "EchoTime", 
                  (0x2005, 0x1572)] # This last element is a good example of private tag


class SortedImageSlider(QSlider):
    """Subclass of the QSlider class with the added property attribute 
    which identifies what the image subset has been filtered for"""
    def __init__(self,  DicomAttribute): 
       super().__init__(orientation=Qt.Horizontal)
       self.attribute =  DicomAttribute
       self.setToolTip("Images sorted according to {}".format(DicomAttribute))


class ImageSliders(QObject):
    """Creates a custom, composite widget composed of one or more sliders for 
    navigating a DICOM series of images."""

    sliderMoved = pyqtSignal(str)


    def __init__(self,  pointerToWeasel, subjectID, 
                 studyID, seriesID, imagePathList):
        try:
            #Super class QObject to provide support for pyqtSignal
            super().__init__()
            self.imagePathList = imagePathList
            self.subjectID = subjectID
            self.studyID = studyID
            self.seriesID = seriesID
            self.weasel = pointerToWeasel
            self.selectedImagePath = imagePathList[0]
        
            # Global variables for the Multisliders
            self.dynamicListImageType = []
            self.shapeList = []
            self.arrayForMultiSlider = self.imagePathList # Please find the explanation of this variable at __multipleImageSliderMoved(self)
            self.seriesToFormat = Series(self.weasel, self.subjectID, self.studyID, self.seriesID, listPaths=self.imagePathList)
            #A list of the sorted image sliders, 
            #updated as they are added and removed 
            #from the subwindow
            self.listSortedImageSliders = []  

            #Create the custom, composite sliders widget
            self.__setUpLayouts()
            self.__createMainImageSlider()
            self.__addMainImageSliderToLayout()
            self.__setUpImageTypeList()
            self.__setUpSliderResetButton()
        except Exception as e:
            print('Error in ImageSliders.__init__: ' + str(e))
            logger.error('Error in ImageSliders.__init__: ' + str(e))


    def getCustomSliderWidget(self):
        """A public function that passes the 
        composite slider widget to the
        parent layout on the subwindow"""
        return self.mainVerticalLayout


    def getMainSlider(self):
        """A public function that passes the main image 
        slider to Weasel"""
        return self.mainImageSlider


    def displayFirstImage(self):
        """A public function that displays the first image 
        in Weasel"""
        self.__mainImageSliderMoved(1)


    def __setUpLayouts(self):
        try:
            self.mainVerticalLayout = QVBoxLayout()
        
            self.mainSliderLayout = QHBoxLayout()
            self.imageTypeLayout = QHBoxLayout()
            self.sortedImageSliderLayout = QFormLayout()
        
            self.mainVerticalLayout.addLayout(self.mainSliderLayout)
            self.mainVerticalLayout.addLayout(self.imageTypeLayout)
            self.mainVerticalLayout.addLayout(self.sortedImageSliderLayout)
        except Exception as e:
            print('Error in ImageSliders.__setUpLayouts: ' + str(e))
            logger.error('Error in ImageSliders.__setUpLayouts: ' + str(e))

    
    def __createMainImageSlider(self): 
        try:
            self.mainImageSlider = QSlider(Qt.Horizontal)
            self.mainImageSlider.setFocusPolicy(Qt.StrongFocus) # This makes the slider work with arrow keys on Mac OS
            self.mainImageSlider.setToolTip("Use this slider to navigate the series of DICOM images")
            self.mainImageSlider.setSingleStep(1)
            self.mainImageSlider.setTickPosition(QSlider.TicksBothSides)
            self.mainImageSlider.setTickInterval(1)
            self.mainImageSlider.setMinimum(1)
            self.mainImageSlider.valueChanged.connect(self.__mainImageSliderMoved)
        except Exception as e:
            print('Error in ImageSliders.__createMainImageSlider: ' + str(e))
            logger.error('Error in ImageSliders.__createMainImageSlider: ' + str(e))

    
    def __mainImageSliderMoved(self, imageNumber=None):
        """On the Multiple Image Display sub window, this
        function is called when the image slider is moved. 
        It causes the next image in imageList to be displayed
        """
        try: 
            logger.info("ImageSliders.__mainImageSliderMoved called")
            if imageNumber:
                self.mainImageSlider.setValue(imageNumber)
            else:
                imageNumber = self.mainImageSlider.value()
            currentImageNumber = imageNumber - 1
            if currentImageNumber >= 0:
                maxNumberImages = str(len(self.imagePathList))
                imageNumberString = "image {} of {}".format(imageNumber, maxNumberImages)
                self.imageNumberLabel.setText(imageNumberString)
                self.selectedImagePath = self.imagePathList[currentImageNumber]

                #Send the file path of  current image to the parent application
                self.sliderMoved.emit(self.selectedImagePath)

                #SS 31 Aug. Synchronising main and sorted image sliders attempt
                if len(self.listSortedImageSliders)>0:
                    np_array = np.array(self.arrayForMultiSlider)
                    item_index = np.where(np_array == self.selectedImagePath) 
                    if np_array.ndim == 1:
                        firstSliderValue = item_index[0][0]
                        #print("firstSliderValue ={}".format(firstSliderValue))
                        self.listSortedImageSliders[0][0].blockSignals(True)
                        self.listSortedImageSliders[0][0].setValue(firstSliderValue)
                        #Need to update image x of y text for this slider
                        self.listSortedImageSliders[0][0].blockSignals(False)
                    elif np_array.ndim == 2:
                        firstSliderValue = item_index[0][0]
                        secondSliderValue = item_index[1][0]
                        #print("firstSliderValue ={}".format(firstSliderValue))
                        #print("secondSliderValue ={}".format(secondSliderValue))
                        self.listSortedImageSliders[0][0].blockSignals(True)
                        self.listSortedImageSliders[0][0].setValue(firstSliderValue)
                        self.listSortedImageSliders[0][0].blockSignals(False)
                        self.listSortedImageSliders[1][0].blockSignals(True)
                        self.listSortedImageSliders[1][0].setValue(secondSliderValue)
                        self.listSortedImageSliders[1][0].blockSignals(False)
                        #Need to update image x of y text for these sliders

        except TypeError as e: 
            print('Type Error in ImageSliders.__mainImageSliderMoved: ' + str(e))
            logger.error('Type Error in ImageSliders.__mainImageSliderMoved: ' + str(e))
        except Exception as e:
            print('Error in ImageSliders.__mainImageSliderMoved: ' + str(e))
            logger.error('Error in ImageSliders.__mainImageSliderMoved: ' + str(e))


    def __addMainImageSliderToLayout(self):
        """Configures the width of the slider according to the number of images
        it must navigate and adds it and its associated label to the main slider
        layout"""
        try:
            maxNumberImages = len(self.imagePathList)
            self.mainImageSlider.setMaximum(maxNumberImages)
            widthSubWindow = self.weasel.mdiArea.width()
            if maxNumberImages < 4:
                self.mainImageSlider.setFixedWidth(widthSubWindow*.2)
            elif maxNumberImages > 3 and maxNumberImages < 11:
                self.mainImageSlider.setFixedWidth(widthSubWindow*.5)
            else:
                self.mainImageSlider.setFixedWidth(widthSubWindow*.80)
        
            self.imageNumberLabel = QLabel()
        
            if maxNumberImages > 1:
                self.mainSliderLayout.addWidget(self.mainImageSlider)
                self.mainSliderLayout.addWidget(self.imageNumberLabel)
        
            if maxNumberImages < 11:
                self.mainSliderLayout.addStretch(1)
        except Exception as e:
            print('Error in ImageSliders.__addMainImageSliderToLayout: ' + str(e))
            logger.error('Error in ImageSliders.__addMainImageSliderToLayout: ' + str(e))

    
    def __setUpImageTypeList(self):
        self.imageTypeList = self.__createImageTypeList()
        self.imageTypeLayout.addWidget(self.imageTypeList)


    def __createImageTypeList(self):
        try:
            imageTypeList = QListWidget()
            imageTypeList.setFlow(QListView.Flow.LeftToRight)
            imageTypeList.setWrapping(True)
            imageTypeList.setMaximumHeight(25)
            for imageType in listImageTypes:
                # First, check if the DICOM tag exists in the images of the series.
                if ReadDICOM_Image.getImageTagValue(self.selectedImagePath, imageType) is not None:
                    _, numAttr = ReadDICOM_Image.getSeriesTagValues(self.imagePathList, imageType)
                    # Then, check if there's more than 1 unique value for the corresponding DICOM tag
                    if numAttr > 1:
                        item = QListWidgetItem(imageType)
                        item.setToolTip("Tick the check box to create a subset of images based on {}".format(imageType))
                        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                        item.setCheckState(Qt.Unchecked)
                        imageTypeList.addItem(item)
               
            imageTypeList.itemClicked.connect(lambda item: self.__addRemoveSortedImageSlider(item))
            return imageTypeList
        except Exception as e:
            print('Error in ImageSliders.__createImageTypeList: ' + str(e))
            logger.error('Error in ImageSliders.__createImageTypeList: ' + str(e))


    def __addRemoveSortedImageSlider(self, item):
        try:
            if item.checkState() == Qt.Checked:
                #add a slider-label pair
                imageSliderLayout = self.__createSortedImageSlider(item.text()) 
                if imageSliderLayout is not None:
                    self.sortedImageSliderLayout.addRow(item.text(), imageSliderLayout)  
            else:
                #remove a slider-label pair
                for rowNumber in range(0, self.sortedImageSliderLayout.rowCount()):
                    layoutItem = self.sortedImageSliderLayout.itemAt(rowNumber, QFormLayout.LabelRole)
                    if item.text() == layoutItem.widget().text():
                        self.sortedImageSliderLayout.removeRow(rowNumber)
                        self.dynamicListImageType.remove(item.text())
                        for sliderImagePair in self.listSortedImageSliders: 
                            if sliderImagePair[0].attribute == item.text(): 
                                self.listSortedImageSliders.remove(sliderImagePair) 
                        self.shapeList = []
                        if len(self.dynamicListImageType) > 1:
                            # Loop through all the existing sliders at this stage and update the setMaximum of each slider
                            for index, tag in enumerate(self.dynamicListImageType):
                                _, numAttr = ReadDICOM_Image.getSeriesTagValues(self.imagePathList, tag)
                                self.shapeList.append(numAttr)
                                self.sortedImageSliderLayout.itemAt(2*index+1).layout().itemAt(0).widget().setMaximum(numAttr)
                                currentImageNumber = self.sortedImageSliderLayout.itemAt(2*index+1).layout().itemAt(0).widget().value()
                                labelText = "image {} of {}".format(currentImageNumber, numAttr)
                                self.sortedImageSliderLayout.itemAt(2*index+1).layout().itemAt(1).widget().setText(labelText)
                            # Sort according to the tags
                            self.seriesToFormat.sort(*self.dynamicListImageType)
                            # Reshape the self.arrayForMultiSlider list of paths
                            self.arrayForMultiSlider = self.__reshapePathsList()
                        elif len(self.dynamicListImageType) == 1:
                            sortedSequencePath, _, _, _ = ReadDICOM_Image.sortSequenceByTag(self.imagePathList, self.dynamicListImageType[0])
                            self.arrayForMultiSlider = sortedSequencePath
                            self.sortedImageSliderLayout.itemAt(1).layout().itemAt(0).widget().setMaximum(len(sortedSequencePath))
                            currentImageNumber = self.sortedImageSliderLayout.itemAt(1).layout().itemAt(0).widget().value()
                            labelText = "image {} of {}".format(currentImageNumber, len(sortedSequencePath))
                            self.sortedImageSliderLayout.itemAt(1).layout().itemAt(1).widget().setText(labelText)
                        else:
                            self.arrayForMultiSlider = self.imagePathList
                            self.sortedImageSliderLayout.itemAt(1).layout().itemAt(0).widget().setMaximum(len(self.imagePathList)) 
                            currentImageNumber = self.sortedImageSliderLayout.itemAt(1).layout().itemAt(0).widget().value()
                            labelText = "image {} of {}".format(currentImageNumber, len(self.imagePathList))
                            self.sortedImageSliderLayout.itemAt(1).layout().itemAt(1).widget().setText(labelText)
        except Exception as e:
            print('Error in ImageSliders.__addRemoveSortedImageSlider: ' + str(e))
            logger.error('Error in ImageSliders.__addRemoveSortedImageSlider: ' + str(e))


    def __reshapePathsList(self): 
        """This is ann auxiliary function that reshapes the
           list of paths to match the multisliders in the viewer.
        """
        list1 = list(np.arange(np.prod(self.shapeList)).reshape(self.shapeList))
        list2 = self.seriesToFormat.images
        last = 0
        res = []
        for ele in list1:
            res.append(list2[last : last + len(ele)])
            last += len(ele)
        return res


    def __createSortedImageSlider(self, DicomAttribute):  
        try:
            imageSlider = SortedImageSlider(DicomAttribute)
            imageLabel = QLabel()
            layout = QHBoxLayout()
            layout.addWidget(imageSlider)
            layout.addWidget(imageLabel)
            listSliderLabelPair = [imageSlider, imageLabel]
            self.listSortedImageSliders.append(listSliderLabelPair)
            # This makes the slider work with arrow keys on Mac OS
            imageSlider.setFocusPolicy(Qt.StrongFocus) 
            self.dynamicListImageType.append(DicomAttribute)
            # If there is more that 1 slider in the multi-slider layout
            if len(self.dynamicListImageType) > 1:
                # Loop through all the existing sliders at this stage and update the setMaximum of each slider
                self.shapeList = []
                for index, tag in enumerate(self.dynamicListImageType[:-1]):
                    _, numAttr = ReadDICOM_Image.getSeriesTagValues(self.imagePathList, tag)
                    self.shapeList.append(numAttr)
                    self.sortedImageSliderLayout.itemAt(2*index+1).layout().itemAt(0).widget().setMaximum(numAttr)
                    currentImageNumber = self.sortedImageSliderLayout.itemAt(2*index+1).layout().itemAt(0).widget().value()
                    labelText = "image {} of {}".format(currentImageNumber, numAttr)
                    self.sortedImageSliderLayout.itemAt(2*index+1).layout().itemAt(1).widget().setText(labelText)
                _, maxNumberImages = ReadDICOM_Image.getSeriesTagValues(self.imagePathList, DicomAttribute)
                self.shapeList.append(maxNumberImages)
                # Sort according to the tags
                self.seriesToFormat.sort(*self.dynamicListImageType)
                # Reshape the self.arrayForMultiSlider list of paths
                if np.prod(self.shapeList) > len(self.imagePathList):
                    QMessageBox.warning(self.weasel, "Maximum dimension exceeded", "The number of slider combinations exceeds the total number of images in the series")
                    self.listSortedImageSliders.remove(listSliderLabelPair)
                    return None
                else:
                    self.arrayForMultiSlider = self.__reshapePathsList()
            else:
                sortedSequencePath, _, _, _ = ReadDICOM_Image.sortSequenceByTag(self.imagePathList, DicomAttribute)
                maxNumberImages = len(self.imagePathList)
                self.arrayForMultiSlider = sortedSequencePath
                
            imageSlider.setMaximum(maxNumberImages)
            imageSlider.setSingleStep(1)
            imageSlider.setTickPosition(QSlider.TicksBothSides)
            imageSlider.setTickInterval(1)
            imageSlider.setMinimum(1)
            
            imageSlider.valueChanged.connect(self.__multipleImageSliderMoved)
            imageLabel.setText("image 1 of {}".format(maxNumberImages))
            
            return layout
        except Exception as e:
            print('Error in ImageSliders.__createSortedImageSlider: ' + str(e))
            logger.exception('Error in ImageSliders.__createSortedImageSlider: ' + str(e))
    

    def __multipleImageSliderMoved(self):  
        """This function is attached to the slider moved event of each 
        multiple slider.  The slider is identified by the DicomAttribute parameter. 
        The slider being moved determines the image displayed in the image viewer"""
        try:
            indexDict = {}
            #Create a dictionary of DICOM attribute:slider index pairs
            for sliderImagePair in self.listSortedImageSliders:
                #update the text of the image x of y label
                indexDict[sliderImagePair[0].attribute] = sliderImagePair[0].value()
                currentImageNumberThisSlider =  sliderImagePair[0].value()
                maxNumberImagesThisSlider =  sliderImagePair[0].maximum()
                labelText = "image {} of {}".format(currentImageNumberThisSlider, maxNumberImagesThisSlider)
                sliderImagePair[1].setText(labelText)
            # Create a copy of self.arrayForMultiSlider and loop through 
            # indexDict to get the sliders values and map them to self.arrayForMultiSlider
            auxList = copy.copy(self.arrayForMultiSlider)
            for index in indexDict.values():
                auxList = auxList[index - 1]
            self.selectedImagePath = auxList
            self.sliderMoved.emit(self.selectedImagePath)
            
            #update the position of the main slider so that it points to the
            #same image as the sorted image sliders.
            indexImageInMainList = self.imagePathList.index(self.selectedImagePath)
            self.mainImageSlider.setValue(indexImageInMainList+1)
        except Exception as e:
            print('Error in ImageSliders.__multipleImageSliderMoved: ' + str(e))
            logger.exception('Error in ImageSliders.__multipleImageSliderMoved: ' + str(e))
    

    def __setUpSliderResetButton(self):
        self.resetButton = QPushButton("Reset")
        self.resetButton.setToolTip("Return this screen to the state that it had when first opened")
        self.resetButton.clicked.connect(self.__resetSliders)
        self.imageTypeLayout.addWidget(self.resetButton)


    def __resetSliders(self):
        try:
            ##Remove sorted image sliders
            while self.sortedImageSliderLayout.rowCount() > 0:
                rowNumber = self.sortedImageSliderLayout.rowCount() - 1
                self.sortedImageSliderLayout.removeRow(rowNumber)

            #Uncheck all checkboxes in image type list 
            for index in xrange(self.imageTypeList.count()):
                self.imageTypeList.item(index).setCheckState(Qt.Unchecked)
            
            #Reinialise Global variables for the Multisliders
            self.listSortedImageSliders = []
            self.dynamicListImageType = []
            self.shapeList = []
            self.arrayForMultiSlider = self.imagePathList

            #Reset the main image slider
            self.__mainImageSliderMoved(1)
        except Exception as e:
            print('Error in ImageSliders.__resetSliders: ' + str(e))
            logger.error('Error in ImageSliders.__resetSliders: ' + str(e))


    def __imageDeleted(self, newImagePathList):
        try:
            #newImagePathList is the original image file path list
            #but with the file path of the deleted image removed.
            self.imagePathList = newImagePathList
            self.mainImageSlider.setMaximum(len(newImagePathList))
            imageNumber = self.mainImageSlider.value()
            imageIndex = imageNumber - 1
            self.selectedImagePath = self.imagePathList[imageIndex]
            #Send the new current image to the parent application
            self.sliderMoved.emit(self.selectedImagePath)
            
            #To Do 
            #adjust the lists attached to sorted image list sliders
            #by removing the deleted image from the slider if present
            #and calling setMaximum(len(image list)) for each slider

            #if deleted image in self.arrayForMultiSlider
            # remove image from self.arrayForMultiSlider

            if len(self.listSortedImageSliders) > 0:
                print("self.arrayForMultiSlider={}".format(self.arrayForMultiSlider))
            
        except Exception as e:
            print('Error in ImageSliders.__imageDeleted: ' + str(e))
        

            
    