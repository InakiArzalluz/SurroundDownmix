import subprocess as sp
import os


class Demuxer:
    ''' returns dict with: { streamFilename : dict with info about that stream } '''
    def demux(self, filepath: str, demuxLocation: str, list_streams: list[str]) -> dict[str, dict[str,str]]:
        pass


class Mkvmerge_Demuxer(Demuxer):

    def demux(self, filepath: str, demuxLocation: str, list_streams: list[str]) -> dict[str, dict[str, str]]:
        dict_dict_stream = {}
        filename = os.path.basename(filepath)
        streams_arg: str = ''
        for stream in list_streams:
            stream_dict = {}
            infos = stream.rsplit(sep='\n')
            infos.remove('')
            for info in infos:
                dict_entry = info.rsplit(sep='=')
                stream_dict[dict_entry[0]] = dict_entry[1]

            if stream_dict['codec_type'] == 'audio':
                index: str = stream_dict['index']
                filename_no_ext: str = filename.rsplit(sep='.')[0]
                file2Write: str = f'{index}_{filename_no_ext}_audio'
                if 'DISPOSITION:forced' in stream_dict and stream_dict['DISPOSITION:forced'] == '1':
                    file2Write += '_forced'
                if 'TAG:language' in stream_dict:
                    file2Write += "_"+stream_dict['TAG:language']
                file2Write += "."+stream_dict['codec_name']

                file2Write: str = os.path.join(demuxLocation, file2Write)
                streams_arg: str = f'{streams_arg}-map 0:{index} -c copy \"{file2Write}\" '
                dict_dict_stream[file2Write] = stream_dict

        ffmpegCommand = f'ffmpeg -y -i \"{filepath}\" {streams_arg}'
        try:
            sp.run(ffmpegCommand, capture_output=True, shell=True, check=True, encoding='utf-8')
        except sp.SubprocessError as error:
            print(error.stderr)

        return dict_dict_stream


class FFMPEG_Demuxer(Demuxer):

    # mapping from codec_name to file extension
    __extensions_dict = {'h264': 'mp4', 'subrip': 'srt', 'mjpeg': 'jpg'}

    def demux(self, filepath: str, demuxLocation: str, list_streams: list[str]) -> dict[str, dict[str, str]]:
        streams = ''
        # attachments = ''
        dict_dict_stream = {}
        filename = os.path.basename(filepath)
        for stream in list_streams:
            stream_dict = {}
            infos = stream.rsplit(sep='\n')
            infos.remove('')
            for info in infos:
                dict_entry = info.rsplit(sep='=')
                stream_dict[dict_entry[0]] = dict_entry[1]

            index: str = stream_dict['index']
            filename_no_ext: str = filename.rsplit(sep='.')[0]
            codecType: str = stream_dict['codec_type']
            file2Write: str = f'{index}_{filename_no_ext}_{codecType}'

            if 'DISPOSITION:forced' in stream_dict and stream_dict['DISPOSITION:forced'] == '1':
                file2Write += '_forced'

            if 'TAG:language' in stream_dict:
                file2Write += '_' + stream_dict['TAG:language']

            codec = stream_dict['codec_name']
            if codec in FFMPEG_Demuxer.__extensions_dict:
                # por h264, subrip, etc.
                file2Write += '.'+FFMPEG_Demuxer.__extensions_dict[codec]
            else:
                file2Write += '.'+codec

            # if codecType == 'attachment':
            #    # '/' helps differentiate extracted from not extracted, since '/' is forbidden in filenames
            #    file2Write = '/' + file2Write
            #    attachments += '-dump_attachment:' + stream_dict['index'] + ' \"' + file2Write
            #    if('TAG:filename' in stream_dict):
            #        file2Write = os.path.join(demuxLocation, stream_dict['TAG:filename'])
            #    attachments += file2Write+'\" '
            if codecType == 'audio' and stream_dict['channels'] == '6':
                file2Write: str = os.path.join(demuxLocation, file2Write)
                streams += f'-map 0:{index} -c copy \"{file2Write}\" '
            else:
                # '/' helps differentiate extracted from not extracted, '/' is forbidden in filenames
                file2Write = '/' + file2Write

            dict_dict_stream[file2Write] = stream_dict

        ffmpegCommand = f'ffmpeg -y -i \"{filepath}\" {streams}'
        sp.run(ffmpegCommand, capture_output=True, shell=True, encoding="utf-8")
        # if attachments != "":
        #    attachmentsCommand = ffmpegExe +" "+attachments+ "-i " + "\""+parentFolder+"\\A-Inputs\\"+filename+"\""
        #    print('\033[92m'+"attachments command: "+'\033[0m')
        #    print(attachmentsCommand)
        #    subprocess.run(attachmentsCommand, capture_output=True, shell=True, encoding="utf-8")
        return dict_dict_stream
