import os
import platform
from src.tools import tools
from src.prober import prober
from src.remuxer import remuxer
from src.remuxerFactory import remuxerFactory

parentFolder = os.getcwd()
dir_inputs = os.path.join(parentFolder, 'A-Inputs')
dir_remux = os.path.join(parentFolder, 'Remux')


if __name__ == '__main__':
    foldersToCreate = (dir_inputs, dir_remux)
    for folder in foldersToCreate:
        try:
            os.mkdir(folder)
        except OSError as error:
            if error.errno != 17:
                print(error)
    
    for root, dirs, files in os.walk(dir_inputs):
        for filename in files:
            missingStructure = root[len(dir_inputs)+1:].split(os.sep)
            tools.createFolderStructure(dir_remux, missingStructure)

            filepath = os.path.join(root, filename)
            remuxLocation = os.path.join(dir_remux, os.path.join(root[len(dir_inputs)+1:]))
            newLocation = os.path.join(remuxLocation, filename)

            if filename.rsplit(sep='.')[-1] == 'mkv': #Solo estoy limitado si es con mkvmerge
                print('\033[92m---------------------------------------------------------------------------------------------------\033[0m')
                print("".join(["Processing ", filepath[len(dir_inputs)-8:]]))

                prober_inst = prober(limitedToAudio = True)
                
                rem_factory = remuxerFactory()
                remuxer = rem_factory.getRemuxer('ffmpeg','atscboost')
                
                list_streams = prober_inst.probe(filepath)
                if(tools.hasSurround(list_streams)):
                    remuxer.remux(filepath, newLocation)
                else:
                    os.replace(filepath, newLocation)
            else:
                os.replace(filepath, newLocation)
    print('\033[92m--------------------------------------------- DONE ---------------------------------------------\033[0m')
    if platform.system() == 'Windows':
        os.system('pause')
    else:
        os.system('read -p "Press any key to exit ..."')
