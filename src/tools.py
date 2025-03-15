import os
import shutil as sh


class Tools:

    @staticmethod
    def createFolderStructure(root: str, missing):
        missingFolder = root
        for folder in missing:
            missingFolder = os.path.join(missingFolder, folder)
            try:
                os.mkdir(missingFolder)
            except OSError as error:
                if error.errno != 17:  # 17: "File already exists"
                    print(error)

    @staticmethod
    def cleanFolder(dir_demux: str):
        for content in os.listdir(dir_demux):
            contentPath = os.path.join(dir_demux, content)
            if os.path.isfile(contentPath):
                os.remove(contentPath)
            else:
                sh.rmtree(contentPath)
