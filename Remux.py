import subprocess as sp
import os
import datetime as dt
import shutil as sh
import multiprocessing as mp
import platform
# --------------------------------------------- Downmix Algorithms ---------------------------------------------
# ATSC formula (ffmpeg's default):
algoritmoDownix = '\"pan=stereo|c0 < 1.0*c0 + 0.707*c2 + 0.707*c4|c1 < 1.0*c1 + 0.707*c2 + 0.707*c5\"'

# without discarding the LFE channel:
# algoritmoDownix = '\"pan=stereo|c0=0.5*c2+0.707*c0+0.707*c4+0.5*c3|c1=0.5*c2+0.707*c1+0.707*c5+0.5*c3\"'

# Nightmode:
# algoritmoDownix = '\"pan=stereo|c0=c2+0.30*c0+0.30*c4|c1=c2+0.30*c1+0.30*c5\"'
# ---------------------------------------------------------------------------------------------------------------
parentFolder = os.getcwd()
dir_inputs = os.path.join(parentFolder, 'A-Inputs')
dir_demux = os.path.join(parentFolder, 'Demux')
dir_remux = os.path.join(parentFolder, 'Remux')
if (platform.system() == 'Windows'):
    ffmpeg = f'\"{parentFolder}{os.sep}Tools{os.sep}ffmpeg{os.sep}ffmpeg.exe\"'
    mkvmerge = f'\"{parentFolder}{os.sep}Tools{os.sep}mkvtoolnix{os.sep}mkvmerge.exe\"'
    ffprobe = f'\"{parentFolder}{os.sep}Tools{os.sep}ffmpeg{os.sep}ffprobe.exe\"'
else:
    ffmpeg = 'ffmpeg'
    mkvmerge = 'mkvmerge'
    ffprobe = 'ffprobe'
streamSuffix = '[/STREAM]\n'


def probe(filepath):
    ffprobeCommand = f'{ffprobe} -v error -show_streams -select_streams a -show_entries stream=index,codec_name,codec_type,channels,start_time:stream_tags=language:disposition=default \"{filepath}\"'
    str_Stdout = sp.run(ffprobeCommand, capture_output=True, shell=True, encoding='utf-8').stdout
    list_Stdout = str_Stdout.rsplit(sep='[STREAM]\n')
    list_streams = []
    for parte in list_Stdout:
        if parte.endswith(streamSuffix):
            parte = parte[:-len(streamSuffix)]
        if parte != '':
            list_streams += parte,
    del list_Stdout
    return list_streams


def createFolderStructure(root, missing):
    missingFolder = root
    for folder in missing:
        missingFolder = os.path.join(missingFolder, folder)
        try:
            os.mkdir(missingFolder)
        except OSError as error:
            if error.errno != 17:  # 17: "File already exists"
                print(error)


def demux(root, filename, demuxLocation, list_streams):
    print("Demuxing")
    filesToDownmix = False
    streams = ''
    dict_dict_stream = {}  # key=filename(with only 1 stream), value=dict with info about that unique stream
    for stream in list_streams:
        stream_dict = {}
        infos = stream.rsplit(sep='\n')
        infos.remove('')
        for info in infos:
            dict_entry = info.rsplit(sep='=')
            stream_dict[dict_entry[0]] = dict_entry[1]
        if stream_dict['codec_type'] == 'audio':
            file2Write = ''.join([stream_dict['index'], '_', filename.rsplit(sep='.')[0], '_', stream_dict['codec_type']])
            if 'DISPOSITION:forced' in stream_dict and stream_dict['DISPOSITION:forced'] == '1':
                file2Write += '_forced'
            if 'TAG:language' in stream_dict:
                file2Write += "_"+stream_dict['TAG:language']
            file2Write += "."+stream_dict['codec_name']

            missingStructure = os.path.split(root[len(dir_inputs)+1:])+(filename,)
            createFolderStructure(dir_demux, missingStructure)

            file2Write = os.path.join(demuxLocation, file2Write)
            streams = ''.join([f'{streams}-map 0:', stream_dict['index'], f' -c copy \"{file2Write}\" '])
            dict_dict_stream[file2Write] = stream_dict
            if stream_dict['channels'] == '6':
                filesToDownmix = True

    if filesToDownmix:
        inputFile = os.path.join(root, filename)
        ffmpegCommand = f'{ffmpeg} -y -i \"{inputFile}\" {streams}'
        try:
            sp.run(ffmpegCommand, capture_output=True, shell=True, check=True, encoding='utf-8')
        except sp.SubprocessError as error:
            print(error.stderr)
    return dict_dict_stream, filesToDownmix


