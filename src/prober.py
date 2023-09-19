import subprocess as sp

class prober:

    __streamSuffix = '[/STREAM]\n'

    def __init__(self, limitedToAudio: bool = True):
        if limitedToAudio:
            self.__command: str = 'ffprobe -v error -show_streams -select_streams a -show_entries stream=index,codec_name,codec_type,channels,start_time:stream_tags=language:disposition=default'
        else:
            self.__command: str = 'ffprobe -v error -show_entries stream=index,codec_name,codec_type,channels:stream_tags=language,filename:disposition=default,forced'

    def probe(self, filepath : str) -> list[str]:
        ffprobeCommand = f'{self.__command} \"{filepath}\"'
        runResult = sp.run(ffprobeCommand, capture_output=True, shell=True, encoding='utf-8')
        if(runResult.stdout == ''):
            raise Exception(runResult.stderr)
        
        list_Stdout = runResult.stdout.rsplit(sep='[STREAM]\n')
        list_streams = []
        for parte in list_Stdout:
            parte = parte.removesuffix(prober.__streamSuffix)
            if parte != '':
                list_streams += parte,
        del list_Stdout
        return list_streams
