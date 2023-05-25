"""
The medical image classes are defined in this module:

    - ImagesList
    - SeriesList
    - StudyList
    - SubjectList
    - Project
    - Subject
    - Study
    - Series
    - Image

The functions and attributes that compose these classes make use of functions defined in `ReadDICOM_Image.py`, `SaveDICOM_Image.py`, `DeveloperTools.py`, `CoreModules.TreeView.py` and `CoreModules.WeaselXMLReader.py`. There are also some applications of the API module using the global Weasel variable.
"""

import os
import datetime
import numpy as np
import random
import pydicom
import nibabel as nib
import pandas as pd
import copy
from ast import literal_eval # Convert strings to their actual content. Eg. "[a, b]" becomes the actual list [a, b]
from DICOM.DeveloperTools import (PixelArrayDICOMTools, GenericDICOMTools)
import DICOM.ReadDICOM_Image as ReadDICOM_Image
import DICOM.SaveDICOM_Image as SaveDICOM_Image

import logging
logger = logging.getLogger(__name__)

class ListOfDicomObjects(list):
    """
    A superclass for managing Lists of Subjects, Studies, Series or Images. 
    """
    def delete(self):
        """
        Deletes all items in the list
        """
        for item in self:
            item.delete()

    def display(self):
        """
        Displays all items in the list.
        """
        for item in self:
            item.objWeasel.display(item)


class ImagesList(ListOfDicomObjects):
    """
    A class containing a list of objects of class Image. 
    """
    @property
    def label(self):
        """
        Returns a list of names of the list of images.
        """
        listNames = [image.label for image in self]
        return listNames

    @property
    def paths(self):
        """
        Returns a list of file paths of the list of images.
        """
        listPaths = [image.path for image in self]
        return listPaths

    def copy(self):
        """
        Returns a copy of the list of images.
        """
        copy = []
        for image in self:
            copy.append(image.copy())
        return ImagesList(copy)
        
    def merge(self, series_number=None,series_name='MergedSeries', study_name=None, patient_name=None, overwrite=True, progress_bar=True):
        """
        Merges a list of images into a new series under the same study
        """
        if len(self) == 0: return
        return self[0].merge(self, series_id=series_number, series_name=series_name, study_name=study_name, patient_id=patient_name, overwrite=overwrite, progress_bar=progress_bar)

    def new_parent(self, suffix="_Suffix"):
        """
        Creates a new parent series from the images in the list.
        """
        return self[0].newSeriesFrom(self, suffix=suffix)

    @property
    def parent(self):
        """
        Returns a list of unique series to which the images belong to.
        """
        parentsList = []
        listParentsAttribute = []
        for image in self:
            series = image.parent
            listIndividualAttributes = [series.subjectID, series.studyID, series.seriesID,
                                        series.images, series.studyUID, series.seriesUID, series.suffix]
            listParentsAttribute.append(listIndividualAttributes)
        listUniqueParentsAttribute = self[0].objWeasel.unique_elements(listParentsAttribute)
        for listAtt in listUniqueParentsAttribute:
            series = Series(self[0].objWeasel, listAtt[0], listAtt[1], listAtt[2], listAtt[3], listAtt[4], listAtt[5], listAtt[6])
            parentsList.append(series)
        return SeriesList(parentsList)


    def display(self):
        """
        Displays all images as a series.
        """
        self[0].objWeasel.display(self)


    def sort(self, *argv, reverse=False):
        """
        Sort the list of images by the given DICOM tags.
        """
        tuple_to_sort = []
        list_to_sort = []
        list_to_sort.append(self)
        for tag in argv:
            if len(self.get_value(tag)) > 0:
                attributeList = self.get_value(tag)
                list_to_sort.append(attributeList)
        for index, _ in enumerate(self):
            individual_tuple = []
            for individual_list in list_to_sort:
                individual_tuple.append(individual_list[index])
            tuple_to_sort.append(tuple(individual_tuple))
        tuple_sorted = sorted(tuple_to_sort, key=lambda x: x[1:], reverse=reverse)
        list_sorted_images = []
        for individual in tuple_sorted:
            list_sorted_images.append(individual[0])
        self = ImagesList(list_sorted_images)
        return self

    def where(self, tag, condition, target):
        list_images = []
        for image in self:
            value = image[tag]
            if condition == "==":
                statement = 'str(' + repr(value) + ') ' + condition + ' str(' + repr(target) + ')'
                if eval(statement) == True:
                    list_images.append(image)
            else:
                statement = repr(value) + ' ' + repr(condition) + ' ' + repr(target)
                if eval(literal_eval(statement)) == True:
                    list_images.append(image)
        self = ImagesList(list_images)
        return self

    def get_value(self, tag):
        """
        Returns a list of values of the given DICOM tag in the list of images
        """
        attributes_list = []
        for image in self:
            attributes_list.append(image.get_value(tag))
        return attributes_list

    def set_value(self, tag, value):
        """
        Set the variable "value" to the given DICOM tag in the list of images
        """
        if isinstance(value, list) and len(self) == len(value):
            for index, image in enumerate(self):
                image.set_value(tag, value[index])
        else:
            for image in self:
                image.set_value(tag, value)
    
    def __getitem__(self, tag):
        if isinstance(tag, int):
            for index, image in enumerate(self):
                if index == tag:
                    return image
        else:
            return self.get_value(tag)

    def __setitem__(self, tag, value):
        if isinstance(tag, str) and len(tag.split(' ')) == 3:
            dicom_tag = tag.split(' ')[0]
            logical_operator = tag.split(' ')[1]
            target_value = tag.split(' ')[2]
            listImages = self.where(dicom_tag, logical_operator, target_value)
            listImages.set_value(dicom_tag, value)
        elif isinstance(tag, str):
            self.set_value(tag, value)
        elif isinstance(tag, int) and isinstance(value, Image):
            newList = []
            for index, image in enumerate(self):
                if index == tag:
                    newList.append(value)
                else:
                    newList.append(image)
            self = newList
            #self[tag] = value
        elif isinstance(tag, list) and isinstance(value, list):
            for index, dicom_tag in enumerate(tag):
                self.set_value(dicom_tag, value[index])


class SeriesList(ListOfDicomObjects):
    """
    A class containing a list of class Series. 
    """  
    def copy(self):
        """
        Returns a copy of the list of series.
        """
        copy = []
        for series in self:
            copy.append(series.copy())
        return SeriesList(copy)

    def merge(self, series_name='MergedSeries', study_name=None, patient_name=None, overwrite=True, progress_bar=True):
        """
        Merges a list of series into a new series under the same study
        """
        if len(self) == 0: return
        return self[0].merge(self, series_name=series_name, study_name=study_name, patient_id=patient_name, overwrite=overwrite, progress_bar=progress_bar)  

    @property
    def parent(self):
        """
        Returns a list of unique studies to which the series belong to.
        """
        parentsList = []
        listParentsAttribute = []
        for series in self:
            study = series.parent
            listIndividualAttributes = [study.subjectID, study.studyID, study.studyUID, study.suffix]
            listParentsAttribute.append(listIndividualAttributes)
        listUniqueParentsAttribute = self[0].objWeasel.unique_elements(listParentsAttribute)
        for listAtt in listUniqueParentsAttribute:
            study = Study(self[0].objWeasel, listAtt[0], listAtt[1], listAtt[2], listAtt[3])
            parentsList.append(study)
        return StudyList(parentsList)

    @property
    def children(self):
        """
        Returns a list of lists of images where each list refers to the various images of a series.
        """
        childrenList = []
        for series in self:
            # We're returning list of lists by using append.
            # If we want a flat list, we'll have to use extend instead.
            childrenList.append(series.children)
        return childrenList


class StudyList(ListOfDicomObjects):
    """
    A class containing a list of class Study. 
    """
    def copy(self):
        """
        Returns a copy of the list of studies.
        """
        copy = []
        for study in self:
            copy.append(study.copy())
        return StudyList(copy)

    def merge(self, study_name='MergedStudies', overwrite=True, progress_bar=True):
        """
        Merges a list of series into a new series under the same study
        """
        if len(self) == 0: return
        return self[0].merge(self, newStudyName=study_name, overwrite=overwrite, progress_bar=progress_bar)

    @property
    def parent(self):
        """
        Returns a list of unique subjects to which the studies belong to.
        """
        parentsList = []
        listParentsAttribute = []
        for study in self:
            subject = study.parent
            listIndividualAttributes = [subject.subjectID, subject.suffix]
            listParentsAttribute.append(listIndividualAttributes)
        listUniqueParentsAttribute = self[0].objWeasel.unique_elements(listParentsAttribute)
        for listAtt in listUniqueParentsAttribute:
            subject = Subject(self[0].objWeasel, listAtt[0], listAtt[1])
            parentsList.append(subject)
        return SubjectList(parentsList)

    @property
    def children(self):
        """
        Returns a list of lists of series where each list refers to the various series of a study.
        """
        childrenList = []
        for study in self:
            # We're returning list of lists by using append.
            # If we want a flat list, we'll have to use extend instead.
            childrenList.append(study.children)
        return childrenList


class SubjectList(ListOfDicomObjects):
    """
    A class containing a list of class Subject. 
    """
    def copy(self):
        """
        Returns a copy of the list of subjects.
        """
        copy = []
        for subject in self:
            copy.append(subject.copy())
        return SubjectList(copy)

    def merge(self, subject_name='MergedSubjects', overwrite=True, progress_bar=True):
        """
        Merges a list of series into a new series under the same study
        """
        if len(self) == 0: return
        return self[0].merge(self, newSubjectName=subject_name, overwrite=overwrite, progress_bar=progress_bar)

    @property
    def children(self):
        """
        Returns a list of lists of series where each list refers to the various series of a study.
        """
        childrenList = []
        for subject in self:
            # We're returning list of lists by using append.
            # If we want a flat list, we'll have to use extend instead.
            childrenList.append(subject.subject)
        return childrenList