def runDownmix(args):
    filepath, downmixCommand = args
    try:
        sp.run(downmixCommand, capture_output=True, shell=True, check=True, encoding='utf-8')
        os.remove(filepath)
    except sp.SubprocessError as error:
        print(error.stderr)


def downmix(demuxLocation, dict_dict_stream):
    print("Downmixing")
    pool = mp.Pool()  # As many workers as logical cores
    iterable = []
    for filename2 in os.listdir(demuxLocation):
        filepath = os.path.join(demuxLocation, filename2)
        if os.path.isfile(filepath) and filename2.find('_downmix') == -1 and dict_dict_stream[filepath]['channels'] == '6':
            codec = dict_dict_stream[filepath]['codec_name']
            filenameSeparated = filename2.rsplit(sep='.')
            outputFileNoExt = os.path.join(demuxLocation, ''.join(filenameSeparated[:-1]))
            downmixCommand = f'{ffmpeg} -y -i \"{filepath}\" -c {codec} -af {algoritmoDownix} \"{outputFileNoExt}_downmix.{codec}\"'
            dict_dict_stream[f'{outputFileNoExt}_downmix.{codec}'] = dict_dict_stream[filepath]
            del dict_dict_stream[filepath]
            iterable.append((filepath, downmixCommand))
    pool.imap_unordered(runDownmix, iterable)
    pool.close()
    pool.join()


def remux(inputFile, demuxLocation, remuxedFile, dict_dict_stream, filesToDownmix):
    print("Remuxing")
    delay = arguments = ''
    if filesToDownmix:
        for audioStream in os.listdir(demuxLocation):
            filepath = os.path.join(demuxLocation, audioStream)
            if os.path.isfile(filepath):
                if 'TAG:language' in dict_dict_stream[filepath]:
                    arguments = ''.join([arguments, ' --language 0:', dict_dict_stream[filepath]['TAG:language']])
                isDefault = 'DISPOSITION:default' in dict_dict_stream[filepath] and dict_dict_stream[filepath]['DISPOSITION:default'] == '1'
                arguments += f' --default-track-flag 0:{int(isDefault)}'
                if 'start_time' in dict_dict_stream[filepath] and float(dict_dict_stream[filepath]['start_time']) != float('0.000000'):
                    delay = int(1000*float(dict_dict_stream[filepath]['start_time']))
                    arguments += f' --sync 0:{delay}'
                arguments = f'{arguments} \"{filepath}\"'
            remuxCommand = f'{mkvmerge} -o \"{remuxedFile}\" -A \"{inputFile}\" {arguments}'
            try:
                sp.run(remuxCommand, capture_output=True, shell=True, check=True, encoding='utf-8')
            except sp.SubprocessError as error:
                print(error.stderr)
    else:
        os.replace(inputFile, remuxedFile)


def cleanDemuxfolder():
    for content in os.listdir(dir_demux):
        contentPath = os.path.join(dir_demux, content)
        if os.path.isfile(contentPath):  # There should only be folders, but just in case
            os.remove(contentPath)
        else:
            sh.rmtree(contentPath)

if __name__ == '__main__':
    start_time = dt.datetime.now()
    foldersToCreate = (dir_inputs, dir_demux, dir_remux)
    for folder in foldersToCreate:
        try:
            os.mkdir(folder)
        except OSError as error:
            if error.errno != 17:  # 17: "File already exists"
                print(error)
    print('\033[92m---------------------------------------------------------------------------------------------------\033[0m')
    for root, dirs, files in os.walk(dir_inputs):
        for filename in files:
            filepath = os.path.join(root, filename)
            remuxLocation = os.path.join(dir_remux, os.path.join(root[len(dir_inputs)+1:]))
            missingStructure = os.path.split(root[len(dir_inputs)+1:])
            createFolderStructure(dir_remux, missingStructure)
            if filename.rsplit(sep='.')[-1] == 'mkv':
                print("".join(["Processing ", filepath]))
                list_streams = probe(filepath)
                demuxLocation = os.path.join(dir_demux, os.path.join(root[len(dir_inputs)+1:], filename))
                dict_dict_stream, filesToDownmix = demux(root, filename, demuxLocation, list_streams)
                downmix(demuxLocation, dict_dict_stream)
                inputFile = os.path.join(root, filename)
                remuxedFile = os.path.join(remuxLocation, filename)
                remux(inputFile, demuxLocation, remuxedFile, dict_dict_stream, filesToDownmix)
                del dict_dict_stream
            else:
                os.replace(filepath, os.path.join(remuxLocation, filename))
    cleanDemuxfolder()
    print('\033[92m--------------------------------------------- DONE ---------------------------------------------\033[0m')
    print(f"se tardo: {dt.datetime.now()-start_time}")
    if (platform.system() == 'Windows'):
        os.system('pause')
    else:
        os.system('read -p "Press any key to exit ..."')
