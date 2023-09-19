import subprocess as sp
import multiprocessing as mp
import os

class downmixer:

    def __init__(self, algorithm: str):
        self.__downmixAlgorithm: str = algorithm

    def downmix(self, filepath: str, codec: str) -> str:
        if codec == 'dts':
            codec = 'ac3'
        if codec == 'aac':
            aac_fast = '-aac_coder fast'
        else:
            aac_fast = ''
        filenameSeparated = os.path.basename(filepath).rsplit(sep='.')
        dirpath = os.path.dirname(filepath)
        outputFileNoExt = os.path.join(dirpath, ''.join(filenameSeparated[:-1]))

        downmixCommand = f'ffmpeg -y -i \"{filepath}\" -c {codec} {aac_fast} -af {self.__downmixAlgorithm} \"{outputFileNoExt}_downmix.{codec}\"'
        try:
            sp.run(downmixCommand, capture_output=True, shell=True, check=True, encoding='utf-8')
            os.remove(filepath)
        except sp.SubprocessError as error:
            print(error.stderr)
        
        return f'{outputFileNoExt}_downmix.{codec}'
