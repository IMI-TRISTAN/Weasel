from Developer.DeveloperTools import UserInterfaceTools
from Developer.External.ukat.mapping.b0 import B0
import re
#***************************************************************************
import numpy as np
FILE_SUFFIX = '_B0Map'
#***************************************************************************

def isSeriesOnly(self):
    #This functionality only applies to a series of DICOM images
    return True


def main(objWeasel):
    ui = UserInterfaceTools(objWeasel)
    # Get all series in the Checkboxes
    seriesList = ui.getCheckedSeries()
    for series in seriesList:
        seriesPhase = series.getPhase
        if checkB0(seriesPhase):
            seriesPhase.sort("SliceLocation")
            seriesPhase.sort("EchoTime")
            te = np.unique(seriesPhase.EchoTimes)
            pixelArray = seriesPhase.PixelArray # (32, 256, 256)
            reformatShape = (len(te), int(np.shape(pixelArray)[0]/len(te)), np.shape(pixelArray)[1], np.shape(pixelArray)[2])
            phase = np.transpose(pixelArray.reshape(reformatShape)) # (2, 16, 256, 256) => (256, 256, 16, 2) after the np.transpose
            # Initialise B0 mapping object
            mapper_B0 = B0(phase, te, unwrap=True)
            b0map = mapper_B0.b0_map # (256, 256, 16)
            newSeries = seriesPhase.new(suffix=FILE_SUFFIX)
            newSeries.write(np.transpose(b0map)) # (16, 256, 256)
            # Refresh the UI screen
            ui.refreshWeasel(new_series_name=newSeries.seriesID)
            # Display series
            newSeries.DisplaySeries()
        else:
            ui.showMessageWindow(msg='The checked series doesn\'t meet the criteria to calculate the B0 Map', title='NOT POSSIBLE TO CALCULATE B0 MAP')


def checkB0(series):
    numberEchoes = len(np.unique(series.EchoTimes))
    if (numberEchoes >= 2) and (re.match(".*b0.*", series.seriesID.lower())):
        return True
    else:
        return None
