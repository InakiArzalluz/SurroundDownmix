import subprocess as sp


class Muxer:

    def mux(self, inputFile, remuxedFile, dict_dict_stream):
        pass


class Mkvmerge_Muxer(Muxer):

    def mux(self, inputFile, remuxedFile, dict_dict_stream):
        delay = arguments = ''
        for key in dict_dict_stream.keys():
            dict_stream = dict_dict_stream[key]
            if 'TAG:language' in dict_stream:
                arguments = ''.join([arguments, ' --language 0:', dict_stream['TAG:language']])

            isDefault = 'DISPOSITION:default' in dict_stream and dict_stream['DISPOSITION:default'] == '1'
            arguments += f' --default-track-flag 0:{int(isDefault)}'

            if 'start_time' in dict_stream and float(dict_stream['start_time']) != float('0.000000'):
                delay = int(1000*float(dict_stream['start_time']))
                arguments += f' --sync 0:{delay}'
            arguments = f'{arguments} \"{key}\"'

        remuxCommand = f'mkvmerge -o \"{remuxedFile}\" -A \"{inputFile}\" {arguments}'
        try:
            sp.run(remuxCommand, capture_output=True, shell=True, check=True, encoding='utf-8')
        except sp.SubprocessError as error:
            print(error)


class FFMPEG_Muxer(Muxer):

    def __copyFromInput(self, inputFile, dict_dict_stream) -> list[str]:
        maps = metadata = imports = dispositions = ''
        typeCounter_dict = {'v': 0, 'a': 0, 's': 0, 'NoLoSe': 0, 't': 0}
        for key in dict_dict_stream.keys():
            if key[0:1] == '/':
                if imports == '':
                    imports += f' -i \"{inputFile}\"'
                dict_stream = dict_dict_stream[key]
                index: int = dict_stream['index']
                maps += f' -map 0:{index}'
                metadataType = dict_stream['codec_type'][0]

                if ('TAG:language' in dict_stream):
                    typeCounter: str = str(typeCounter_dict[metadataType])
                    tag: str = dict_stream['TAG:language']
                    metadata += f' -metadata:s:{metadataType}:{typeCounter} language={tag}'

                if ('DISPOSITION:default' in dict_stream and dict_stream['DISPOSITION:default'] == '1'):
                    typeCounter: str = str(typeCounter_dict[metadataType])
                    dispositions += f' -disposition:{metadataType}:{typeCounter} +default'

                if ('DISPOSITION:forced' in dict_stream and dict_stream['DISPOSITION:forced'] == '1'):
                    dispositions += '+forced'

                typeCounter_dict[metadataType] += 1

        return [maps, metadata, imports, dispositions]

    def mux(self, inputFile, remuxedFile, dict_dict_stream):
        fromFile: list[str] = self.__copyFromInput(inputFile, dict_dict_stream)
        maps = fromFile[0]
        metadata = fromFile[1]
        imports = fromFile[2]
        dispositions = fromFile[3]
        counter = 1  # Podría checkear si se tomó algo del archivo original
        typeCounter_dict = {'v': 0, 'a': 0, 's': 0, 'NoLoSe': 0, 't': 0}
        for key in dict_dict_stream.keys():
            if key[0:1] != '/':
                imports += ' -i ' + '\"'+key+'\"'
                maps += ' -map '+str(counter)+':0'
                dict_stream = dict_dict_stream[key]
                metadataType = dict_stream['codec_type'][0]
                if ('TAG:language' in dict_stream):
                    typecounter: str = str(typeCounter_dict[metadataType])
                    lang: str = dict_stream['TAG:language']
                    metadata += f' -metadata:s:{metadataType}:{typecounter} language={lang}'

                if ('DISPOSITION:default' in dict_stream and dict_stream['DISPOSITION:default'] == '1'):
                    typecounter: str = str(typeCounter_dict[metadataType])
                    dispositions += f' -disposition:{metadataType}:{typecounter} +default'

                if ('DISPOSITION:forced' in dict_stream and dict_stream['DISPOSITION:forced'] == '1'):
                    dispositions += '+forced'

                typeCounter_dict[metadataType] += 1
                counter += 1

        remuxCommand = 'ffmpeg' + imports + ' -c copy' + maps + metadata + dispositions + ' -max_interleave_delta 0 \"'+remuxedFile+'\"'
        try:
            sp.run(remuxCommand, capture_output=True, shell=True, check=True, encoding='utf-8')
        except sp.SubprocessError as error:
            print(error)
