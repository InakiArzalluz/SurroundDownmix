import subprocess as sp
import os
from src.tools import tools

class demuxer:

    def demux(self, filepath: str, demuxLocation: str, list_streams: list[str]) -> tuple[dict[str, dict[str,str]]]:
        pass

class mkvmerge_demux(demuxer):
    
    def demux(self, filepath: str, demuxLocation: str, list_streams: list[str]) -> tuple[dict[str, dict[str,str]]]:
        #  dict_dict_stream{
        #    key = streamFilename
        #    value = dict with info about that stream
        #  }
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
                file2Write: str = ''.join([stream_dict['index'], '_', filename.rsplit(sep='.')[0], '_', stream_dict['codec_type']])
                if 'DISPOSITION:forced' in stream_dict and stream_dict['DISPOSITION:forced'] == '1':
                    file2Write += '_forced'
                if 'TAG:language' in stream_dict:
                    file2Write += "_"+stream_dict['TAG:language']
                file2Write += "."+stream_dict['codec_name']

                file2Write: str = os.path.join(demuxLocation, file2Write)
                streams_arg: str = ''.join([f'{streams_arg}-map 0:', stream_dict['index'], f' -c copy \"{file2Write}\" '])
                dict_dict_stream[file2Write] = stream_dict
        
        ffmpegCommand = f'ffmpeg -y -i \"{filepath}\" {streams_arg}'
        try:
            sp.run(ffmpegCommand, capture_output=True, shell=True, check=True, encoding='utf-8')
        except sp.SubprocessError as error:
            print(error.stderr)

        return dict_dict_stream

class ffmpeg_demux(demuxer):

    __extensions_dict = {'h264':'mp4', 'subrip':'srt', 'mjpeg':'jpg'} # mapeo de codec_name a file extension

    def demux(self, filepath: str, demuxLocation: str, list_streams: list[str]) -> tuple[dict[str, dict[str,str]]]:
        streams = attachments = ''
        dict_dict_stream = {}
        filename = os.path.basename(filepath)
        for stream in list_streams:
            stream_dict = {}
            infos = stream.rsplit(sep='\n')
            infos.remove('')
            for info in infos:
                dict_entry = info.rsplit(sep='=')
                stream_dict[dict_entry[0]] = dict_entry[1]
            codec = stream_dict['codec_name']
            file2Write: str = ''.join([stream_dict['index'], '_', filename.rsplit(sep='.')[0], '_', stream_dict['codec_type']])
            
            if 'DISPOSITION:forced' in stream_dict and stream_dict['DISPOSITION:forced'] == '1':
                file2Write += '_forced'

            if 'TAG:language' in stream_dict:
                file2Write += '_'+stream_dict['TAG:language']
            
            codec = stream_dict['codec_name']
            if codec in ffmpeg_demux.__extensions_dict:
                file2Write += '.'+ffmpeg_demux.__extensions_dict[codec] # por h264, subrip, etc.
            else:
                file2Write += '.'+codec

            #if stream_dict['codec_type'] == 'attachment':
            #    # '/' helps differentiate extracted from not extracted, since '/' is forbidden in filenames
            #    file2Write = '/' + file2Write
            #    attachments += '-dump_attachment:' + stream_dict['index'] + ' \"' + file2Write
            #    if('TAG:filename' in stream_dict):
            #        file2Write = os.path.join(demuxLocation, stream_dict['TAG:filename'])
            #    attachments += file2Write+'\" '
            if stream_dict['codec_type'] == 'audio' and stream_dict['channels'] == '6':
                file2Write: str = os.path.join(demuxLocation, file2Write)
                streams += '-map 0:' + stream_dict['index'] + ' -c copy ' +'\"'+file2Write+'\" '
            else:
                # '/' helps differentiate extracted from not extracted, '/' is forbidden in filenames
                file2Write = '/' + file2Write
            
            dict_dict_stream[file2Write] = stream_dict
        
        ffmpegCommand =	'ffmpeg -y -i \"' + filepath + '\" ' + streams
        sp.run(ffmpegCommand, capture_output=True, shell=True, encoding="utf-8")
        #if attachments != "":
        #    attachmentsCommand = ffmpegExe +" "+attachments+ "-i " + "\""+parentFolder+"\\A-Inputs\\"+filename+"\""
        #	print('\033[92m'+"attachments command: "+'\033[0m')
        #	print(attachmentsCommand)
        #   subprocess.run(attachmentsCommand, capture_output=True, shell=True, encoding="utf-8")
        return dict_dict_stream
