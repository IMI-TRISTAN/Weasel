

def main(weasel):
    try:
        dicomList = weasel.series()
        if len(dicomList) == 0: dicomList = weasel.images()
        if len(dicomList) == 0: return
        local_path = weasel.select_folder()
        if local_path is None: return
        for i, series in enumerate(dicomList):
            weasel.progress_bar(max=len(dicomList), index=i+1, msg="Saving series " + series.label + " to CSV")
            series.export_as_csv(directory=local_path)
        weasel.close_progress_bar()
        weasel.information(msg="Selected series successfully saved as CSV", title="Export to CSV")
    except Exception as e:
        # Record error message in the log and prints in the terminal
        weasel.log_error('Error in function File__ExportToCSV.main: ' + str(e))
        # If we want to show the message in the GUI
        weasel.error(msg=str(e), title="Error Exporting to CSV")