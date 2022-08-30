"""
Creates a subwindow that displays a DICOM image's metadata.
"""
    
import logging
logger = logging.getLogger(__name__)

from Displays.ViewMetaData import DisplayMetaDataSubWindow

def main(weasel):
    try:
        logger.info("View__DICOMheader called")
        print("weasel.series()={}".format(weasel.series()))
        series_list = weasel.series()
        if series_list == []: 
            for img in weasel.images(msg = 'No images checked'):
                DisplayMetaDataSubWindow(weasel, "Metadata for image {}".format(img.label), img.read())
        else:
            for series in series_list:
                img = series.children[0]
                DisplayMetaDataSubWindow(weasel, "Metadata for image {}".format(img.label), img.read())
    except (IndexError, AttributeError):
        weasel.information(msg="Select either a series or an image", title="View DICOM header")
    except Exception as e:
        print('Error in View__DICOMheader: ' + str(e))
        logger.error('Error in View__DICOMheader: ' + str(e))