class Project:
    """This class is the top-level of the TreeView hierarchy. It bundles all scans opened in the Weasel GUI.

        Parameters
        ----------
        objWeasel : the Weasel global variable
    """
    def __init__(self, objWeasel):
        self.objWeasel = objWeasel
    
    def __repr__(self):
       return '{}'.format(self.__class__.__name__)

    @property
    def children(self):
        logger.info("Project.children called")
        try:
            children = []
            rootXML = self.objWeasel.objXMLReader.root
            for subjectXML in rootXML:
                subjectID = subjectXML.attrib['id']
                subject = Subject(self.objWeasel, subjectID)
                children.append(subject)
            return SubjectList(children)
        except Exception as e:
            print('Error in Project.children: ' + str(e))
            logger.exception('Error in Project.children: ' + str(e))
    
    @property
    def number_children(self):
        return len(self.children)


class Subject:
    """This class encloses all DICOM files that share the same tag value of "PatientID".

        Parameters
        ----------
        objWeasel : the Weasel global variable
        subjectID : string
            This is the name or identification of the subject, which is stored in the "PatientID" DICOM tag.
        suffix : string (optional)
            This is the text to append to subjectID if a new Subject() class is created.
    """
    __slots__ = ('objWeasel', 'subjectID', 'suffix')
    def __init__(self, objWeasel, subjectID, suffix=None):
        self.objWeasel = objWeasel
        self.subjectID = subjectID
        self.suffix = '' if suffix is None else suffix

    def __repr__(self):
       return '{}'.format(self.__class__.__name__)
    
    @property
    def children(self):
        logger.info("Subject.children called")
        try:
            children = []
            subjectXML = self.objWeasel.objXMLReader.getSubject(self.subjectID)
            if subjectXML:
                for studyXML in subjectXML:
                    studyID = studyXML.attrib['id']
                    study = Study(self.objWeasel, self.subjectID, studyID)
                    children.append(study)
            return StudyList(children)
        except Exception as e:
            print('Error in Subject.children: ' + str(e))
            logger.exception('Error in Subject.children: ' + str(e))

    @property
    def parent(self):
        logger.info("Subject.parent called")
        try:
            return Project(self.objWeasel)
        except Exception as e:
            print('Error in Subject.parent: ' + str(e))
            logger.exception('Error in Subject.parent: ' + str(e))

    @property
    def number_children(self):
        return len(self.children)
    
    @property
    def label(self):
        logger.info("Subject.label called")
        try:
            return self.subjectID
        except Exception as e:
            print('Error in Subject.label: ' + str(e))
            logger.exception('Error in Subject.label: ' + str(e))
    
    @property
    def all_images(self):
        logger.info("Subject.all_images called")
        try:
            listImages = []
            for study in self.children:
                listImages.extend(study.all_images)
            return ImagesList(listImages)
        except Exception as e:
            print('Error in Subject.all_images: ' + str(e))
            logger.exception('Error in Subject.all_images: ' + str(e))
    
    def new(self, suffix="_Copy", subjectID=None):
        logger.info("Subject.new called")
        try:
            if subjectID is None:
                subjectID = self.subjectID + suffix
            return Subject(self.objWeasel, subjectID)
        except Exception as e:
            print('Error in Subject.new: ' + str(e))
            logger.exception('Error in Subject.new: ' + str(e))

    def copy(self, suffix="_Copy", output_dir=None):
        logger.info("Subject.copy called")
        try:
            newSubjectID = self.subjectID + suffix
            for study in self.children:
                study.copy(suffix='', newSubjectID=newSubjectID, output_dir=output_dir)
            return Subject(self.objWeasel, newSubjectID)
        except Exception as e:
            print('Error in Subject.copy: ' + str(e))
            logger.exception('Error in Subject.copy: ' + str(e))

    def delete(self):
        logger.info("Subject.delete called")
        try:
            for study in self.children:
                study.delete()
            self.subjectID = ''
            #interfaceDICOMXMLFile.removeSubjectinXMLFile(self.objWeasel, self.subjectID)
        except Exception as e:
            print('Error in Subject.delete: ' + str(e))
            logger.exception('Error in Subject.delete: ' + str(e))

    def add(self, study):
        logger.info("Subject.add called")
        try:
            study.subjectID = self.subjectID
            study["PatientID"] = study.subjectID
            #interfaceDICOMXMLFile.insertNewStudyInXMLFile(self, study.subjectID, study.studyID, study.suffix)
        except Exception as e:
            print('Error in Subject.add: ' + str(e))
            logger.exception('Error in Subject.add: ' + str(e))

    @staticmethod
    def merge(listSubjects, newSubjectName=None, suffix='_Merged', overwrite=False, progress_bar=False, output_dir=None):
        logger.info("Subject.merge called")
        try:
            if newSubjectName:
                outputSubject = Subject(listSubjects[0].objWeasel, newSubjectName)
            else:
                outputSubject = listSubjects[0].new(suffix=suffix)
            # Setup Progress Bar
            progressBarTitle = "Progress Bar - Merging " + str(len(listSubjects)) + " Subjects"
            if progress_bar == True: 
                listSubjects[0].objWeasel.progress_bar(
                    msg = ("<H4>Merging {} Subjects</H4>").format(len(listSubjects)),
                    index = 0, max = len(listSubjects))
            # Add new subject (outputSubject) to XML
            for index, subject in enumerate(listSubjects):
                # Increment progress bar
                subjMsg = "Merging subject " + subject.subjectID
                if progress_bar == True: 
                    listSubjects[0].objWeasel.progress_bar(
                        msg = ("<H4>" + subjMsg + "</H4>"),
                        index = index+1, max = len(listSubjects))
                # Overwrite or not?
                if overwrite == False:
                    for study in subject.children:
                        # Create a copy of the study into the new subject
                        studyMsg = ", study " + study.studyID
                        if progress_bar == True: 
                            listSubjects[0].objWeasel.progress_bar(
                                msg = ("<H4>" + subjMsg + studyMsg + "</H4>"),
                                index = index+1, max = len(listSubjects))
                        study.copy(suffix=suffix, newSubjectID=outputSubject.subjectID, output_dir=output_dir)
                else:
                    for study in subject.children:
                        studyMsg = ", study " + study.studyID
                        if progress_bar == True: 
                            listSubjects[0].objWeasel.progress_bar(
                                msg = ("<H4>" + subjMsg + studyMsg + "</H4>"),
                                index = index+1, max = len(listSubjects))
                        seriesPathsList = []
                        for series in study.children:
                            series.Item('PatientID', outputSubject.subjectID)
                            seriesPathsList.append(series.images)
                        outputSubject.objWeasel.objXMLReader.insertNewStudyInXMLFile(
                                    outputSubject.subjectID, study.studyID, suffix, seriesList=seriesPathsList) # Need new Study name situation
                        # Add study to new subject in the XML
                    subject.objWeasel.objXMLReader.removeSubjectFromXMLFile(subject.subjectID)
            return outputSubject
        except Exception as e:
            print('Error in Subject.merge: ' + str(e))
            logger.exception('Error in Subject.merge: ' + str(e))

    def get_value(self, tag):
        logger.info("Subject.get_value called")
        try:
            if len(self.children) > 0:
                studyOutputValuesList = []
                for study in self.children:
                    studyOutputValuesList.append(study.get_value(tag)) # extend will allow long single list, while append creates list of lists
                return studyOutputValuesList
            else:
                return []
        except Exception as e:
            print('Error in Subject.get_value: ' + str(e))
            logger.exception('Error in Subject.get_value: ' + str(e))

    def set_value(self, tag, newValue):
        logger.info("Subject.set_value called")
        try:
            if len(self.children) > 0:
                for study in self.children:
                    study.set_value(tag, newValue)
        except Exception as e:
            print('Error in Subject.set_value: ' + str(e))
            logger.exception('Error in Subject.set_value: ' + str(e))
    
    def __getitem__(self, tag):
        return self.get_value(tag)

    def __setitem__(self, tag, value):
        self.set_value(tag, value)


