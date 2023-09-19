import os
import shutil as sh

class tools:

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

    @staticmethod
    def hasSurround(streams: list[str]):
        for stream in streams:
            stream_dict = {}
            infos = stream.rsplit(sep='\n')
            infos.remove('')
            for info in infos:
                dict_entry = info.rsplit(sep='=')
                stream_dict[dict_entry[0]] = dict_entry[1]

            if stream_dict['codec_type'] == 'audio' and stream_dict['channels'] == '6':
                return True
        return False
