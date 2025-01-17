"""
Create new series holding images of the same slice location. If images are selected from multiple studies then a new series is created inside each study.
"""

def enable(weasel):
    return False

def main(weasel):
    images = weasel.images()
    studies = images.parent.parent
    for study in studies:
        imgs = study.all_images
        new_study_description = 'Sorted by slice location_' + study.studyID
        series_number = 1
        for loc in weasel.unique_elements(imgs.get_value("SliceLocation")):
            imgs_loc = imgs.where("SliceLocation", "==", loc)
            series = imgs_loc.merge(series_number=series_number, series_name='Slice location [' + str(loc) + ']', study_name=new_study_description, progress_bar=False, overwrite=False)
            series_number += 1
            # loc can be series_number actually
    weasel.refresh()


def suggestion(weasel):
    # Get all images checked by the user
    images = weasel.images()
    # Loop over the studies that the images are part of
    for study in images.studies():
        # Get the part of the images that are in the study
        imgs = images.of(study)
        # Create a new study
        new_study = study.new_sibling(StudyDescription = 'Sorted by slice location')
        # Loop over the unique slice locations
        for loc in imgs.SliceLocation.unique():
            # get the images at slice location loc
            imgs_loc = imgs.where("SliceLocation" == loc)
            # store those images in a new series of the new study
            series = new_study.new_child(imgs_loc)
            # rename the series with the slice location
            series.SeriesDescription = 'Slice location [' + str(loc) + ']'
            
