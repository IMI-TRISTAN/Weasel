"""
This class contains functions that read the items selected in the User Interface and return variables that are used in processing pipelines. 

It also contains functions that allow the user to insert inputs and give an update of the pipeline steps through message windows. 
"""

import os
import logging
from PyQt5.QtWidgets import (QMessageBox, QFileDialog)
from Displays.ViewMetaData import DisplayMetaDataSubWindow
from DICOM.DeveloperTools import PixelArrayDICOMTools

logger = logging.getLogger(__name__)

class UserInterfaceTools():
    
    def __repr__(self):
       return '{}'.format(self.__class__.__name__)

    def selectFolder(self, title="Select the directory"):
        """Displays an open folder dialog window to allow the
        user to select afolder """
        scan_directory = QFileDialog.getExistingDirectory(self, title, self.weaselDataFolder, QFileDialog.ShowDirsOnly)
        return scan_directory

    def displayMetadata(self, inputPath):
        """
        Displays the metadata in "inputPath" in the User Interface.
        If "inputPath" is a list, then it displays the metadata of the first image.
        """
        logger.info("UserInterfaceTools.displayMetadata called")
        try:
            if isinstance(inputPath, str) and os.path.exists(inputPath):
                dataset = PixelArrayDICOMTools.getDICOMobject(inputPath)
                displayMetaDataSubWindow(self, "Metadata for image {}".format(inputPath), dataset)
            elif isinstance(inputPath, list) and os.path.exists(inputPath[0]):
                dataset = PixelArrayDICOMTools.getDICOMobject(inputPath[0])
                displayMetaDataSubWindow(self, "Metadata for image {}".format(inputPath[0]), dataset)
        except Exception as e:
            print('Error in function UserInterfaceTools.displayMetadata: ' + str(e))
            logger.exception('Error in UserInterfaceTools.displayMetadata: ' + str(e))

        