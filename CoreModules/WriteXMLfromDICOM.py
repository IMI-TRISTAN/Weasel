import os
from pyqtgraph.Qt import QtCore, QtGui
import pydicom
import xml.etree.ElementTree as ET
import datetime
import numpy as np
import re
from collections import defaultdict
from xml.dom import minidom
import iBeatImport


def select_path():
    """This method opens a Dialog Box that allows the user to choose the folder containing the MRI scan.
        The path to the folder is what is returned in this method.
    """
    try:
        cwd = os.getcwd()
        app = QtGui.QApplication([])  # pylint: disable=unused-variable
        scan_directory = QtGui.QFileDialog.getExistingDirectory(None, 'Select the'
                   ' directory containing the scan', cwd, QtGui.QFileDialog.ShowDirsOnly)
        if len(scan_directory) == 0:
            raise SystemExit('No folder selected')

        return scan_directory
    except Exception as e:
        print('Error in WriteXMLfromDICOM.select_path: ' + str(e))
        

def get_files_info(scan_directory):
    """This method returns the number of files and subfolders in a folder. It doesn't mean that they are all DICOM.
    """
    try:
        number_files = 0
        number_folders = 0
        for _, sub_folders, file_list in os.walk(scan_directory):
            number_files += len(file_list)
            number_folders += len(sub_folders)
        if number_files == 0:
            raise FileNotFoundError('No files present in the selected folder')
        return number_files, number_folders
    except Exception as e:
            print('Error in WriteXMLfromDICOM.get_files_info: ' + str(e))


def atof(text):
    """ This function is auxiliary for the natural sorting of the paths names"""
    try:
        retval = float(text)
    except ValueError:
        retval = text
    return retval


