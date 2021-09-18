import xml.etree.cElementTree as ET  
from datetime import datetime
import logging
import DICOM.ReadDICOM_Image as ReadDICOM_Image

logger = logging.getLogger(__name__)

__author__ = "Steve Shillitoe"

class WeaselXMLReader:
    """Reads, edits and writes the XML file summarising the DICOM folder.

    > WeaselXMLReader represents the XML file in memory as an ElementTree,
    and uses the ElementTree functionality to edit.
    > WeaselXMLReader ONLY accesses the Messaging API of Weasel; 
    no other weasel attributes or methods are used. 
    > WeaselXMLReader can also be run in command line mode. In that case
    the messages are printed in the terminal.
    """
    def __init__(self, weasel=None): 
        """ Initialise the WeaselXMLReader

        Keyword arguments
        -----------------
        weasel
            Optional argument used for signalling the state of
            calculations to the user using the Weasel Messaging API. 
            If the weasel argument is not provided, 
            messages are printed in the terminal instead. 
        """

        try:
            self.hasXMLFileParsedOK = True
            self.fullFilePath = ""
            self.tree = None 
            self.root = None 
            self.weasel = weasel 

            logger.info('In module ' + __name__ + ' Created XML Reader Object')

        except Exception as e:
            print('Error in WeaselXMLReader.__init__: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.__init__: ' + str(e)) 
            

    def __repr__(self):
       return '{}, {!r}'.format(
           self.__class__.__name__,
           self.fullFilePath)


    def parseXMLFile(self, fullFilePath): 
        """Loads and parses the XML configuration file at fullFilePath.
       After successful parsing, the XML tree and its root node
      is stored in memory."""
        try:
            self.hasXMLFileParsedOK = True
            self.fullFilePath = fullFilePath
            self.tree = ET.parse(fullFilePath)
            self.root = self.tree.getroot()
            return self.root
            # Uncomment to test XML file loaded OK
            #print(ET.tostring(self.root, encoding='utf8').decode('utf8'))
           
            logger.info('In module ' + __name__ 
                    + 'WeaselXMLReader.parseConfigFile ' + fullFilePath)

        except ET.ParseError as et:
            print('WeaselXMLReader.parseConfigFile error: ' + str(et)) 
            logger.error('WeaselXMLReader.parseConfigFile error: ' + str(et))
            self.hasXMLFileParsedOK = False
            
        except Exception as e:
            print('Error in WeaselXMLReader.parseConfigFile: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.parseConfigFile: ' + str(e)) 
            self.hasXMLFileParsedOK = False


    def saveXMLFile(self, filePath=None):
        try:
            if filePath is None:
                filePath = self.fullFilePath
            self.tree.write(filePath)
        except Exception as e:
            print('Error in WeaselXMLReader.saveXMLFile: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.saveXMLFile: ' + str(e))
    

    def getXMLRoot(self):
        return self.root


    def resetXMLTree(self, root):
        """This function uses recursion to set the checked 
        attributes to False

        Input Parameters
        ****************
        root - an element in the XML tree
                """
        try:
            if root.tag == 'image':
                root.attrib['checked'] = 'False'
                return
            for elem in root.getchildren():
                elem.attrib['checked'] = 'False'
                self.resetXMLTree(elem)
        except Exception as e:
            print('Error in WeaselXMLReader.resetXMLTree: ' + str(e))
            logger.error('Error in WeaselXMLReader.resetXMLTree: ' + str(e))


    def getSubjects(self):
        try:
            return self.root.findall('.//subject')
        except Exception as e:
            print('Error in WeaselXMLReader.getSubjects: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getSubjects: ' + str(e))


    def getStudies(self):
        return self.root.findall('.//subject/study')


    def getSubjectList(self):
        try:
            subjects = self.root.findall('.//subject')
            subjectList = [subject.attrib['id'] for subject in subjects]
            return subjectList
        except Exception as e:
            print('Error in WeaselXMLReader.getSubjectList: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getSubjectList: ' + str(e))

    
    def getStudyList(self, subjectID):
        try:
            xPath = './/subject[@id=' + chr(34) + subjectID + chr(34) +  \
                    ']/study'
            studies =  self.root.findall(xPath)
            studyList = [study.attrib['id'] for study in studies]
            return studyList
        except Exception as e:
            print('Error in WeaselXMLReader.getStudyList: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getStudyList: ' + str(e))


    def getSeriesList(self, subjectID, studyID):
        """Returns a list of the names of the non-mask series in specific 
        study in a specific subject"""
        try:
            xPath = './/subject[@id='+ chr(34) + subjectID + chr(34) + \
                    ']/study[@id=' + chr(34) + studyID + chr(34) + \
                    ']/series'        
            series = self.root.findall(xPath)
            seriesList = [singleSeries.attrib['id'] 
                          for singleSeries in series]
            return seriesList
        except Exception as e:
            print('Error in WeaselXMLReader.getNonMaskSeriesList: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getNonMaskSeriesList: ' + str(e))


    def getImageList(self, subjectID, studyID, seriesID):
        """Returns a list of image elements in a specific series"""
        try:
            #print("getImageList: studyID={}, seriesID={}".format(studyID, seriesID))

            xPath = './/subject[@id='+ chr(34) + subjectID + chr(34) + \
                    ']/study[@id=' + chr(34) + studyID + chr(34) + \
                    ']/series[@id=' + chr(34) + seriesID + chr(34) + ']/image'        
            return self.root.findall(xPath)
        except Exception as e:
            print('Error in WeaselXMLReader.getImageList: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getImageList: ' + str(e))


    def getSubject(self, subjectID):
        try:
            xPath = './/subject[@id=' + chr(34) + subjectID + chr(34) + ']'
            #print(xPath)
            return self.root.find(xPath)
        except Exception as e:
            print('Error in WeaselXMLReader.getSubject: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getSubject: ' + str(e))


    def getStudy(self, subjectID, studyID):
        try:
            xPath = './/subject[@id=' + chr(34) + subjectID + chr(34) +  \
                    ']/study[@id=' + chr(34) + studyID + chr(34) + ']'
            #print(xPath)
            return self.root.find(xPath)
        except Exception as e:
            print('Error in WeaselXMLReader.getStudy: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getStudy: ' + str(e))


    def getSeries(self, subjectID, studyID, seriesID):
        try: 
            xPath = './/subject[@id=' + chr(34) + subjectID + chr(34) + ']' \
                    '/study[@id=' + chr(34) + studyID + chr(34) + ']' + \
                    '/series[@id=' + chr(34) + seriesID + chr(34) + ']'
            #print ("get series Xpath = {}".format(xPath))
            return self.root.find(xPath)
        except Exception as e:
            print('Error in WeaselXMLReader.getSeries: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getSeries_: ' + str(e))


    def getImage(self, subjectID, studyID, seriesID, imageName):
        try:
            xPath = './/subject[@id=' + chr(34) + subjectID + chr(34) +  \
                    ']/study[@id=' + chr(34) + studyID + chr(34) + \
                    ']/series[@id=' + chr(34) + seriesID + chr(34)  + \
                    ']/image[name=' + chr(34) + imageName + chr(34) +']'
            return self.root.find(xPath)
        except Exception as e:
            print('Error in WeaselXMLReader.getImage: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getImage: ' + str(e))


    def getImageLabel(self, subjectID, studyID, seriesID, imageName = None):
        try:
            if imageName is None:
                return "000000"
            else:
                xPath = './/subject[@id=' + chr(34) + subjectID + chr(34) +  \
                        ']/study[@id=' + chr(34) + studyID + chr(34) + \
                        ']/series[@id=' + chr(34) + seriesID + chr(34)  + \
                        ']/image[name=' + chr(34) + imageName + chr(34) +']/label'
                return self.root.find(xPath).text
        except Exception as e:
            print('Error in WeaselXMLReader.getImageLabel: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getImageLabel: ' + str(e))


    def getImageTime(self, subjectID, studyID, seriesID, imageName = None):
        try:
            if imageName is None:
                now = datetime.now()
                return now.strftime("%H:%M:%S")
            else:
                xPath = './/subject[@id=' + chr(34) + subjectID + chr(34) +  \
                        ']/study[@id=' + chr(34) + studyID + chr(34) + \
                        ']/series[@id=' + chr(34) + seriesID + chr(34)  + \
                        ']/image[name=' + chr(34) + imageName + chr(34) +']/time'
                return self.root.find(xPath).text
        except Exception as e:
            print('Error in WeaselXMLReader.getImageTime: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getImageTime: ' + str(e))

    
    def getImageDate(self, subjectID, studyID, seriesID, imageName = None):
        try:
            if imageName is None:
                now = datetime.now()
                return now.strftime("%d/%m/%Y") 
            else:
                xPath = './/subject[@id=' + chr(34) + subjectID + chr(34) +  \
                        ']/study[@id=' + chr(34) + studyID + chr(34) + \
                        ']/series[@id=' + chr(34) + seriesID + chr(34)  + \
                        ']/image[name=' + chr(34) + imageName + chr(34) +']/date'
                return self.root.find(xPath).text   
        except Exception as e:
            print('Error in WeaselXMLReader.getImageDate: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getImageDate: ' + str(e))


    def getImagePathList(self, subjectID, studyID, seriesID):
        try:
            xPath = './/subject[@id=' + chr(34) + subjectID + chr(34) +  \
                    ']/study[@id=' + chr(34) + studyID + chr(34) + \
                    ']/series[@id=' + chr(34) + seriesID + chr(34) + ']/image'
            # print(xPath)
            images = self.root.findall(xPath)
            #print("images={}".format(images))
            imageList = [image.find('name').text for image in images]
            #print("length imageList={}".format(len(imageList)))
            return imageList
        except Exception as e:
            print('Error in weaselXMLReader.getImagePathList: ' + str(e))
            logger.error('Error in weaselXMLReader.getImagePathList: ' + str(e))
    

    def getImageParentIDs(self, imageName):
        try:
            xPathSubject = './/subject/study/series/image[name=' + chr(34) + imageName + chr(34) +']/../../..'
            if self.root.find(xPathSubject):
                subjectID = self.root.find(xPathSubject).attrib['id']
            else:
                subjectID = None
            xPathStudy = './/subject/study/series/image[name=' + chr(34) + imageName + chr(34) +']/../..'
            if self.root.find(xPathStudy):
                studyID = self.root.find(xPathStudy).attrib['id']
            else:
                studyID = None
            xPathSeries = './/subject/study/series/image[name=' + chr(34) + imageName + chr(34) +']/..'
            if self.root.find(xPathSeries):
                seriesID = self.root.find(xPathSeries).attrib['id']
            else:
                seriesID = None
            return (subjectID, studyID, seriesID)
        except Exception as e:
            print('Error in WeaselXMLReader.getImageParentIDs: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.getImageParentIDs: ' + str(e))


    def objectID(self, elem):
        """Returns the ID as currently used within weasel as a list"""
        
        if elem in self.root: # elem is a subject
            return [elem.attrib['id']]
        else:
            for subject in self.root:
                if elem in subject: # elem is a study
                    return [subject.attrib['id'], elem.attrib['id']]
                else:
                    for study in subject:
                        if elem in study: # elem is a series
                            return [subject.attrib['id'], study.attrib['id'], elem.attrib['id']]
                        else:
                            for series in study:
                                if elem in series: # elem is an image
                                    return [subject.attrib['id'], study.attrib['id'], series.attrib['id'], elem.find('name').text]


    def branch(self, elem):
        """Returns the parents of the current element"""
        
        if elem in self.root: # elem is a subject
            return [elem]
        else:
            for subject in self.root:
                if elem in subject: # elem is a study
                    return [subject, elem]
                else:
                    for study in subject:
                        if elem in study: # elem is a series
                            return [subject, study, elem]
                        else:
                            for series in study:
                                if elem in series: # elem is an image
                                    return [subject, study, series, elem]


    def buildListsCheckedItems(self):
        """This function generates and returns lists of checked items."""

        logger.info("WeaselXMLReader.buildListsCheckedItems called")
        try:
            checkedImageList = []
            checkedSeriesList = []
            checkedStudyList = []
            checkedSubjectList = []
            for subject in self.root:
                if subject.attrib['checked'] == 'True':
                    checkedSubjectList.append(subject)
                for study in subject:
                    if study.attrib['checked'] == 'True':
                        checkedStudyList.append(study)
                    for series in study:
                        if series.attrib['checked'] == 'True':
                            checkedSeriesList.append(series)
                        for image in series:
                            if image.attrib['checked'] == 'True':
                                checkedImageList.append(image)
            return checkedImageList, checkedSeriesList, checkedStudyList, checkedSubjectList
        except Exception as e:
            print('Error in WeaselXMLReader.buildListsCheckedItems: ' + str(e))
            logger.exception('Error in WeaselXMLReader.buildListsCheckedItems: ' + str(e))


    @property
    def checkedImageList(self):
        images, _, _, _ = self.buildListsCheckedItems()
        return images

    @property
    def checkedSeriesList(self):
        _, series, _, _ = self.buildListsCheckedItems()
        return series

    @property
    def checkedStudyList(self):
        _, _, studies, _ = self.buildListsCheckedItems()
        return studies

    @property
    def checkedSubjectList(self):
        _, _, _, subjects = self.buildListsCheckedItems()
        return subjects


    def removeSubjectFromXMLFile(self, subjectID):
        """Removes a subject from the DICOM XML file"""
        try:
            logger.info("WeaselXMLReader removeSubjectFromXMLFile called")
            subject = self.getSubject(subjectID)
            if subject:
                self.root.remove(subject)
            else:
                print("Unable to remove subject {}".format(subjectID))
        except Exception as e:
            print('Error in WeaselXMLReader removeSubjectFromXMLFile: ' + str(e))
            logger.error('Error in WeaselXMLReader removeSubjectFromXMLFile: ' + str(e))


    def removeOneStudyFromXMLFile(self, subjectID, studyID):
        """Removes a whole study from the DICOM XML file"""
        try:
            logger.info("weaseXMLReader.removeOneStudyFromSubject called")
            subject = self.getSubject(subjectID)
            study = self.getStudy(subjectID, studyID)
            if study and subject:
                subject.remove(study)
            else:
                print("Unable to remove study {}".format(studyID))
        except AttributeError as e:
            print('Attribute Error in weaseXMLReader.removeOneStudyFromSubject : ' + str(e))
            logger.error('Attribute Error in weaseXMLReader.removeOneStudyFromSubject: ' + str(e))
        except Exception as e:
            print('Error in weaseXMLReader.removeOneStudyFromSubject : ' + str(e))
            logger.error('Error in weaseXMLReader.removeOneStudyFromSubject: ' + str(e))


    def removeOneSeriesFromXMLFile(self, subjectID, studyID, seriesID):
        """Removes a whole series from the DICOM XML file"""
        try:
            logger.info("weaseXMLReader.removeOneSeriesFromStudy called")
            study = self.getStudy(subjectID, studyID)
            series = self.getSeries(subjectID, studyID, seriesID)
            if study and series:
                study.remove(series)
            else:
                print("Unable to remove series {}".format(seriesID))
        except AttributeError as e:
            print('Attribute Error in weaseXMLReader.removeOneSeriesFromStudy : ' + str(e))
            logger.error('Attribute Error in weaseXMLReader.removeOneSeriesFromStudy: ' + str(e))
        except Exception as e:
            print('Error in weaseXMLReader.removeOneSeriesFromStudy : ' + str(e))
            logger.error('Error in weaseXMLReader.removeOneSeriesFromStudy: ' + str(e))


    def removeOneImageFromSeries(self, subjectID, studyID, seriesID, imagePath):
        try:
            series = self.getSeries(subjectID, studyID, seriesID)
            if series:
                for image in series:
                    if image.find('name').text == imagePath:
                        series.remove(image)
                        break
        except Exception as e:
            print('Error in WeaselXMLReader.removeOneImageFromSeries: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.removeOneImageFromSeries: ' + str(e))


    def removeOneStudyFromSubject(self, subjectID, studyID):
        """Removes a study from the given subject from the DICOM XML file"""
        try:
            logger.info("WeaselXMLReader removeOneStudyFromSubject called")
            studiesList = self.getSubject(subjectID)
            if len(studiesList) == 1:
                self.removeSubjectFromXMLFile(subjectID)
            elif len(studiesList) > 1:
                self.removeOneStudyFromXMLFile(subjectID, studyID)
        except Exception as e:
            print('Error in WeaselXMLReader removeOneStudyFromSubject: ' + str(e))
            logger.error('Error in WeaselXMLReader removeOneStudyFromSubject: ' + str(e))


    def removeOneSeriesFromStudy(self, subjectID, studyID, seriesID):
        """Removes a whole series from the DICOM XML file"""
        try:
            logger.info("WeaselXMLReader removeOneSeriesFromStudy called")
            seriesList = self.getStudy(subjectID, studyID)
            if len(seriesList) == 1:
                self.removeOneStudyFromSubject(subjectID, studyID)
            elif len(seriesList) > 1:
                self.removeOneSeriesFromXMLFile(subjectID, studyID, seriesID)
        except Exception as e:
            print('Error in WeaselXMLReader removeOneSeriesFromStudy: ' + str(e))
            logger.error('Error in WeaselXMLReader removeOneSeriesFromStudy: ' + str(e))


    def removeImageFromXMLFile(self, imageFileName):
        """Removes an image from the DICOM XML file"""
        try:
            logger.info("WeaselXMLReader removeImageFromXMLFile called")
            (subjectID, studyID, seriesID) = self.getImageParentIDs(imageFileName)
            images = self.getImageList(subjectID, studyID, seriesID)
            if len(images) == 1:
                self.removeOneSeriesFromStudy(subjectID, studyID, seriesID)
            elif len(images) > 1:
                self.removeOneImageFromSeries(subjectID, studyID, seriesID, imageFileName)
        except Exception as e:
            print('Error in WeaselXMLReader removeImageFromXMLFile: ' + str(e))
            logger.error('Error in WeaselXMLReader removeImageFromXMLFile: ' + str(e))


    def removeMultipleImagesFromXMLFile(self, origImageList):
        """Removes a list of images from the DICOM XML file"""
        try:
            logger.info("WeaselXMLReader removeMultipleImagesFromXMLFile called")
            for image in origImageList:
                self.removeImageFromXMLFile(image)
        except Exception as e:
            print('Error in WeaselXMLReader removeMultipleImagesFromXMLFile: ' + str(e))
            logger.error('Error in WeaselXMLReader removeMultipleImagesFromXMLFile: ' + str(e))


    def moveImageInXMLFile(self, subjectID, studyID, seriesID, newSubjectID, newStudyID, newSeriesID, imageName, suffix):
        try:
            self.insertNewImageInXML(imageName, imageName, newSubjectID, newStudyID, newSeriesID, suffix)
            images = self.getImageList(subjectID, studyID, seriesID)
            if len(images) == 1:
                self.removeOneSeriesFromStudy(subjectID, studyID, seriesID)
            elif len(images) > 1:
                self.removeOneImageFromSeries(subjectID, studyID, seriesID, imageName)
        except Exception as e:
            print('Error in InterfaceDICOMXMLFile.moveImageInXMLFile: ' + str(e)) 
            logger.error('Error in InterfaceDICOMXMLFile.moveImageInXMLFile: ' + str(e))


    def insertNewStudyInXMLFile(self, subjectID, newStudyID, suffix, seriesList=[], newSubjectName=None):
        """Creates a new study to hold the new series"""
        try:
            logger.info("WeaselXMLReader insertNewStudyInXMLFile called")
            if newSubjectName is not None: subjectID = newSubjectName
            self.insertNewStudyinXML(seriesList, subjectID, newStudyID, suffix)
            if self.weasel is None:
                print('New study created: - ' + newStudyID)
            else:
                self.weasel.set_status('New study created: - ' + newStudyID)
            return newStudyID
        except Exception as e:
            print('Error in WeaselXMLReader.insertNewStudyInXMLFile: ' + str(e))
            logger.error('Error in WeaselXMLReader.insertNewStudyInXMLFile: ' + str(e))


    def insertNewSeriesInXMLFile(self, origImageList, newImageList, suffix, newSeriesName=None, newStudyName=None, newSubjectName=None):
        """Creates a new series to hold the series of New images"""
        try:
            logger.info("InterfaceDICOMXMLFile insertNewSeriesInXMLFile called")
            (subjectID, studyID, seriesID) = self.getImageParentIDs(origImageList[0])
            dataset = ReadDICOM_Image.getDicomDataset(newImageList[0])
            if newStudyName is not None: studyID = str(dataset.StudyDate) + "_" + str(dataset.StudyTime).split(".")[0] + "_" + newStudyName
            if newSubjectName is not None: subjectID = newSubjectName
            newSeriesID = self.getNewSeriesName(subjectID, studyID, dataset, suffix, newSeriesName=newSeriesName) # If developer sets seriesName
            self.insertNewSeriesInXML(origImageList, 
                        newImageList, subjectID, studyID, newSeriesID, seriesID, suffix)
            if self.weasel is None:
                print('New series created: - ' + newSeriesID)
            else:
                self.weasel.set_status('New series created: - ' + newSeriesID)
            return newSeriesID
        except Exception as e:
            print('Error in WeaselXMLReader.insertNewSeriesInXMLFile: ' + str(e))
            logger.error('Error in WeaselXMLReader.insertNewSeriesInXMLFile: ' + str(e))


    def insertNewImageInXMLFile(self, imagePath, newImageFileName, suffix, newSeriesName=None, newStudyName=None, newSubjectName=None):
        """This function inserts information regarding a new image 
        in the DICOM XML file
        """
        try:
            logger.info("InterfaceDICOMXMLFile insertNewImageInXMLFile called")
            (subjectID, studyID, seriesID) = self.getImageParentIDs(imagePath)
            return self.insertNewImageInXML(imagePath,
                newImageFileName, subjectID, studyID, seriesID, suffix, newSeriesName=newSeriesName, newStudyName=newStudyName, newSubjectName=newSubjectName)
        except Exception as e:
            print('Error in insertNewImageInXMLFile: ' + str(e))
            logger.error('Error in insertNewImageInXMLFile: ' + str(e))


    def insertNewSubjectinXML(self, newStudiesList, newSubjectID, suffix):
        newAttributes = {'id':newSubjectID, 
                         'typeID':suffix,
                         'checked': 'False'}
        #Add new subject to project
        newSubject = ET.SubElement(self.root, 'subject', newAttributes)
        for newStudy in newStudiesList:
            dataset = ReadDICOM_Image.getDicomDataset(newStudy[0][0])
            newStudyID = str(dataset.StudyDate) + "_" + str(dataset.StudyTime).split(".")[0] + "_" + str(dataset.StudyDescription)
            self.insertNewStudyinXML(newStudy, newSubjectID, newStudyID, '')


    def insertNewStudyinXML(self, newSeriesList, subjectID, newStudyID, suffix):
        """
        newSeriesList: This is a list of lists. Each nested list is a set of filenames belonging to same series.
        """
        try:
            dataset = ReadDICOM_Image.getDicomDataset(newSeriesList[0][0])
            currentSubject = self.getSubject(subjectID)
            newAttributes = {'id':newStudyID, 
                             'typeID':suffix,
                             'uid':str(dataset.StudyInstanceUID),
                             'checked': 'False'}

            if currentSubject is not None:
                #Add new study to subject to hold new series+images
                newStudy = ET.SubElement(currentSubject, 'study', newAttributes)
                for newSeries in newSeriesList:
                    dataset = ReadDICOM_Image.getDicomDataset(newSeries[0])
                    newSeriesID = str(dataset.SeriesNumber) + "_" + str(dataset.SeriesDescription)
                    self.insertNewSeriesInXML(newSeries, newSeries, subjectID, newStudyID, newSeriesID, newSeriesID, suffix)
            else:
                self.insertNewSubjectinXML([newSeriesList], subjectID, suffix)
                #self.insertNewSubjectinXML([newSeriesList], subjectID, '')
                #self.insertNewStudyinXML(newSeriesList, subjectID, newStudyID, suffix)
        except Exception as e:
            print('Error in WeaselXMLReader.insertNewStudyInXML: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.insertNewStduyInXML: ' + str(e))


    def insertNewSeriesInXML(self, origImageList, newImageList, subjectID,
                     studyID, newSeriesID, seriesID, suffix):
        try:
            dataset = ReadDICOM_Image.getDicomDataset(newImageList[0])
            currentStudy = self.getStudy(subjectID, studyID)
            newAttributes = {'id':newSeriesID, 
                             'typeID':suffix,
                             'uid':str(dataset.SeriesInstanceUID),
                             'checked': 'False'}

            if currentStudy is not None:
                #Add new series to study to hold new images
                newSeries = ET.SubElement(currentStudy, 'series', newAttributes)
                #Get image date & time from original image
                for index, imageNewName in enumerate(newImageList):
                    subjectID_Original, studyID_Original, seriesID_Original = self.getImageParentIDs(origImageList[index])
                    if subjectID_Original is None or studyID_Original is None or seriesID_Original is None:
                        imageLabel = str(index + 1).zfill(6) # + suffix
                    else:
                        imageLabel = str(ReadDICOM_Image.getImageTagValue(newImageList[index], 'InstanceNumber')).zfill(6)
                        #imageLabel = self.getImageLabel(subjectID_Original, studyID_Original, seriesID_Original, origImageList[index])
                    imageTime = self.getImageTime(subjectID, studyID, seriesID)
                    imageDate = self.getImageDate(subjectID, studyID, seriesID)
                    newAttributes = {'checked':'False'}
                    newImage = ET.SubElement(newSeries,'image', newAttributes)
                    #Add child nodes of the image element
                    labelNewImage = ET.SubElement(newImage, 'label')
                    #labelNewImage.text = str(index + 1).zfill(6)
                    labelNewImage.text = imageLabel # + suffix
                    nameNewImage = ET.SubElement(newImage, 'name')
                    nameNewImage.text = imageNewName
                    timeNewImage = ET.SubElement(newImage, 'time')
                    timeNewImage.text = imageTime
                    dateNewImage = ET.SubElement(newImage, 'date')
                    dateNewImage.text = imageDate
            else:
                self.insertNewStudyinXML([newImageList], subjectID, studyID, suffix)
                #self.insertNewStudyinXML([[]], subjectID, studyID, '')
                #self.insertNewSeriesInXML(origImageList, newImageList, subjectID, studyID, newSeriesID, seriesID, suffix)
        except Exception as e:
            print('Error in WeaselXMLReader.insertNewSeriesInXML: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.insertNewSeriesInXML: ' + str(e))

  
    def insertNewImageInXML(self, imageName, newImageFileName, subjectID, studyID, seriesID, suffix, 
                            newSeriesName=None, newStudyName=None, newSubjectName=None):
        try:
            dataset = ReadDICOM_Image.getDicomDataset(newImageFileName)
            if newSeriesName:
                newSeriesID = str(dataset.SeriesNumber) + "_" + newSeriesName
            else:
                if hasattr(dataset, "SeriesDescription"):
                    newSeriesID = str(dataset.SeriesNumber) + "_" + dataset.SeriesDescription
                elif hasattr(dataset, "SequenceName"):
                    newSeriesID = str(dataset.SeriesNumber) + "_" + dataset.SequenceName
                elif hasattr(dataset, "ProtocolName"):
                    newSeriesID = str(dataset.SeriesNumber) + "_" + dataset.ProtocolName
                else:
                    newSeriesID = str(dataset.SeriesNumber) + "_" + "No Sequence Name"
            # Check if the newSeries exists or not
            series = self.getSeries(subjectID, studyID, newSeriesID)
            #Get image label, date & time of Original image in case it's needed.
            subjectID_Original, studyID_Original, seriesID_Original = self.getImageParentIDs(imageName)
            if subjectID_Original is None or studyID_Original is None or seriesID_Original is None:
                imageLabel = self.getImageLabel(subjectID_Original, studyID_Original, seriesID_Original)
            else:
                imageLabel = str(ReadDICOM_Image.getImageTagValue(newImageFileName, 'InstanceNumber')).zfill(6)
                #imageLabel = self.getImageLabel(subjectID_Original, studyID_Original, seriesID_Original, imageName)
            imageTime = self.getImageTime(subjectID, studyID, seriesID)
            imageDate = self.getImageDate(subjectID, studyID, seriesID)
            if series is None:
                #Need to create a new series to hold this new image
                #Get study branch
                currentStudy = self.getStudy(subjectID, studyID)
                if currentStudy is None:
                    currentSubject = self.getSubject(subjectID)
                    if currentSubject is None:
                        if newSubjectName:
                            newSubjectID = newSubjectName
                        else:
                            newSubjectID = str(dataset.PatientID)
                        self.insertNewSubjectinXML([[[newImageFileName]]], newSubjectID, '')
                        return newSeriesID
                    else:
                        newSubjectID = subjectID
                        if newStudyName:
                            newStudyID = str(dataset.StudyDate) + "_" + str(dataset.StudyTime).split(".")[0] + "_" + newStudyName
                        else:
                            newStudyID = str(dataset.StudyDate) + "_" + str(dataset.StudyTime).split(".")[0] + "_" + str(dataset.StudyDescription)
                        self.insertNewStudyinXML([[newImageFileName]], newSubjectID, newStudyID, '')
                        return newSeriesID
                    #currentStudy = self.getStudy(newSubjectID, newStudyID)
                newAttributes = {'id':newSeriesID, 
                                 'typeID':suffix,
                                 'uid':str(dataset.SeriesInstanceUID),
                                 'checked':'False'}

                #Add new series to study to hold new images
                newSeries = ET.SubElement(currentStudy, 'series', newAttributes)     
                #print("image time {}, date {}".format(imageTime, imageDate))
                #Now add image element
                newAttributes = {'checked':'False'}
                newImage = ET.SubElement(newSeries, 'image', newAttributes)
                #Add child nodes of the image element
                labelNewImage = ET.SubElement(newImage, 'label')
                labelNewImage.text = imageLabel # + suffix
                #labelNewImage.text = "000001"
                nameNewImage = ET.SubElement(newImage, 'name')
                nameNewImage.text = newImageFileName
                timeNewImage = ET.SubElement(newImage, 'time')
                timeNewImage.text = imageTime
                dateNewImage = ET.SubElement(newImage, 'date')
                dateNewImage.text = imageDate
                return newSeriesID
            else:
                #A series already exists to hold new images from
                #the current parent series
                newAttributes = {'checked':'False'}
                newImage = ET.SubElement(series, 'image', newAttributes)
                #Add child nodes of the image element
                labelNewImage = ET.SubElement(newImage, 'label')
                #imageLabel = self.getImageLabel(subjectID, studyID, seriesID, imageName)
                labelNewImage.text = imageLabel # + suffix
                #labelNewImage.text = str(len(series)).zfill(6)
                nameNewImage = ET.SubElement(newImage, 'name')
                nameNewImage.text = newImageFileName
                timeNewImage = ET.SubElement(newImage, 'time')
                timeNewImage.text = imageTime
                dateNewImage = ET.SubElement(newImage, 'date')
                dateNewImage.text = imageDate
                return series.attrib['id']
        except Exception as e:
            print('Error in WeaselXMLReader.insertNewImageInXML: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.insertNewImageInXML: ' + str(e))


    def renameSubjectInXMLFile(self, subjectID, xmlSubjectName):
        try:
            subject = self.getSubject(subjectID)
            subject.attrib['id'] = xmlSubjectName
        except Exception as e:
            print('Error in WeaselXMLReader.renameSubjectInXMLFile: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.renameSubjectInXMLFile: ' + str(e))


    def renameStudyInXMLFile(self, subjectID, studyID, xmlStudyName):
        try:
            study = self.getStudy(subjectID, studyID)
            study.attrib['id'] = xmlStudyName
        except Exception as e:
            print('Error in WeaselXMLReader.renameStudyInXMLFile: ' + str(e)) 
            logger.error('Error in WeaselXMLReader.renameStudyInXMLFile: ' + str(e))


    def renameSeriesinXMLFile(self, imageList, series_id=None, series_name=None):
        """Renames a whole series in the DICOM XML file"""
        try:
            logger.info("InterfaceDICOMXMLFile renameSeriesinXMLFile called")
            (subjectID, studyID, seriesID) = self.getImageParentIDs(imageList[0])
            seriesNumber = str(ReadDICOM_Image.getDicomDataset(imageList[0]).SeriesNumber) if series_id is None else str(series_id)
            try:
                newName = str(ReadDICOM_Image.getDicomDataset(imageList[0]).SeriesDescription) if series_name is None else str(series_name)
            except:
                try:
                    newName = str(ReadDICOM_Image.getDicomDataset(imageList[0]).SequenceName) if series_name is None else str(series_name)
                except:
                    newName = str(ReadDICOM_Image.getDicomDataset(imageList[0]).ProtocolName) if series_name is None else str(series_name)
            xmlSeriesName = seriesNumber + "_" + newName
            self.getSeries(subjectID, studyID, seriesID).attrib['id'] = xmlSeriesName
        except Exception as e:
            print('Error in InterfaceDICOMXMLFile removeOneSeriesFromStudy: ' + str(e))
            logger.error('Error in InterfaceDICOMXMLFile removeOneSeriesFromStudy: ' + str(e))


    def getNewSeriesName(self, subjectID, studyID, dataset, suffix, newSeriesName=None):
        """This function uses recursion to find the next available
        series name.  A new series name is created by adding a suffix
        at the end of an existing series name. """
        try:
            # Swapped SeriesNumber with SeriesDescription
            if newSeriesName:
                seriesID = str(dataset.SeriesNumber) + "_" + newSeriesName
            else:
                if hasattr(dataset, "SeriesDescription"):
                    seriesID = str(dataset.SeriesNumber) + "_" + dataset.SeriesDescription
                elif hasattr(dataset, "SequenceName"):
                    seriesID = str(dataset.SeriesNumber) + "_" + dataset.SequenceName
                elif hasattr(dataset, "ProtocolName"):
                    seriesID = str(dataset.SeriesNumber) + "_" + dataset.ProtocolName
            imageList = self.getImageList(subjectID, studyID, seriesID)
            if imageList:
                #A series of images already exists 
                #for the series called seriesID
                #so make another new series ID 
                #by adding the suffix to the previous
                #new series ID
                if newSeriesName:
                    dataset.SeriesDescription = newSeriesName
                    return self.getNewSeriesName(subjectID, studyID, dataset, suffix, newSeriesName=None)
                else:
                    if hasattr(dataset, "SeriesDescription"):
                        dataset.SeriesDescription = dataset.SeriesDescription + suffix
                    elif hasattr(dataset, "SequenceName"):
                        dataset.SequenceName = dataset.SequenceName + suffix
                    elif hasattr(dataset, "ProtocolName"):
                        dataset.ProtocolName = dataset.ProtocolName + suffix
                    return self.getNewSeriesName(subjectID, studyID, dataset, suffix)
            else:
                logger.info("WeaselXMLReader getNewSeriesName returns seriesID {}".format(seriesID))
                return seriesID
        except Exception as e:
            print('Error in WeaselXMLReader.getNewSeriesName: ' + str(e))


    
