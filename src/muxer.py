import os
import subprocess as sp

class muxer:

    def mux(self, inputFile, remuxedFile, dict_dict_stream):
        pass

class mkvmerge_mux(muxer):

    def mux(self, inputFile, remuxedFile, dict_dict_stream):
        delay = arguments = ''
        for key in dict_dict_stream.keys():
            if 'TAG:language' in dict_dict_stream[key]:
                arguments = ''.join([arguments, ' --language 0:', dict_dict_stream[key]['TAG:language']])

            isDefault = 'DISPOSITION:default' in dict_dict_stream[key] and dict_dict_stream[key]['DISPOSITION:default'] == '1'
            arguments += f' --default-track-flag 0:{int(isDefault)}'

            if 'start_time' in dict_dict_stream[key] and float(dict_dict_stream[key]['start_time']) != float('0.000000'):
                delay = int(1000*float(dict_dict_stream[key]['start_time']))
                arguments += f' --sync 0:{delay}'
            arguments = f'{arguments} \"{key}\"'
        
        remuxCommand = f'mkvmerge -o \"{remuxedFile}\" -A \"{inputFile}\" {arguments}'
        try:
            sp.run(remuxCommand, capture_output=True, shell=True, check=True, encoding='utf-8')
        except sp.SubprocessError as error:
            print(error.stderr)


class ffmpeg_mux(muxer):

    def __copyFromInput(self, inputFile, dict_dict_stream) -> list[str]:
        counter: int = 0
        maps = metadata = imports = dispositions = ''
        typeCounter_dict = {'v':0, 'a':0, 's':0, 'NoLoSe':0, 't':0}
        for key in dict_dict_stream.keys():
            if key[0:1] == '/':
                if imports == '':
                    imports += f' -i \"{inputFile}\"'
                index: int = dict_dict_stream[key]['index']
                maps += f' -map 0:{index}'
                metadataType = dict_dict_stream[key]['codec_type'][0]

                if('TAG:language' in dict_dict_stream[key]):
                    typeCounter: str = str(typeCounter_dict[metadataType])
                    tag: str = dict_dict_stream[key]['TAG:language']
                    metadata += f' -metadata:s:{metadataType}:{typeCounter} language={tag}'
                
                if('DISPOSITION:default' in dict_dict_stream[key] and dict_dict_stream[key]['DISPOSITION:default'] == '1'):
                    typeCounter: str = str(typeCounter_dict[metadataType])
                    dispositions += f' -disposition:{metadataType}:{typeCounter} +default'
                
                if('DISPOSITION:forced' in dict_dict_stream[key] and dict_dict_stream[key]['DISPOSITION:forced'] == '1'):
                    dispositions+='+forced'
                
                typeCounter_dict[dict_dict_stream[key]['codec_type'][0]] +=1

        return [maps, metadata, imports, dispositions]

    def mux(self, inputFile, remuxedFile, dict_dict_stream):
        fromFile: list[str] = self.__copyFromInput(inputFile,dict_dict_stream)
        maps = fromFile[0]
        metadata = fromFile[1]
        imports = fromFile[2]
        dispositions = fromFile[3]
        counter = 1 # Podría checkear si se tomó algo del archivo original
        typeCounter_dict = {'v':0, 'a':0, 's':0, 'NoLoSe':0, 't':0}
        for key in dict_dict_stream.keys():
            if key[0:1] != '/':
                imports += ' -i ' + '\"'+key+'\"'
                maps += ' -map '+str(counter)+':0'
                metadataType = dict_dict_stream[key]['codec_type'][0]
                if('TAG:language' in dict_dict_stream[key]):
                    metadata += ' -metadata:s:'+metadataType+':'+str(typeCounter_dict[metadataType])+' language='+dict_dict_stream[key]['TAG:language']

                if('DISPOSITION:default' in dict_dict_stream[key] and dict_dict_stream[key]['DISPOSITION:default'] == '1'):
                    dispositions += ' -disposition:'+metadataType+':'+str(typeCounter_dict[metadataType])+' +default'

                if('DISPOSITION:forced' in dict_dict_stream[key] and dict_dict_stream[key]['DISPOSITION:forced'] == '1'):
                    dispositions+='+forced'

                typeCounter_dict[dict_dict_stream[key]['codec_type'][0]] +=1
                counter += 1
        
        remuxCommand = 'ffmpeg' + imports + ' -c copy' + maps + metadata + dispositions + ' \"'+remuxedFile+'\"'
        try:
            sp.run(remuxCommand, capture_output=True, shell=True, check=True, encoding='utf-8')
        except sp.SubprocessError as error:
            print(error.stderr)