def natural_keys(text):
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    float regex comes from https://stackoverflow.com/a/12643073/190597
    """
    return [ atof(c) for c in re.split(r'[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)', text) ] 


def get_scan_data(scan_directory):
    """This method opens all DICOM files in the provided path recursively and saves 
        each file individually as a variable into a list/array.
    """
    try:
        list_dicom = list()
        list_paths = list()
        for dir_name, _, file_list in os.walk(scan_directory):
            file_list.sort(key=natural_keys)
            for filename in file_list:
                try:
                    list_dicom.append(pydicom.dcmread(
                        os.path.join(dir_name, filename)))
                    list_paths.append(os.path.join(dir_name, filename))
                except:
                    continue
        if len(list_dicom) == 0:
            raise FileNotFoundError(
                'No DICOM files present in the selected folder')

        return list_dicom, list_paths
    except Exception as e:
            print('Error in WriteXMLfromDICOM.get_scan_data: ' + str(e))


def get_studies_series(list_dicom):
    try:
        xml_dict = defaultdict(list)
        for file in list_dicom:
            if len(file.dir("SeriesDescription"))>0:
                xml_dict[str(file.PatientID) + "_" + str(file.StudyDate)].append(str(file.SeriesDescription) + "_" + str(file.SeriesNumber))
            elif len(file.dir("SequenceName"))>0 & len(file.dir("PulseSequenceName"))==0:
                xml_dict[str(file.PatientID) + "_" + str(file.StudyDate)].append(str(file.SequenceName) + "_" + str(file.SeriesNumber))
            elif len(file.dir("ProtocolName"))>0:
                xml_dict[str(file.PatientID) + "_" + str(file.StudyDate)].append(str(file.ProtocolName) + "_" + str(file.SeriesNumber))
            else:
                xml_dict[str(file.PatientID) + "_" + str(file.StudyDate)].append("No Sequence Name_" + str(file.SeriesNumber))
        for study in xml_dict:
            xml_dict[study] = np.unique(xml_dict[study])

        return xml_dict
    except Exception as e:
            print('Error in WriteXMLfromDICOM.get_studies_series: ' + str(e))


def get_studies_series_iBEAT(list_dicom):
    try:
        xml_dict = defaultdict(list)
        for file in list_dicom:
            individualStudy, individualSeries = iBeatImport.getScanInfo(file)
            xml_dict[individualStudy].append(individualSeries)
        for study in xml_dict:
            xml_dict[study] = np.unique(xml_dict[study])

        return xml_dict
    except Exception as e:
            print('Error in WriteXMLfromDICOM.get_studies_series_iBEAT: ' + str(e))


def open_dicom_to_xml(xml_dict, list_dicom, list_paths):
    """This method opens all DICOM files in the given list and saves 
        information from each file individually to an XML tree/structure.
    """
    try:    
        DICOM_XML_object = ET.Element('DICOM')
        comment = ET.Comment('WARNING: PLEASE, DO NOT MODIFY THIS FILE \n This .xml file is automatically generated by a script that reads folders containing DICOM files. \n Any changes can affect the software\'s functionality, so do them at your own risk')
        DICOM_XML_object.append(comment)

        for study in xml_dict:
            study_element = ET.SubElement(DICOM_XML_object, 'study')
            study_element.set('id',study)
            for series in xml_dict[study]:
                series_element = ET.SubElement(study_element, 'series')
                series_element.set('id', series)
                series_element.set('parentID', '')

        for index, file in enumerate(list_dicom):
            study_search_string = "./*[@id='" + str(file.PatientID) + "_" + str(file.StudyDate) + "']"
            series_root = DICOM_XML_object.find(study_search_string)
            if len(file.dir("SeriesDescription"))>0:
                series_search_string = "./*[@id='"+ str(file.SeriesDescription) + "_" + str(file.SeriesNumber) + "']"
            elif len(file.dir("SequenceName"))>0 & len(file.dir("PulseSequenceName"))==0:
                series_search_string = "./*[@id='"+ str(file.SequenceName) + "_" + str(file.SeriesNumber) + "']"
            elif len(file.dir("ProtocolName"))>0:
                series_search_string = "./*[@id='"+ str(file.ProtocolName) + "_" + str(file.SeriesNumber) + "']"
            else:
                series_search_string = "./*[@id='No Sequence Name_" + str(file.SeriesNumber) + "']"
            image_root = series_root.find(series_search_string)
            image_element = ET.SubElement(image_root, 'image')
            name = ET.SubElement(image_element, 'name')
            time = ET.SubElement(image_element, 'time')
            date = ET.SubElement(image_element, 'date')
            name.text =  os.path.normpath(list_paths[index])
            # The next lines save the time and date to XML - They consider multiple/eventual formats
            if len(file.dir("AcquisitionTime"))>0:
                try:
                    time.text = datetime.datetime.strptime(file.AcquisitionTime, '%H%M%S').strftime('%H:%M')
                except:
                    time.text = datetime.datetime.strptime(file.AcquisitionTime, '%H%M%S.%f').strftime('%H:%M')
                date.text = datetime.datetime.strptime(file.AcquisitionDate, '%Y%m%d').strftime('%d/%m/%Y')
            elif len(file.dir("SeriesTime"))>0:
                # It means it's Enhanced MRI
                try:
                    time.text = datetime.datetime.strptime(file.SeriesTime, '%H%M%S').strftime('%H:%M')
                except:
                    time.text = datetime.datetime.strptime(file.SeriesTime, '%H%M%S.%f').strftime('%H:%M')
                date.text = datetime.datetime.strptime(file.SeriesDate, '%Y%m%d').strftime('%d/%m/%Y')
            else:
                time.text = datetime.datetime.strptime('000000', '%H%M%S').strftime('%H:%M')
                date.text = datetime.datetime.strptime('20000101', '%Y%m%d').strftime('%d/%m/%Y')

        return DICOM_XML_object
    except Exception as e:
            print('Error in WriteXMLfromDICOM.open_dicom_to_xml: ' + str(e))


def open_dicom_to_xml_iBEAT(xml_dict, list_dicom, list_paths):
    """This method opens all DICOM files in the given list and saves 
        information from each file individually to an XML tree/structure.
    """
    try:    
        DICOM_XML_object = ET.Element('DICOM')
        comment = ET.Comment('WARNING: PLEASE, DO NOT MODIFY THIS FILE \n This .xml file is automatically generated by a script that reads folders containing DICOM files. \n Any changes can affect the software\'s functionality, so do them at your own risk')
        DICOM_XML_object.append(comment)

        for study in xml_dict:
            study_element = ET.SubElement(DICOM_XML_object, 'study')
            study_element.set('id',study)
            for series in xml_dict[study]:
                series_element = ET.SubElement(study_element, 'series')
                series_element.set('id', series)
                series_element.set('parentID', '')

        for index, file in enumerate(list_dicom):
            study_search_string, series_search_string = iBeatImport.getScanInfo(file)
            series_root = DICOM_XML_object.find(study_search_string)
            image_root = series_root.find(series_search_string)
            image_element = ET.SubElement(image_root, 'image')
            name = ET.SubElement(image_element, 'name')
            time = ET.SubElement(image_element, 'time')
            date = ET.SubElement(image_element, 'date')
            name.text =  os.path.normpath(list_paths[index])
            # The next lines save the time and date to XML - They consider multiple/eventual formats
            if len(file.dir("AcquisitionTime"))>0:
                try:
                    time.text = datetime.datetime.strptime(file.AcquisitionTime, '%H%M%S').strftime('%H:%M')
                except:
                    time.text = datetime.datetime.strptime(file.AcquisitionTime, '%H%M%S.%f').strftime('%H:%M')
                date.text = datetime.datetime.strptime(file.AcquisitionDate, '%Y%m%d').strftime('%d/%m/%Y')
            elif len(file.dir("SeriesTime"))>0:
                # It means it's Enhanced MRI
                try:
                    time.text = datetime.datetime.strptime(file.SeriesTime, '%H%M%S').strftime('%H:%M')
                except:
                    time.text = datetime.datetime.strptime(file.SeriesTime, '%H%M%S.%f').strftime('%H:%M')
                date.text = datetime.datetime.strptime(file.SeriesDate, '%Y%m%d').strftime('%d/%m/%Y')
            else:
                time.text = datetime.datetime.strptime('000000', '%H%M%S').strftime('%H:%M')
                date.text = datetime.datetime.strptime('20000101', '%Y%m%d').strftime('%d/%m/%Y')

        return DICOM_XML_object
    except Exception as e:
            print('Error in WriteXMLfromDICOM.open_dicom_to_xml_iBEAT: ' + str(e))


def create_XML_file(DICOM_XML_object, scan_directory):
    """This method creates a new XML file with the based on the structure of the selected DICOM folder"""
    try:
        xmlstr = ET.tostring(DICOM_XML_object, encoding='utf-8')
        XML_data = minidom.parseString(xmlstr).toprettyxml(encoding="utf-8", indent="  ")
        filename = os.path.basename(os.path.normpath(scan_directory)) + ".xml"
        with open(os.path.join(scan_directory, filename), "wb") as f:
            f.write(XML_data)  
        return os.path.join(scan_directory, filename)
    except Exception as e:
            print('Error in WriteXMLfromDICOM.create_XML_file: ' + str(e))


def main():
    generic_path = select_path()
    scans, paths = get_scan_data(generic_path)
    dictionary = get_studies_series(scans)
    xml = open_dicom_to_xml(dictionary, scans, paths)
    create_XML_file(xml, generic_path)


if __name__ == '__main__':
        main()