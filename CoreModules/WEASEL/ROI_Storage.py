class ROIs():
    def __init__(self):
        self.dictPathCoords = {}
        self.dictMasks = {}
        self.regionNumber = 0
        self.prevRegionName = None


    def addRegion(self, pathCoords, mask):
        #get next ROI name
        self.regionNumber += 1
        regionName = "region" + str(self.regionNumber)
        self.dictPathCoords[regionName] = pathCoords
        self.dictMasks[regionName] = mask


    def getListOfRegions(self):
        return list(self.dictMasks)


    def setPreviousRegionName(self, regionName):
        self.prevRegionName = regionName


    def getMask(self, regionName):
        return self.dictMasks[regionName]


    def getPathCoords(self, regionName):
        return self.dictPathCoords[regionName]


    def renameDictionaryKey(self, newName):
        try:
            oldName = self.prevRegionName
            if oldName in self.dictMasks:
                pass
            else:
                oldName = newName[0 : len(newName)-1]

            self.dictPathCoords[newName] = self.dictPathCoords.pop(oldName)
            self.dictMasks[newName] = self.dictMasks.pop(oldName)
        except Exception as e:
            print('Error in ROI_Storage.renameDictionaryKey: ' + str(e))
           


       # numpy.logical_or(x1, x2, /, out=None, *, where=True, casting='same_kind', order='K', dtype=None, subok=True[, signature, extobj]) = <ufunc 'logical_or'>¶
#Compute the truth value of x1 OR x2 element-wise.