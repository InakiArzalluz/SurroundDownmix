import os
import platform
from src.tools import Tools
from src.prober import Prober
from src.remuxer import Remuxer
from src.remuxerFactory import RemuxerFactory

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

    prober_inst = Prober(limitedToAudio=True)
    rem_factory = RemuxerFactory()
    remuxer_inst: Remuxer = rem_factory.getRemuxer('mkvmerge', 'atscboost')

    for root, dirs, files in os.walk(dir_inputs):
        for filename in files:
            missingStructure = root[len(dir_inputs)+1:].split(os.sep)
            Tools.createFolderStructure(dir_remux, missingStructure)

            filepath = os.path.join(root, filename)
            remuxLocation = os.path.join(dir_remux, os.path.join(root[len(dir_inputs)+1:]))
            newLocation = os.path.join(remuxLocation, filename)

            # TODO: I'm only limited to mkv if it's using mkvmerge
            # it should still check the file type, or it would try
            # to process ANY file
            if filename.rsplit(sep='.')[-1] == 'mkv':
                print('---------------------------------------')
                print("".join(["Processing ", filepath[len(dir_inputs)-8:]]))

                if (prober_inst.has_surround(filepath)):
                    remuxer_inst.remux(filepath, newLocation)
                else:
                    os.replace(filepath, newLocation)
            else:
                os.replace(filepath, newLocation)

    print('----------------- DONE -----------------')
    if platform.system() == 'Windows':
        os.system('pause')
    else:
        os.system('read -p "Press any key to exit ..."')