class Study:
    """This class encloses all DICOM files that share the same tag value of "StudyInstanceUID", "StudyDescription", "StudyDate" and "StudyTime".

        Parameters
        ----------
        objWeasel : the Weasel global variable
        subjectID : string
            This is the name or identification of the subject, which is stored in the "PatientID" DICOM tag.
        studyID : string
            This is the name or identification of the study, which is stored in the "StudyDescription" DICOM tag.
        studyUID : string (optional)
            This is the unique identification of the study, which is stored in the "StudyInstanceUID" DICOM tag.
        suffix : string (optional)
            This is the text to append to subjectID if a new Study() class is created.
    """
    __slots__ = ('objWeasel', 'subjectID', 'studyID', 'studyUID', 'suffix')
    def __init__(self, objWeasel, subjectID, studyID, studyUID=None, suffix=None):
        self.objWeasel = objWeasel
        self.subjectID = subjectID
        self.studyID = studyID
        self.studyUID = self.StudyUID if studyUID is None else studyUID
        self.suffix = '' if suffix is None else suffix
    
    def __repr__(self):
       return '{}'.format(self.__class__.__name__)

    @property
    def children(self):
        logger.info("Study.children called")
        try:
            children = []
            studyXML = self.objWeasel.objXMLReader.getStudy(self.subjectID, self.studyID)
            if studyXML:
                for seriesXML in studyXML:
                    seriesID = seriesXML.attrib['id']
                    images = []
                    for imageXML in seriesXML:
                        images.append(imageXML.find('name').text)
                    series = Series(self.objWeasel, self.subjectID, self.studyID, seriesID, listPaths=images)
                    children.append(series)
            return SeriesList(children)
        except Exception as e:
            print('Error in Study.children: ' + str(e))
            logger.exception('Error in Study.children: ' + str(e))
    
    @property
    def parent(self):
        logger.info("Study.parent called")
        try:
            return Subject(self.objWeasel, self.subjectID)
        except Exception as e:
            print('Error in Study.parent: ' + str(e))
            logger.exception('Error in Study.parent: ' + str(e))

    @property
    def number_children(self):
        return len(self.children)

    @property
    def label(self):
        logger.info("Study.label called")
        try:
            return self.studyID
        except Exception as e:
            print('Error in Study.label: ' + str(e))
            logger.exception('Error in Study.label: ' + str(e))

    @property
    def all_images(self):
        logger.info("Study.all_images called")
        try:
            listImages = []
            for series in self.children:
                listImages.extend(series.children)
            return ImagesList(listImages)
        except Exception as e:
            print('Error in Study.all_images: ' + str(e))
            logger.exception('Error in Study.all_images: ' + str(e))

    def new(self, suffix="_Copy", studyID=None):
        logger.info("Study.new called")
        try:
            if studyID is None:
                studyID = self.studyID + suffix
            else:
                dt = datetime.datetime.now()
                time = dt.strftime('%H%M%S')
                date = dt.strftime('%Y%m%d')
                studyID = date + "_" + time + "_" + studyID + suffix
            prefixUID = '.'.join(self.studyUID.split(".", maxsplit=6)[:5]) + "." + str(random.randint(0, 9999)) + "."
            study_uid = pydicom.uid.generate_uid(prefix=prefixUID)
            return Study(self.objWeasel, self.subjectID, studyID, studyUID=study_uid, suffix=suffix)
        except Exception as e:
            print('Error in Study.new: ' + str(e))
            logger.exception('Error in Study.new: ' + str(e))

    def copy(self, suffix="_Copy", newSubjectID=None, output_dir=None):
        logger.info("Study.copy called")
        try:
            if newSubjectID:
                prefixUID = '.'.join(self.studyUID.split(".", maxsplit=6)[:5]) + "." + str(random.randint(0, 9999)) + "."
                study_uid = pydicom.uid.generate_uid(prefix=prefixUID)
                newStudyInstance = Study(self.objWeasel, newSubjectID, self.studyID + suffix, studyUID=study_uid, suffix=suffix)
            else:
                newStudyInstance = self.new(suffix=suffix)
            seriesPathsList = []
            for series in self.children:
                copiedSeries = series.copy(suffix=suffix, series_id=series.seriesID.split('_', 1)[0], series_name=series.seriesID.split('_', 1)[1], study_uid=newStudyInstance.studyUID,
                                           study_name=newStudyInstance.studyID.split('_', 1)[1].split('_', 1)[1], patient_id=newSubjectID, output_dir=output_dir)
                seriesPathsList.append(copiedSeries.images)
            #interfaceDICOMXMLFile.insertNewStudyInXMLFile(newStudyInstance.objWeasel, newStudyInstance.subjectID, newStudyInstance.studyID, suffix, seriesList=seriesPathsList)
            return newStudyInstance
        except Exception as e:
            print('Error in Study.copy: ' + str(e))
            logger.exception('Error in Study.copy: ' + str(e))

    def delete(self):
        logger.info("Study.delete called")
        try:
            for series in self.children:
                series.delete()
            #interfaceDICOMXMLFile.removeOneStudyFromSubject(self.objWeasel, self.subjectID, self.studyID)
            self.subjectID = self.studyID = ''
        except Exception as e:
            print('Error in Study.delete: ' + str(e))
            logger.exception('Error in Study.delete: ' + str(e))
    
    def add(self, series):
        logger.info("Study.add called")
        try:
            series["PatientID"] = self.subjectID
            series["StudyDate"] = self.studyID.split("_")[0]
            series["StudyTime"] = self.studyID.split("_")[1]
            series["StudyDescription"] = "".join(self.studyID.split("_")[2:])
            series["StudyInstanceUID"] = self.studyUID
            # Need to adapt the series to the new Study
            seriesNewID, seriesNewUID = GenericDICOMTools.generateSeriesIDs(self.objWeasel, series.images, studyUID=self.studyUID)
            series["SeriesNumber"] = seriesNewID
            series["SeriesInstanceUID"] = seriesNewUID
        except Exception as e:
            print('Error in Study.add: ' + str(e))
            logger.exception('Error in Study.add: ' + str(e))

    @staticmethod
    def merge(listStudies, newStudyName=None, suffix='_Merged', overwrite=False, output_dir=None, progress_bar=True):
        logger.info("Study.merge called")
        try:
            if newStudyName:
                prefixUID = '.'.join(listStudies[0].studyUID.split(".", maxsplit=6)[:5]) + "." + str(random.randint(0, 9999)) + "."
                study_uid = pydicom.uid.generate_uid(prefix=prefixUID)
                newStudyID = listStudies[0].studyID.split('_')[0] + "_" + listStudies[0].studyID.split('_')[1] + "_" + newStudyName
                outputStudy = Study(listStudies[0].objWeasel, listStudies[0].subjectID, newStudyID, studyUID=study_uid)
            else:
                outputStudy = listStudies[0].new(suffix=suffix)
            # Set up Progress Bar
            progressBarTitle = "Progress Bar - Merging " + str(len(listStudies)) + " Studies"
            if progress_bar == True: 
                listStudies[0].objWeasel.progress_bar(
                    msg = ("<H4>Merging {} Studies</H4>").format(len(listStudies)),
                    index = 0, max = len(listStudies))
            # Add new study (outputStudy) to XML
            seriesPathsList = []
            if overwrite == False:
                for index, study in enumerate(listStudies):
                    if progress_bar == True: 
                        listStudies[0].objWeasel.progress_bar(
                            msg = ("<H4>Merging study " + study.studyID + "</H4>"),
                            index = index+1, max = len(listStudies))
                    seriesNumber = 1
                    for series in study.children:
                        copiedSeries = series.copy(suffix=suffix, series_id=seriesNumber, series_name=series.seriesID.split('_', 1)[1], study_uid=outputStudy.studyUID,
                                                   study_name=outputStudy.studyID.split('_', 1)[1].split('_', 1)[1], patient_id=outputStudy.subjectID, output_dir=output_dir)
                        seriesPathsList.append(copiedSeries.images)
                        seriesNumber += 1
            else:
                seriesNumber = 1
                for index, study in enumerate(listStudies):
                    if progress_bar == True: 
                        listStudies[0].objWeasel.progress_bar(
                            msg = ("<H4>Merging study " + study.studyID + "</H4>"),
                            index = index+1, max = len(listStudies))
                    for series in study.children:
                        series.Item('PatientID', outputStudy.subjectID)
                        series.Item('StudyInstanceUID', outputStudy.studyUID)
                        series.Item('StudyDescription', outputStudy.studyID.split('_', 1)[1].split('_', 1)[1])
                        series.Item('SeriesNumber', seriesNumber)
                        # Generate new series uid based on outputStudy.studyUID
                        _, new_series_uid = GenericDICOMTools.generateSeriesIDs(series.objWeasel, series.images, seriesNumber=seriesNumber, studyUID=outputStudy.studyUID)
                        series.Item('SeriesInstanceUID', new_series_uid)
                        seriesPathsList.append(series.images)
                        seriesNumber += 1
                    study.objWeasel.objXMLReader.removeOneStudyFromSubject(study.subjectID, study.studyID)
            outputStudy.objWeasel.objXMLReader.insertNewStudyInXMLFile(outputStudy.subjectID, outputStudy.studyID, suffix, seriesList=seriesPathsList)
            return outputStudy
        except Exception as e:
            print('Error in Study.merge: ' + str(e))
            logger.exception('Error in Study.merge: ' + str(e))

    @property
    def StudyUID(self):
        if len(self.children) > 0:
            return self.children[0].studyUID
        else:
            return pydicom.uid.generate_uid(prefix=None)
    
    def get_value(self, tag):
        logger.info("Study.get_value called")
        try:
            if len(self.children) > 0:
                seriesOutputValuesList = []
                for series in self.children:
                    seriesOutputValuesList.append(series.get_value(tag)) # extend will allow long single list, while append creates list of lists.
                return seriesOutputValuesList
            else:
                return []
        except Exception as e:
            print('Error in Study.get_value: ' + str(e))
            logger.exception('Error in Study.get_value: ' + str(e))

    def set_value(self, tag, newValue):
        logger.info("Study.set_value called")
        try:
            if len(self.children) > 0:
                for series in self.children:
                    series.set_value(tag, newValue)
        except Exception as e:
            print('Error in Study.set_value: ' + str(e))
            logger.exception('Error in Study.set_value: ' + str(e))

    
    def __getitem__(self, tag):
        return self.get_value(tag)

    def __setitem__(self, tag, value):
        self.set_value(tag, value)


