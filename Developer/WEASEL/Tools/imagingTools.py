import numpy as np
import pydicom
from skimage.transform import resize


#INSERT A METHOD TO DEAL WITH MOSAIC PIXEL ARRAYS
#INSERT MOSAIC IMAGE CONDITION HERE / OR AT IMAGINGTOOLS.PY

def resizePixelArray(pixelArray, pixelSpacing, reconstPixel=None):
    """Resizes the given array, using reconstPixel as reference of the resizing""" 
    # Resample Data / Don't forget to resample the 128x128 of GE
    # This is so that data shares the same resolution and sizing

    if reconstPixel is not None:
        fraction = reconstPixel / pixelSpacing
    else:
        fraction = 1
    
    # What happens to SliceSpacing?!
    if len(np.shape(pixelArray)) == 3:
        pixelArray = resize(pixelArray, (pixelArray.shape[0] // fraction, pixelArray.shape[1] // fraction, pixelArray.shape[2]), anti_aliasing=True)
    elif len(np.shape(pixelArray)) == 4:
        pixelArray = resize(pixelArray, (pixelArray.shape[0] // fraction, pixelArray.shape[1] // fraction, pixelArray.shape[2], pixelArray.shape[3]), anti_aliasing=True)
    elif len(np.shape(pixelArray)) == 5:
        pixelArray = resize(pixelArray, (pixelArray.shape[0] // fraction, pixelArray.shape[1] // fraction, pixelArray.shape[2], pixelArray.shape[3], pixelArray.shape[4]), anti_aliasing=True)
    elif len(np.shape(pixelArray)) == 6:
        pixelArray = resize(pixelArray, (pixelArray.shape[0] // fraction, pixelArray.shape[1] // fraction, pixelArray.shape[2], pixelArray.shape[3], pixelArray.shape[4], pixelArray.shape[5]), anti_aliasing=True)

    return pixelArray


def formatArrayForAnalysis(volumeArray, numAttribute, dataset, dimension='2D', transpose=False, resize=None):
    """Formats the given array in a structured manner according to the given flags"""

    if dimension == '3D':
        volumeArray = np.squeeze(np.reshape(volumeArray, (int(np.shape(volumeArray)[0]/numAttribute), numAttribute, np.shape(volumeArray)[1])))
    elif dimension == '4D':
        volumeArray = np.squeeze(np.reshape(volumeArray, (int(np.shape(volumeArray)[0]/numAttribute), numAttribute, np.shape(volumeArray)[1], np.shape(volumeArray)[2])))
    elif dimension == '5D':
        volumeArray = np.squeeze(np.reshape(volumeArray, (int(np.shape(volumeArray)[0]/numAttribute), numAttribute, np.shape(volumeArray)[1], np.shape(volumeArray)[2], np.shape(volumeArray)[3])))
    elif dimension == '6D':
        volumeArray = np.squeeze(np.reshape(volumeArray, (int(np.shape(volumeArray)[0]/numAttribute), numAttribute, np.shape(volumeArray)[1], np.shape(volumeArray)[2], np.shape(volumeArray)[3], np.shape(volumeArray)[4])))

    if transpose == True:
        volumeArray = np.transpose(volumeArray)
    
    if hasattr(dataset, 'PerFrameFunctionalGroupsSequence'):
        pixelSpacing = dataset.PerFrameFunctionalGroupsSequence[0].PixelMeasuresSequence[0].PixelSpacing[0]
    else: # For normal DICOM, slicelist is a list of slice locations in mm.
        pixelSpacing = dataset.PixelSpacing[0]

    pixelArray = resizePixelArray(volumeArray, pixelSpacing, reconstPixel=resize)
    del volumeArray, pixelSpacing
    return pixelArray

# I called numAttribute because it might be others than Slices - Here's a pseudo example
#pixelArray = formatArrayForAnalysis(volumeArray, numberSlices, dataset, dimension='4D', transpose=True)
#pixelArray_2 = formatArrayForAnalysis(pixelArray, numberEchoes, dataset, dimension='5D', transpose=False)
#pixelArray_3 = formatArrayForAnalysis(pixelArray, numberBValues, dataset, dimension='6D', transpose=False, resize=3)

# MAYBE A def formatArrayForSaving? THAT WOULD MAKE SENSE AND MAKE THINGS EASIER