class Series:
    """This class encloses all DICOM files that share the same tag value of "StudyInstanceUID", "StudyDescription", "StudyDate" and "StudyTime".

        Parameters
        ----------
        objWeasel : the Weasel global variable
        subjectID : string
            This is the name or identification of the subject, which is stored in the "PatientID" DICOM tag.
        studyID : string
            This is the name or identification of the study, which is stored in the "StudyDescription" DICOM tag.
        seriesID : string
            This is the name or identification of the series, which is stored in the "SeriesDescription" DICOM tag.
        listPaths : list(string) (optional)
            This is a list containing the file paths of the DICOM files that belong to the Series() instance created.
            This class creates the list based on the Weasel GUI TreeView selection if it's not given.
        studyUID : string (optional)
            This is the unique identification of the study, which is stored in the "StudyInstanceUID" DICOM tag.
        seriesUID : string (optional)
            This is the unique identification of the study, which is stored in the "SeriesInstanceUID" DICOM tag.
        suffix : string (optional)
            This is the text to append to subjectID if a new Series() class is created.
    """
    __slots__ = ('objWeasel', 'subjectID', 'studyID', 'seriesID', 'studyUID', 'seriesUID', 
                 'images', 'suffix', 'referencePathsList')
    def __init__(self, objWeasel, subjectID, studyID, seriesID, listPaths=None, studyUID=None, seriesUID=None, suffix=None):
        self.objWeasel = objWeasel
        self.subjectID = subjectID
        self.studyID = studyID
        self.seriesID = seriesID
        self.images = [] if listPaths is None else listPaths
        self.studyUID = self.StudyUID if studyUID is None else studyUID
        self.seriesUID = self.SeriesUID if seriesUID is None else seriesUID
        self.suffix = '' if suffix is None else suffix
        self.referencePathsList = []
        print("Series object created")
        # This is to deal with Enhanced MRI
        #if self.PydicomList and len(self.images) == 1:
        #    self.indices = list(np.arange(len(self.PydicomList[0].PerFrameFunctionalGroupsSequence))) if hasattr(self.PydicomList[0], 'PerFrameFunctionalGroupsSequence') else []
        #else:
        #    self.indices = []
    
    def __repr__(self):
       return '{} series ID={}'.format(self.__class__.__name__, self.seriesID)

    @property
    def children(self):
        logger.info("Series.children called")
        try:
            children = []
            if len(self.images) > 1:
                for imagePath in self.images:
                    image = Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, imagePath)
                    children.append(image)
            else:
                seriesXML = self.objWeasel.objXMLReader.getSeries(self.subjectID, self.studyID, self.seriesID)
                for imageXML in seriesXML:
                    image = Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, imageXML.find('name').text)
                    children.append(image)
            return ImagesList(children)
        except Exception as e:
            print('Error in Series.children: ' + str(e))
            logger.exception('Error in Series.children: ' + str(e))
    
    @property
    def parent(self):
        logger.info("Series.parent called")
        try:
            return Study(self.objWeasel, self.subjectID, self.studyID, studyUID=self.studyUID)
        except Exception as e:
            print('Error in Series.parent: ' + str(e))
            logger.exception('Error in Series.parent: ' + str(e))

    @property
    def number_children(self):
        return len(self.children)

    @property
    def label(self):
        logger.info("Series.label called")
        try:
            return self.seriesID
        except Exception as e:
            print('Error in Series.label: ' + str(e))
            logger.exception('Error in Series.label: ' + str(e))
    
    def new(self, suffix="_Copy", series_id=None, series_name=None, series_uid=None):
        logger.info("Series.new called")
        try:
            if series_id is None:
                series_id, _ = GenericDICOMTools.generateSeriesIDs(self.objWeasel, self.images)
            if series_name is None:
                series_name = self.seriesID.split('_', 1)[1] + suffix
            if series_uid is None:
                _, series_uid = GenericDICOMTools.generateSeriesIDs(self.objWeasel, self.images, seriesNumber=series_id)
            seriesID = str(series_id) + '_' + series_name
            newSeries = Series(self.objWeasel, self.subjectID, self.studyID, seriesID, seriesUID=series_uid, suffix=suffix)
            newSeries.referencePathsList = self.images
            return newSeries
        except Exception as e:
            print('Error in Series.new: ' + str(e))
            logger.exception('Error in Series.new: ' + str(e))
    
    def copy(self, suffix="_Copy", newSeries=True, series_id=None, series_name=None, series_uid=None, study_uid=None, study_name=None, patient_id=None, output_dir=None):
        logger.info("Series.copy called")
        try:
            if newSeries == True:
                newPathsList, newSeriesID = GenericDICOMTools.copyDICOM(self.objWeasel, self.images, series_id=series_id, series_uid=series_uid, series_name=series_name,
                                                                        study_uid=study_uid, study_name=study_name, patient_id=patient_id, suffix=suffix, output_dir=output_dir)
                return Series(self.objWeasel, self.subjectID, self.studyID, newSeriesID, listPaths=newPathsList, suffix=suffix)
            else:
                series_id = self.seriesID.split('_', 1)[0]
                series_name = self.seriesID.split('_', 1)[1]
                series_uid = self.seriesUID
                suffix = self.suffix
                newPathsList, _ = GenericDICOMTools.copyDICOM(self.objWeasel, self.images, series_id=series_id, series_uid=series_uid, series_name=series_name, study_uid=study_uid,
                                                              study_name=study_name, patient_id=patient_id,suffix=suffix, output_dir=output_dir) # StudyID in InterfaceXML
                for newCopiedImagePath in newPathsList:
                    newImage = Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, newCopiedImagePath)
                    self.add(newImage)
        except Exception as e:
            print('Error in Series.copy: ' + str(e))
            logger.exception('Error in Series.copy: ' + str(e))

    def delete(self):
        logger.info("Series.delete called")
        try:
            GenericDICOMTools.deleteDICOM(self.objWeasel, self.images)
            self.images = self.referencePathsList = []
            #self.children = self.indices = []
            #self.number_children = 0
            self.subjectID = self.studyID = self.seriesID = self.seriesUID = ''
        except Exception as e:
            print('Error in Series.delete: ' + str(e))
            logger.exception('Error in Series.delete: ' + str(e))

    def add(self, Image):
        logger.info("Series.add called")
        try:
            self.images.append(Image.path)
            # Might need XML functions
            #self.children.append(Image)
            #self.number_children = len(self.children)
        except Exception as e:
            print('Error in Series.add: ' + str(e))
            logger.exception('Error in Series.add: ' + str(e))

    def remove(self, all_images=False, Image=None):
        logger.info("Series.remove called")
        try:
            if all_images == True:
                self.images = []
                # Might need XML functions
                #self.children = []
                #self.number_children = 0
            elif Image is not None:
                self.images.remove(Image.path)
                # Might need XML functions
                #self.children.remove(Image)
                #self.number_children = len(self.children)
        except Exception as e:
            print('Error in Series.remove: ' + str(e))
            logger.exception('Error in Series.remove: ' + str(e))

    def write(self, pixelArray, output_dir=None, value_range=None, parametric_map=None, colourmap=None):
        logger.info("Series.write called")
        try:
            if isinstance(value_range, list):
                pixelArray = np.nan_to_num(pixelArray, posinf=0, neginf=0)
                pixelArray = np.clip(pixelArray, value_range[0], value_range[1])
            else:
                list_values = np.unique(pixelArray).flatten()
                list_values = [x for x in list_values if np.isnan(x) == False]
                if np.isposinf(list_values[-1]) or np.isinf(list_values[-1]):
                    upper_value = list_values[-2]
                else:
                    upper_value = None
                if np.isneginf(list_values[0]) or np.isinf(list_values[0]):
                    lower_value = list_values[1]
                else:
                    lower_value = None
                pixelArray = np.nan_to_num(pixelArray, posinf=upper_value, neginf=lower_value)
            if self.images:
                PixelArrayDICOMTools.overwritePixelArray(pixelArray, self.images)
            else:
                series_id = self.seriesID.split('_', 1)[0]
                series_name = self.seriesID.split('_', 1)[1]
                inputReference = self.referencePathsList[0] if len(self.referencePathsList)==1 else self.referencePathsList
                outputPath = PixelArrayDICOMTools.writeNewPixelArray(self.objWeasel, pixelArray, inputReference, self.suffix, series_id=series_id, series_name=series_name, series_uid=self.seriesUID, output_dir=output_dir, parametric_map=parametric_map, colourmap=colourmap)
                self.images = outputPath
                if self["WindowWidth"] and self["WindowCenter"] and isinstance(value_range, list):
                    width = value_range[1] - value_range[0]
                    center = value_range[0] + (width/2)
                    self["WindowWidth"] = width
                    self["WindowCenter"] = center
        except Exception as e:
            print('Error in Series.write: ' + str(e))
            logger.exception('Error in Series.write: ' + str(e))
    
    def read(self):
        return self.PydicomList

    def save(self, PydicomList):
        newSubjectID = self.subjectID
        newStudyID = self.studyID
        newSeriesID = self.seriesID
        for index, dataset in enumerate(PydicomList):
            changeXML = False
            if dataset.SeriesDescription != self.PydicomList[index].SeriesDescription or dataset.SeriesNumber != self.PydicomList[index].SeriesNumber:
                changeXML = True
                newSeriesID = str(dataset.SeriesNumber) + "_" + str(dataset.SeriesDescription)
            if dataset.StudyDate != self.PydicomList[index].StudyDate or dataset.StudyTime != self.PydicomList[index].StudyTime or dataset.StudyDescription != self.PydicomList[index].StudyDescription:
                changeXML = True
                newStudyID = str(dataset.StudyDate) + "_" + str(dataset.StudyTime).split(".")[0] + "_" + str(dataset.StudyDescription)
            if dataset.PatientID != self.PydicomList[index].PatientID:
                changeXML = True
                newSubjectID = str(dataset.PatientID)
            SaveDICOM_Image.saveDicomToFile(dataset, output_path=self.images[index])
            if changeXML == True:
                self.objWeasel.objXMLReader.moveImageInXMLFile(self.subjectID, self.studyID, self.seriesID, newSubjectID, newStudyID, newSeriesID, self.images[index], '')
        # Only after updating the Element Tree (XML), we can change the instance values and save the DICOM file
        self.subjectID = newSubjectID
        self.studyID = newStudyID
        self.seriesID = newSeriesID

    @staticmethod
    def merge(listSeries, series_id=None, series_name='NewSeries', series_uid=None, study_name=None, study_uid=None, patient_id=None, suffix='_Merged', overwrite=False, progress_bar=False):
        logger.info("Series.merge called")
        try:
            outputSeries = listSeries[0].new(suffix=suffix, series_id=series_id, series_name=series_name, series_uid=series_uid)
            pathsList = [image for series in listSeries for image in series.images]
            outputPathList = GenericDICOMTools.mergeDicomIntoOneSeries(outputSeries.objWeasel, pathsList, series_uid=series_uid, series_id=series_id, series_name=series_name, study_name=study_name, study_uid=study_uid, patient_id=patient_id, suffix=suffix, overwrite=overwrite, progress_bar=progress_bar)
            outputSeries.images = outputPathList
            outputSeries.referencePathsList = outputPathList
            return outputSeries
        except Exception as e:
            print('Error in Series.merge: ' + str(e))
            logger.exception('Error in Series.merge: ' + str(e))
    
    # Deprecated but might be useful in the future
    #def sort(self, tagDescription, *argv):
    #    if self.Item(tagDescription) or self.Tag(tagDescription):
    #        imagePathList, _, _, indicesSorted = ReadDICOM_Image.sortSequenceByTag(self.images, tagDescription)
    #        self.images = imagePathList
    #        #if self.Multiframe: self.indices = sorted(set(indicesSorted) & set(self.indices), key=indicesSorted.index)
    #    for tag in argv:
    #        if self.Item(tag) or self.Tag(tag):
    #            imagePathList, _, _, indicesSorted = ReadDICOM_Image.sortSequenceByTag(self.images, tag)
    #            self.images = imagePathList
    #            #if self.Multiframe: self.indices = sorted(set(indicesSorted) & set(self.indices), key=indicesSorted.index)
    
    def sort(self, *argv, reverse=False):
        logger.info("Series.sort called")
        try:
            tuple_to_sort = []
            list_to_sort = [self.images]
            for tag in argv:
                if len(self.get_value(tag)) > 0:
                    list_to_sort.append(self.get_value(tag))
            for index in range(len(self.images)):
                individual_tuple = [individual_list[index] for individual_list in list_to_sort]
                tuple_to_sort.append(tuple(individual_tuple))
            tuple_sorted = sorted(tuple_to_sort, key=lambda x: x[1:], reverse=reverse)
            list_sorted_images = [individual[0] for individual in tuple_sorted]
            self.images = list_sorted_images
            return self
        except Exception as e:
            print('Error in Series.sort: ' + str(e))
            logger.exception('Error in Series.sort: ' + str(e))
    
    def where(self, tag, condition, target):
        logger.info("Series.where called")
        try:
            list_images = []
            list_paths = []
            for image in self.children:
                value = image[tag]
                if condition == "==":
                    statement = 'str(' + repr(value) + ') ' + condition + ' str(' + repr(target) + ')'
                    if eval(statement) == True:
                        list_images.append(image)
                        list_paths.append(image.path)
                else:
                    statement = repr(value) + ' ' + repr(condition) + ' ' + repr(target)
                    if eval(literal_eval(statement)) == True:
                        list_images.append(image)
                        list_paths.append(image.path)
            self.images = list_paths
            return self
        except Exception as e:
            print('Error in Series.where: ' + str(e))
            logger.exception('Error in Series.where: ' + str(e))

    def display(self):
        self.objWeasel.display(self)

    def plot(self, xlabel="X axis", ylabel="Y axis"):
        logger.info("Series.plot called")
        try:
            for imagePath in self.images:
                image = Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, imagePath)
                image.plot(xlabel, ylabel)
        except Exception as e:
            print('Error in Series.plot: ' + str(e))
            logger.exception('Error in Series.plot: ' + str(e))

    def Metadata(self):
        logger.info("Series.Metadata called")
        try:
            self.objWeasel.displayMetadata(self.images)
        except Exception as e:
            print('Error in Series.Metadata: ' + str(e))
            logger.exception('Error in Series.Metadata: ' + str(e))

    @property
    def SeriesUID(self):
        if not self.images:
            self.seriesUID = None
        elif os.path.exists(self.images[0]):
            self.seriesUID = ReadDICOM_Image.getImageTagValue(self.images[0], 'SeriesInstanceUID')
        else:
            self.seriesUID = None
        return self.seriesUID

    @property
    def StudyUID(self):
        if not self.images:
            self.studyUID = None
        elif os.path.exists(self.images[0]):
            self.studyUID = ReadDICOM_Image.getImageTagValue(self.images[0], 'StudyInstanceUID')
        else:
            self.studyUID = None
        return self.studyUID

    @property
    def Magnitude(self):
        logger.info("Series.Magnitude called")
        try:
            dicomList = self.PydicomList
            magnitudeSeries = Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, listPaths=self.images)
            magnitudeSeries.remove(all_images=True)
            magnitudeSeries.referencePathsList = self.images
            for index in range(len(self.images)):
                flagMagnitude, _, _, _, _ = ReadDICOM_Image.checkImageType(dicomList[index])
                #if isinstance(flagMagnitude, list) and flagMagnitude:
                #    if len(flagMagnitude) > 1 and len(self.images) == 1:
                #        magnitudeSeries.indices = flagMagnitude
                #    magnitudeSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
                if flagMagnitude == True:
                    magnitudeSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
            return magnitudeSeries
        except Exception as e:
            print('Error in Series.Magnitude: ' + str(e))
            logger.exception('Error in Series.Magnitude: ' + str(e))

    @property
    def Phase(self):
        logger.info("Series.Phase called")
        try:
            dicomList = self.PydicomList
            phaseSeries = Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, listPaths=self.images)
            phaseSeries.remove(all_images=True)
            phaseSeries.referencePathsList = self.images
            for index in range(len(self.images)):
                _, flagPhase, _, _, _ = ReadDICOM_Image.checkImageType(dicomList[index])
                #if isinstance(flagPhase, list) and flagPhase:
                #    if len(flagPhase) > 1 and len(self.images) == 1:
                #        phaseSeries.indices = flagPhase
                #    phaseSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
                if flagPhase == True:
                    phaseSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
            return phaseSeries
        except Exception as e:
            print('Error in Series.Phase: ' + str(e))
            logger.exception('Error in Series.Phase: ' + str(e))

    @property
    def Real(self):
        logger.info("Series.Real called")
        try:
            dicomList = self.PydicomList
            realSeries = Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, listPaths=self.images)
            realSeries.remove(all_images=True)
            realSeries.referencePathsList = self.images
            for index in range(len(self.images)):
                _, _, flagReal, _, _ = ReadDICOM_Image.checkImageType(dicomList[index])
                #if isinstance(flagReal, list) and flagReal:
                #    if len(flagReal) > 1 and len(self.images) == 1:
                #        realSeries.indices = flagReal
                #    realSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
                if flagReal:
                    realSeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
            return realSeries
        except Exception as e:
            print('Error in Series.Real: ' + str(e))
            logger.exception('Error in Series.Real: ' + str(e))

    @property
    def Imaginary(self):
        logger.info("Series.Imaginary called")
        try:
            dicomList = self.PydicomList
            imaginarySeries = Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, listPaths=self.images)
            imaginarySeries.remove(all_images=True)
            imaginarySeries.referencePathsList = self.images
            for index in range(len(self.images)):
                _, _, _, flagImaginary, _ = ReadDICOM_Image.checkImageType(dicomList[index])
                #if isinstance(flagImaginary, list) and flagImaginary:
                #    if len(flagImaginary) > 1 and len(self.images) == 1:
                #        imaginarySeries.indices = flagImaginary
                #    imaginarySeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
                if flagImaginary:
                    imaginarySeries.add(Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, self.images[index]))
            return imaginarySeries
        except Exception as e:
            print('Error in Series.Imaginary: ' + str(e))
            logger.exception('Error in Series.Imaginary: ' + str(e))

    @property
    def PixelArray(self):
        logger.info("Series.PixelArray called")
        try:
            pixelArray = PixelArrayDICOMTools.getPixelArrayFromDICOM(self.images)
            return pixelArray
        except Exception as e:
            print('Error in Series.PixelArray: ' + str(e))
            logger.exception('Error in Series.PixelArray: ' + str(e))
        
    def overlay_mask(self, maskInstance):
        """Returns the PixelArray masked.
            Usage example:
           ''' 
            for series in list_series:
                if "ROI_mask" in series.label:
                    mask_series = series
                if "DWI" in series.label:
                    main_series = series
            masked_array = main_series.overlay_mask(mask_series)
        """
        logger.info("Series.Mask called")
        try:
            dataset = maskInstance.PydicomList
            mask_array = maskInstance.PixelArray
            mask_array[mask_array != 0] = 1
            mask_output = []
            if isinstance(maskInstance, Image):
                for dicomFile in self.images:
                    dataset_original = ReadDICOM_Image.getDicomDataset(dicomFile)
                    tempArray = np.zeros(np.shape(ReadDICOM_Image.getPixelArray(dataset_original)))
                    affine_results = ReadDICOM_Image.mapMaskToImage(mask_array, dataset, dataset_original)
                    if affine_results:
                        coords = zip(*affine_results)
                        tempArray[tuple(coords)] = list(np.ones(len(affine_results)).flatten())
                    mask_output.append(np.transpose(tempArray) * ReadDICOM_Image.getPixelArray(dataset_original))
                return np.nan_to_num(mask_output)
            elif isinstance(maskInstance, Series):
                listImages = self.images
                listMaskImages = maskInstance.images
                if np.shape(mask_array) == np.shape(self.PixelArray) and maskInstance.Affine.all() == self.Affine.all():
                    if len(np.shape(mask_array)) == 3:
                        mask_output = [np.transpose(image2D) for image2D in mask_array]
                    else:
                        mask_output = np.transpose(mask_array)
                else:
                    for dicomFile in listImages:
                        dataset_original = ReadDICOM_Image.getDicomDataset(dicomFile)
                        tempArray = np.zeros(np.shape(ReadDICOM_Image.getPixelArray(dataset_original)))
                        for maskFile in listMaskImages:
                            dataset = ReadDICOM_Image.getDicomDataset(maskFile)
                            mask_array = ReadDICOM_Image.getPixelArray(dataset)
                            mask_array[mask_array != 0] = 1
                            affine_results = ReadDICOM_Image.mapMaskToImage(mask_array, dataset, dataset_original)
                            if affine_results:
                                coords = zip(*affine_results)
                                tempArray[tuple(coords)] = list(np.ones(len(affine_results)).flatten())
                        mask_output.append(np.transpose(tempArray) * ReadDICOM_Image.getPixelArray(dataset_original))
                return np.nan_to_num(mask_output)
        except Exception as e:
            print('Error in Series.Mask: ' + str(e))
            logger.exception('Error in Series.Mask: ' + str(e))
    
    def write_mask(self, mask_array, label=None):
        logger.info("Series.write_mask called")
        try:
            if label is not None:
                self.suffix = "_" + label
            self.write(mask_array, parametric_map="SEG")
        except Exception as e:
            print('Error in Series.write_mask: ' + str(e))
            logger.exception('Error in Series.write_mask: ' + str(e))

    @property
    def Affine(self):
        logger.info("Series.Affine called")
        try:
            return ReadDICOM_Image.returnAffineArray(self.images[0])
        except Exception as e:
            print('Error in Series.Affine: ' + str(e))
            logger.exception('Error in Series.Affine: ' + str(e))
    
    @property
    def TopLeftCorner(self):
        logger.info("Series.TopLeftCorner called")
        try:
            listCoords = list()
            dicomList = self.PydicomList
            for dicom_dataset in dicomList:
                listCoords.append(ReadDICOM_Image.getTopLeftCorner(dicom_dataset))
            return listCoords
        except Exception as e:
            print('Error in Series.TopLeftCorner: ' + str(e))
            logger.exception('Error in Series.TopLeftCorner: ' + str(e))

    @property
    def CentralSliceLocation(self):
        logger.info("Series.CentralSliceLocation called")
        try:
            locations = np.unique(self["SliceLocation"])
            # If number of slices is even, the lower value is selected.
            central_index = int(np.floor(len(locations) / 2))
            return locations[central_index]
        except Exception as e:
            print('Error in Series.CentralSliceLocation: ' + str(e))
            logger.exception('Error in Series.CentralSliceLocation: ' + str(e))

    @property
    def ListAffines(self):
        logger.info("Series.ListAffines called")
        try:
            return [ReadDICOM_Image.returnAffineArray(image) for image in self.images]
        except Exception as e:
            print('Error in Series.ListAffines: ' + str(e))
            logger.exception('Error in Series.ListAffines: ' + str(e))
    
    @property
    def ROIindices(self):
        logger.info("Series.ROIindices called")
        try:
            tempImage = self.PixelArray
            tempImage[tempImage != 0] = 1
            return np.transpose(np.where(tempImage == 1))
        except Exception as e:
            print('Error in Series.ROIindices: ' + str(e))
            logger.exception('Error in Series.ROIindices: ' + str(e))
    
    def get_value(self, tag):
        logger.info("Series.get_value called")
        try:
            if self.images:
                if isinstance(tag, list):
                    outputValuesList = []
                    for ind_tag in tag:
                        if (ind_tag == "SliceLocation" or ind_tag == (0x0020,0x1041)) and not hasattr(self.PydicomList[0], "SliceLocation"): ind_tag = (0x2001, 0x100a)
                        outputValuesList.append(ReadDICOM_Image.getSeriesTagValues(self.images, ind_tag)[0])
                    return outputValuesList
                elif isinstance(tag, str) and len(tag.split(' ')) == 3:
                    dicom_tag = tag.split(' ')[0]
                    if (dicom_tag == "SliceLocation" or dicom_tag == (0x0020,0x1041)) and not hasattr(self.PydicomList[0], "SliceLocation"): dicom_tag = (0x2001, 0x100a)
                    logical_operator = tag.split(' ')[1]
                    target_value = tag.split(' ')[2]
                    series_to_return = copy.copy(self)
                    series_to_return.where(dicom_tag, logical_operator, target_value)
                    list_of_images = series_to_return.children
                    return list_of_images
                elif isinstance(tag, int):
                    return self.children[tag]
                else:
                    if (tag == "SliceLocation" or tag == (0x0020,0x1041)) and not hasattr(self.PydicomList[0], "SliceLocation"): tag = (0x2001, 0x100a)
                    return ReadDICOM_Image.getSeriesTagValues(self.images, tag)[0]
            else:
                return []
        except Exception as e:
            print('Error in Series.get_value: ' + str(e))
            logger.exception('Error in Series.get_value: ' + str(e))

    def set_value(self, tag, newValue):
        logger.info("Series.set_value called")
        try:
            if self.images:
                comparisonDicom = self.PydicomList
                oldSubjectID = self.subjectID
                oldStudyID = self.studyID
                oldSeriesID = self.seriesID
                if isinstance(tag, list) and isinstance(newValue, list):
                    for index, ind_tag in enumerate(tag):
                        self.set_value(ind_tag, newValue[index])
                        #GenericDICOMTools.editDICOMTag(self.images, ind_tag, newValue[index])
                elif isinstance(newValue, list):
                    for value in newValue:
                        GenericDICOMTools.editDICOMTag(self.images, tag, value)
                else:
                    GenericDICOMTools.editDICOMTag(self.images, tag, newValue)
                newDicomList = self.PydicomList
                # Consider the case where other XML fields are changed
                for index, dataset in enumerate(comparisonDicom):
                    changeXML = False
                    if dataset.SeriesDescription != newDicomList[index].SeriesDescription or dataset.SeriesNumber != newDicomList[index].SeriesNumber:
                        changeXML = True
                        newSeriesID = str(newDicomList[index].SeriesNumber) + "_" + str(newDicomList[index].SeriesDescription)
                        self.seriesID = newSeriesID
                    else:
                        newSeriesID = oldSeriesID
                    if dataset.StudyDate != newDicomList[index].StudyDate or dataset.StudyTime != newDicomList[index].StudyTime or dataset.StudyDescription != newDicomList[index].StudyDescription:
                        changeXML = True
                        newStudyID = str(newDicomList[index].StudyDate) + "_" + str(newDicomList[index].StudyTime).split(".")[0] + "_" + str(newDicomList[index].StudyDescription)
                        self.studyID = newStudyID
                    else:
                        newStudyID = oldStudyID
                    if dataset.PatientID != newDicomList[index].PatientID:
                        changeXML = True
                        newSubjectID = str(newDicomList[index].PatientID)
                        self.subjectID = newSubjectID
                    else:
                        newSubjectID = oldSubjectID
                    if changeXML == True:
                        self.objWeasel.objXMLReader.moveImageInXMLFile(oldSubjectID, oldStudyID, oldSeriesID, newSubjectID, newStudyID, newSeriesID, self.images[index], '')
        except Exception as e:
            print('Error in Series.set_value: ' + str(e))
            logger.exception('Error in Series.set_value: ' + str(e))

    def __getitem__(self, tag):
        return self.get_value(tag)

    def __setitem__(self, tag, value):
        if isinstance(tag, str) and len(tag.split(' ')) == 3:
            listImages = self.get_value(tag)
            dicom_tag = tag.split(' ')[0]
            listImages.set_value(dicom_tag, value)
        elif isinstance(tag, int) and isinstance(value, Image):
            self.images[tag] = value.path
        else:
            self.set_value(tag, value)

    # Remove this function in the future - Careful with Subject.merge and Study.merge implications!
    def Item(self, tagDescription, newValue=None):
        if self.images:
            if newValue:
                GenericDICOMTools.editDICOMTag(self.images, tagDescription, newValue)
                if (tagDescription == 'SeriesDescription') or (tagDescription == 'SequenceName') or (tagDescription == 'ProtocolName'):
                    self.objWeasel.objXMLreader.renameSeriesinXMLFile(self.images, series_name=newValue)
                elif tagDescription == 'SeriesNumber':
                    self.objWeasel.objXMLreader.renameSeriesinXMLFile(self.images, series_id=newValue)
            itemList, _ = ReadDICOM_Image.getSeriesTagValues(self.images, tagDescription)
            #if self.Multiframe: 
            #    tempList = [itemList[index] for index in self.indices]
            #    itemList = tempList
            #    del tempList
        else:
            itemList = []
        return itemList
    
    @property
    def PydicomList(self):
        if self.images:
            return PixelArrayDICOMTools.getDICOMobject(self.images)
        else:
            return []

    def export_as_nifti(self, directory=None, filename=None):
        logger.info("Series.export_as_nifti called")
        try:
            if directory is None: directory=os.path.dirname(self.images[0])
            if filename is None: filename=self.seriesID
            dicomHeader = nib.nifti1.Nifti1DicomExtension(2, self.PydicomList[0])
            niftiObj = nib.Nifti1Image(np.flipud(np.rot90(np.transpose(self.PixelArray))), self.Affine)
            # The transpose is necessary in this case to be in line with the rest of Weasel. The rot90() can be a bit questionable, so this should be tested in as much data as possible.
            niftiObj.header.extensions.append(dicomHeader)
            nib.save(niftiObj, directory + '/' + filename + '.nii.gz')
        except Exception as e:
            print('Error in Series.export_as_nifti: ' + str(e))
            logger.exception('Error in Series.export_as_nifti: ' + str(e))
    
    def export_as_csv(self, directory=None, filename=None, columnHeaders=None):
        logger.info("Series.export_as_csv called")
        try:
            if directory is None: directory = os.path.dirname(self.images[0])
            if self.number_children == 1:
                self.children[0].export_as_csv(directory=directory, filename=filename, columnHeaders=columnHeaders)
            else:
                table = self.PixelArray
                image_counter = 0
                for slice_image in table:
                    if filename is None:
                        one_filename = os.path.join(directory, self.seriesID + '_' + str(image_counter).zfill(6) + '.csv')
                    else:
                        one_filename = os.path.join(directory, filename + '_' + str(image_counter).zfill(6) +'.csv')
                    if columnHeaders is None:
                        one_columHeaders = []
                        counter = 0
                        for _ in slice_image:
                            counter += 1
                            one_columHeaders.append("Column" + str(counter))
                    df = pd.DataFrame(np.transpose(slice_image), columns=one_columHeaders)
                    df.to_csv(one_filename, index=False)
                    image_counter += 1
        except Exception as e:
            print('Error in Series.export_as_csv: ' + str(e))
            logger.exception('Error in Series.export_as_csv: ' + str(e))


class Image:
    """This class corresponds to 1 DICOM file that belongs to its parent Subject, Study and Series.

        Parameters
        ----------
        objWeasel : the Weasel global variable
        subjectID : string
            This is the name or identification of the subject, which is stored in the "PatientID" DICOM tag.
        studyID : string
            This is the name or identification of the study, which is stored in the "StudyDescription" DICOM tag.
        seriesID : string
            This is the name or identification of the series, which is stored in the "SeriesDescription" DICOM tag.
        path : string
            This is the file path to the DICOM file represented in this Image() class.
        suffix : string (optional)
            This is the text to append to subjectID if a new Image() class is created.
    """
    __slots__ = ('objWeasel', 'subjectID', 'studyID', 'seriesID', 'path', 'seriesUID',
                 'studyUID', 'suffix', 'referencePath')
    def __init__(self, objWeasel, subjectID, studyID, seriesID, path, suffix=None):
        self.objWeasel = objWeasel
        self.subjectID = subjectID
        self.studyID = studyID
        self.seriesID = seriesID
        self.path = path
        self.seriesUID = self.SeriesUID
        self.studyUID = self.StudyUID
        self.suffix = '' if suffix is None else suffix
        self.referencePath = ''

    def __repr__(self):
       return '{}'.format(self.__class__.__name__)

    @property
    def parent(self):
        logger.info("Image.parent called")
        try:
            temp_series = Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, studyUID=self.studyUID, seriesUID=self.seriesUID)
            paths = []
            images_of_series = temp_series.children
            for image in images_of_series:
                paths.append(image.path)
            del temp_series, images_of_series
            return Series(self.objWeasel, self.subjectID, self.studyID, self.seriesID, listPaths=paths, studyUID=self.studyUID, seriesUID=self.seriesUID)
        except Exception as e:
            print('Error in Image.parent: ' + str(e))
            logger.exception('Error in Image.parent: ' + str(e))
    
    @staticmethod
    def newSeriesFrom(listImages, suffix='_Copy', series_id=None, series_name=None, series_uid=None):
        logger.info("Image.newSeriesFrom called")
        try:
            pathsList = [image.path for image in listImages]
            if series_id is None:
                series_id, _ = GenericDICOMTools.generateSeriesIDs(listImages[0].objWeasel, pathsList)
            if series_name is None:
                series_name = listImages[0].seriesID.split('_', 1)[1] + suffix
            if series_uid is None:
                _, series_uid = GenericDICOMTools.generateSeriesIDs(listImages[0].objWeasel, pathsList, seriesNumber=series_id)
            seriesID = str(series_id) + '_' + series_name
            newSeries = Series(listImages[0].objWeasel, listImages[0].subjectID, listImages[0].studyID, seriesID, seriesUID=series_uid, suffix=suffix)
            newSeries.referencePathsList = pathsList
            return newSeries
        except Exception as e:
            print('Error in Image.newSeriesFrom: ' + str(e))
            logger.exception('Error in Image.newSeriesFrom: ' + str(e))
        
    @property
    def label(self):
        logger.info("Image.label called")
        try:
            return self.objWeasel.objXMLReader.getImageLabel(self.subjectID, self.studyID, self.seriesID, imageName=self.path)
            #return self.objWeasel.treeView.returnImageName(self.subjectID, self.studyID, self.seriesID, self.path)
        except Exception as e:
            print('Error in Image.label: ' + str(e))
            logger.exception('Error in Image.label: ' + str(e))

    def new(self, suffix='_Copy', series=None):
        logger.info("Image.new called")
        try:
            if series is None:
                newImage = Image(self.objWeasel, self.subjectID, self.studyID, self.seriesID, '', suffix=suffix)
            else:
                newImage = Image(series.objWeasel, series.subjectID, series.studyID, series.seriesID, '', suffix=suffix)
            newImage.referencePath = self.path
            return newImage
        except Exception as e:
            print('Error in Image.new: ' + str(e))
            logger.exception('Error in Image.new: ' + str(e))

    def copy(self, suffix='_Copy', series=None, output_dir=None):
        logger.info("Image.copy called")
        try:
            if series is None:
                series_id = self.seriesID.split('_', 1)[0]
                series_name = self.seriesID.split('_', 1)[1]
                series_uid = self.seriesUID
                #suffix = self.suffix
            else:
                series_id = series.seriesID.split('_', 1)[0]
                series_name = series.seriesID.split('_', 1)[1]
                series_uid = series.seriesUID
                suffix = series.suffix
            newPath, newSeriesID = GenericDICOMTools.copyDICOM(self.objWeasel, self.path, series_id=series_id, series_uid=series_uid, series_name=series_name, suffix=suffix, output_dir=output_dir)
            copiedImage = Image(self.objWeasel, self.subjectID, self.studyID, newSeriesID, newPath, suffix=suffix)
            if series: series.add(copiedImage)
            return copiedImage
        except Exception as e:
            print('Error in Image.copy: ' + str(e))
            logger.exception('Error in Image.copy: ' + str(e))

    def delete(self):
        logger.info("Image.delete called")
        try:
            GenericDICOMTools.deleteDICOM(self.objWeasel, self.path)
            self.path = []
            self.referencePath = []
            self.subjectID = self.studyID = self.seriesID = ''
            # Delete the instance, such as del self???
        except Exception as e:
            print('Error in Image.delete: ' + str(e))
            logger.exception('Error in Image.delete: ' + str(e))

    def write(self, pixelArray, series=None, output_dir=None, value_range=None, parametric_map=None, colourmap=None):
        logger.info("Image.write called")
        try:
            if isinstance(value_range, list):
                pixelArray = np.nan_to_num(pixelArray, posinf=0, neginf=0)
                pixelArray = np.clip(pixelArray, value_range[0], value_range[1])
            else:
                list_values = np.unique(pixelArray).flatten()
                list_values = [x for x in list_values if np.isnan(x) == False]
                if np.isposinf(list_values[-1]) or np.isinf(list_values[-1]):
                    upper_value = list_values[-2]
                else:
                    upper_value = None
                if np.isneginf(list_values[0]) or np.isinf(list_values[0]):
                    lower_value = list_values[1]
                else:
                    lower_value = None
                pixelArray = np.nan_to_num(pixelArray, posinf=upper_value, neginf=lower_value)
            if os.path.exists(self.path):
                PixelArrayDICOMTools.overwritePixelArray(pixelArray, self.path) # Include Colourmap and Parametric Map
            else:
                if series is None:
                    series_id = self.seriesID.split('_', 1)[0]
                    series_name = self.seriesID.split('_', 1)[1]
                    series_uid = self.seriesUID
                else:
                    series_id = series.seriesID.split('_', 1)[0]
                    series_name = series.seriesID.split('_', 1)[1]
                    series_uid = series.seriesUID
                outputPath = PixelArrayDICOMTools.writeNewPixelArray(self.objWeasel, pixelArray, self.referencePath, self.suffix, series_id=series_id, series_name=series_name, series_uid=series_uid, parametric_map=parametric_map, output_dir=output_dir, colourmap=colourmap)
                self.path = outputPath[0]
                if series: series.add(self)
        except Exception as e:
            print('Error in Image.write: ' + str(e))
            logger.exception('Error in Image.write: ' + str(e))
        
    def read(self):
        return self.PydicomObject

    def save(self, PydicomObject):
        changeXML = False
        newSubjectID = self.subjectID
        newStudyID = self.studyID
        newSeriesID = self.seriesID
        if PydicomObject.SeriesDescription != self.PydicomObject.SeriesDescription or PydicomObject.SeriesNumber != self.PydicomObject.SeriesNumber:
            changeXML = True
            newSeriesID = str(PydicomObject.SeriesNumber) + "_" + str(PydicomObject.SeriesDescription)
        if PydicomObject.StudyDate != self.PydicomObject.StudyDate or PydicomObject.StudyTime != self.PydicomObject.StudyTime or PydicomObject.StudyDescription != self.PydicomObject.StudyDescription:
            changeXML = True
            newStudyID = str(PydicomObject.StudyDate) + "_" + str(PydicomObject.StudyTime).split(".")[0] + "_" + str(PydicomObject.StudyDescription)
        if PydicomObject.PatientID != self.PydicomObject.PatientID:
            changeXML = True
            newSubjectID = str(PydicomObject.PatientID)
        SaveDICOM_Image.saveDicomToFile(PydicomObject, output_path=self.path)
        if changeXML == True:
            self.objWeasel.objXMLReader.moveImageInXMLFile(self.subjectID, self.studyID, self.seriesID, newSubjectID, newStudyID, newSeriesID, self.path, '')
        # Only after updating the Element Tree (XML), we can change the instance values and save the DICOM file
        self.subjectID = newSubjectID
        self.studyID = newStudyID
        self.seriesID = newSeriesID

    @staticmethod
    def merge(listImages, series_id=None, series_name='NewSeries', series_uid=None, study_name=None, study_uid=None, patient_id=None, suffix='_Merged', overwrite=False, progress_bar=False):
        logger.info("Image.merge called")
        try:
            outputSeries = Image.newSeriesFrom(listImages, suffix=suffix, series_id=series_id, series_name=series_name, series_uid=series_uid)    
            outputPathList = GenericDICOMTools.mergeDicomIntoOneSeries(outputSeries.objWeasel, outputSeries.referencePathsList, series_uid=series_uid, series_id=series_id, series_name=series_name, study_name=study_name, study_uid=study_uid, patient_id=patient_id, suffix=suffix, overwrite=overwrite, progress_bar=progress_bar)
            outputSeries.images = outputPathList
            return outputSeries
        except Exception as e:
            print('Error in Image.merge: ' + str(e))
            logger.exception('Error in Image.merge: ' + str(e))
    
    def display(self):
        self.objWeasel.display(self)


    def plot(self, xlabel="X axis", ylabel="Y axis"):
        logger.info("Image.plot called")
        try:
            self.objWeasel.plot(self.path, self.seriesID, self.PixelArray[0], self.PixelArray[1], xlabel, ylabel)
        except Exception as e:
            print('Error in Image.plot: ' + str(e))
            logger.exception('Error in Image.plot: ' + str(e))

    @property
    def SeriesUID(self):
        if not self.path:
            self.seriesUID = None
        elif os.path.exists(self.path):
            self.seriesUID = ReadDICOM_Image.getImageTagValue(self.path, 'SeriesInstanceUID')
        else:
            self.seriesUID = None
        return self.seriesUID
    
    @property
    def StudyUID(self):
        if not self.path:
            self.studyUID = None
        elif os.path.exists(self.path):
            self.studyUID = ReadDICOM_Image.getImageTagValue(self.path, 'StudyInstanceUID')
        else:
            self.studyUID = None
        return self.studyUID
    
    def Metadata(self):
        logger.info("Image.Metadata called")
        try:
            self.objWeasel.displayMetadata(self.path)
        except Exception as e:
            print('Error in Image.Metadata: ' + str(e))
            logger.exception('Error in Image.Metadata: ' + str(e))

    @property
    def PixelArray(self):
        logger.info("Image.PixelArray called")
        try:
            pixelArray = PixelArrayDICOMTools.getPixelArrayFromDICOM(self.path)
            return pixelArray
        except Exception as e:
            print('Error in Image.PixelArray: ' + str(e))
            logger.exception('Error in Image.PixelArray: ' + str(e))

    def overlay_mask(self, maskInstance):
        """Returns the PixelArray masked.
           Usage example:
           ''' 
            for image in list_images:
                if "ROI_mask" in image.label:
                    mask_image = image
                if "DWI" in image.label:
                    main_image = image
            masked_array = main_image.overlay_mask(mask_image)
        """
        logger.info("Image.Mask called")
        try:
            if isinstance(maskInstance, Image):
                #for index, dicomFile in enumerate(targetPath):
                tempArray = np.zeros(np.shape(self.PixelArray))
                dataset_original = self.PydicomObject
                dataset = maskInstance.PydicomObject
                mask_array = maskInstance.PixelArray
                mask_array[mask_array != 0] = 1
                affine_results = ReadDICOM_Image.mapMaskToImage(mask_array, dataset, dataset_original)
                if affine_results:
                    coords = zip(*affine_results)
                    tempArray[tuple(coords)] = list(np.ones(len(affine_results)).flatten())
                return np.transpose(tempArray) * self.PixelArray
            elif isinstance(maskInstance, Series):
                tempArray = np.zeros(np.shape(self.PixelArray))
                for maskFile in maskInstance.images:
                    dataset_original = self.PydicomObject
                    dataset = ReadDICOM_Image.getDicomDataset(maskFile)
                    mask_array = ReadDICOM_Image.getPixelArray(dataset)
                    mask_array[mask_array != 0] = 1
                    affine_results = ReadDICOM_Image.mapMaskToImage(mask_array, dataset, dataset_original)
                    if affine_results:
                        coords = zip(*affine_results)
                        tempArray[tuple(coords)] = list(np.ones(len(affine_results)).flatten())
                return np.transpose(tempArray) * self.PixelArray
        except Exception as e:
            print('Error in Image.Mask: ' + str(e))
            logger.exception('Error in Image.Mask: ' + str(e))

    def write_mask(self, mask_array, label=None):
        logger.info("Image.write_mask called")
        try:
            if label is not None:
                self.suffix = "_" + label
            self.write(mask_array, parametric_map="SEG")
        except Exception as e:
            print('Error in Image.write_mask: ' + str(e))
            logger.exception('Error in Image.write_mask: ' + str(e))
    
    @property
    def ROIindices(self):
        logger.info("Image.ROIindices called")
        try:
            tempImage = self.PixelArray
            tempImage[tempImage != 0] = 1
            return np.transpose(np.where(tempImage == 1))
        except Exception as e:
            print('Error in Image.ROIindices: ' + str(e))
            logger.exception('Error in Image.ROIindices: ' + str(e))

    @property
    def TopLeftCorner(self):
        logger.info("Image.TopLeftCorner called")
        try:
            return ReadDICOM_Image.getTopLeftCorner(self.PydicomObject)
        except Exception as e:
            print('Error in Image.TopLeftCorner: ' + str(e))
            logger.exception('Error in Image.TopLeftCorner: ' + str(e))

    @property
    def Affine(self):
        logger.info("Image.TopLeftCorner called")
        try:
            return ReadDICOM_Image.returnAffineArray(self.path)
        except Exception as e:
            print('Error in Image.Affine: ' + str(e))
            logger.exception('Error in Image.Affine: ' + str(e)) 
    
    def get_value(self, tag):
        logger.info("Image.get_value called")
        try:
            if isinstance(tag, list):
                outputValuesList = []
                for ind_tag in tag:
                    if (ind_tag == "SliceLocation" or ind_tag == (0x0020,0x1041)) and not hasattr(self.PydicomObject, "SliceLocation"): ind_tag = (0x2001, 0x100a)
                    outputValuesList.append(ReadDICOM_Image.getImageTagValue(self.path, ind_tag))
                return outputValuesList
            else:
                if (tag == "SliceLocation" or tag == (0x0020,0x1041)) and not hasattr(self.PydicomObject, "SliceLocation"): tag = (0x2001, 0x100a)
                return ReadDICOM_Image.getImageTagValue(self.path, tag)
        except Exception as e:
            print('Error in Image.get_value: ' + str(e))
            logger.exception('Error in Image.get_value: ' + str(e))

    def set_value(self, tag, newValue):
        logger.info("Image.set_value called")
        try:
            comparisonDicom = self.PydicomObject
            changeXML = False
            # Not necessary new IDs, but they may be new. The changeXML flag coordinates that.
            oldSubjectID = self.subjectID
            oldStudyID = self.studyID
            oldSeriesID = self.seriesID
            # Set tag commands
            if isinstance(tag, list) and isinstance(newValue, list):
                for index, ind_tag in enumerate(tag):
                    GenericDICOMTools.editDICOMTag(self.path, ind_tag, newValue[index])
            else:
                GenericDICOMTools.editDICOMTag(self.path, tag, newValue)
            # Consider the case where XML fields are changed
            if comparisonDicom.SeriesDescription != self.PydicomObject.SeriesDescription or comparisonDicom.SeriesNumber != self.PydicomObject.SeriesNumber:
                changeXML = True
                newSeriesID = str(self.PydicomObject.SeriesNumber) + "_" + str(self.PydicomObject.SeriesDescription)
                self.seriesID = newSeriesID
            else:
                newSeriesID = oldSeriesID
            if comparisonDicom.StudyDate != self.PydicomObject.StudyDate or comparisonDicom.StudyTime != self.PydicomObject.StudyTime or comparisonDicom.StudyDescription != self.PydicomObject.StudyDescription:
                changeXML = True
                newStudyID = str(self.PydicomObject.StudyDate) + "_" + str(self.PydicomObject.StudyTime).split(".")[0] + "_" + str(self.PydicomObject.StudyDescription)
                self.studyID = newStudyID
            else:
                newStudyID = oldStudyID
            if comparisonDicom.PatientID != self.PydicomObject.PatientID:
                changeXML = True
                newSubjectID = str(self.PydicomObject.PatientID)
                self.subjectID = newSubjectID
            else:
                newSubjectID = oldSubjectID
            if changeXML == True:
                self.objWeasel.objXMLReader.moveImageInXMLFile(oldSubjectID, oldStudyID, oldSeriesID, newSubjectID, newStudyID, newSeriesID, self.path, '')
        except Exception as e:
            print('Error in Image.set_value: ' + str(e))
            logger.exception('Error in Image.set_value: ' + str(e))
        
    def __getitem__(self, tag):
        return self.get_value(tag)

    def __setitem__(self, tag, value):
        self.set_value(tag, value)

    @property
    def PydicomObject(self):
        if self.path:
            return PixelArrayDICOMTools.getDICOMobject(self.path)
        else:
            return []

    def export_as_nifti(self, directory=None, filename=None):
        logger.info("Image.export_as_nifti called")
        try:
            if directory is None: directory=os.path.dirname(self.path)
            if filename is None: filename=self.seriesID
            dicomHeader = nib.nifti1.Nifti1DicomExtension(2, self.PydicomObject)
            niftiObj = nib.Nifti1Image(np.flipud(np.rot90(np.transpose(self.PixelArray))), affine=self.Affine)
            # The transpose is necessary in this case to be in line with the rest of Weasel.
            niftiObj.header.extensions.append(dicomHeader)
            nib.save(niftiObj, directory + '/' + filename + '.nii.gz')
        except Exception as e:
            print('Error in Image.export_as_nifti: ' + str(e))
            logger.exception('Error in Image.export_as_nifti: ' + str(e))

    def export_as_csv(self, directory=None, filename=None, columnHeaders=None):
        logger.info("Image.export_as_csv called")
        try:
            if directory is None: directory = os.path.dirname(self.images[0])
            if filename is None:
                filename = os.path.join(directory, self.seriesID + '.csv')
            else:
                filename = os.path.join(directory, filename + '.csv')
            table = self.PixelArray
            if columnHeaders is None:
                columnHeaders = []
                counter = 0
                for _ in table:
                    counter += 1
                    columnHeaders.append("Column" + str(counter))
            df = pd.DataFrame(np.transpose(table), columns=columnHeaders)
            df.to_csv(filename, index=False)
        except Exception as e:
            print('Error in Image.export_as_csv: ' + str(e))
            logger.exception('Error in Image.export_as_csv: ' + str(e))
