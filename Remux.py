from subprocess import run
from os import getcwd,path,system,mkdir,replace,remove,listdir,walk
from datetime import datetime as dt
from shutil import rmtree
import multiprocessing as mp
# --------------------------------------------- Downmix Algorithms ---------------------------------------------
#ATSC formula (ffmpeg's default):
algoritmoDownix = "\"pan=stereo|c0 < 1.0*c0 + 0.707*c2 + 0.707*c4|c1 < 1.0*c1 + 0.707*c2 + 0.707*c5\""

# without discarding the LFE channel:
# algoritmoDownix = "\"pan=stereo|c0=0.5*c2+0.707*c0+0.707*c4+0.5*c3|c1=0.5*c2+0.707*c1+0.707*c5+0.5*c3\""

# Nightmode:
# algoritmoDownix = "\"pan=stereo|c0=c2+0.30*c0+0.30*c4|c1=c2+0.30*c1+0.30*c5\""
# ---------------------------------------------------------------------------------------------------------------
parentFolder = getcwd()
dir_inputs = path.join(parentFolder,"A-Inputs")
dir_demux = path.join(parentFolder,"Demux")
dir_remux = path.join(parentFolder,"Remux")
ffmpegExe = "".join(["\"",parentFolder,"\\Tools\\ffmpeg\\ffmpeg.exe\""])
mkvmergeExe = "".join(["\"",parentFolder,"\\Tools\\mkvtoolnix\\mkvmerge.exe\""])
streamSuffix="[/STREAM]\n"

def probe(filepath):
	ffprobeCommand = "".join(["\"",parentFolder,"\\Tools\\ffmpeg\\ffprobe.exe\" -v error -show_streams -select_streams a -show_entries stream=index,codec_name,codec_type,channels,start_time:stream_tags=language:disposition=default \"",filepath,"\""])
	str_Stdout = run(ffprobeCommand, capture_output=True, shell=True, encoding="utf-8").stdout
	list_Stdout = str_Stdout.rsplit(sep="[STREAM]\n")
	list_streams = []
	for parte in list_Stdout:
		if parte.endswith(streamSuffix):
			parte = parte[:-len(streamSuffix)]
		if parte != "":
			list_streams+=parte,
	del list_Stdout
	return list_streams

def createFolderStructure(root,missing):
	missingFolder=root
	for folder in missing:
		missingFolder=path.join(missingFolder,folder)
		try:
			mkdir(missingFolder)
		except OSError as error:
			if(error.errno != 17): # 17: "File already exists"
				print(error)

def demux(root,filename,demuxLocation,list_streams):
	# TODO: only demux if at least 1 surround stream is found
	print("Demuxing")
	filesToDownmix = False
	streams = ""
	dict_dict_stream = {} # key=filename(que tiene un unico stream), value=dict de info de ese unico stream
	for stream in list_streams:
		stream_dict = {}
		infos = stream.rsplit(sep="\n")
		infos.remove("")
		for info in infos:
			dict_entry = info.rsplit(sep="=")
			stream_dict[dict_entry[0]] = dict_entry[1]
		if(stream_dict["codec_type"] == "audio"):
			file2Write="".join([stream_dict["index"],"_",filename.rsplit(sep=".")[0],"_",stream_dict["codec_type"]])
			if('DISPOSITION:forced' in stream_dict and stream_dict['DISPOSITION:forced'] == '1'):
				file2Write += "_forced"
			if('TAG:language' in stream_dict):
				file2Write += "_"+stream_dict['TAG:language']
			file2Write += "."+stream_dict["codec_name"]

			missingStructure=path.split(root[len(dir_inputs)+1:])+(filename,)
			createFolderStructure(dir_demux,missingStructure)

			file2Write = path.join(demuxLocation,file2Write)
			streams = "".join([streams,"-map 0:",stream_dict["index"]," -c copy \"",file2Write,"\" "])
			dict_dict_stream[file2Write]=stream_dict
			if(stream_dict['channels']=='6'):
				filesToDownmix = True

	if(filesToDownmix == True):
		ffmpegCommand =	"".join([ffmpegExe," -y -i \"",path.join(root,filename),"\" ",streams])
		run(ffmpegCommand, capture_output=True, shell=True, encoding="utf-8")
	return dict_dict_stream, filesToDownmix

def runDownmix(args):
	filepath, downmixCommand = args
	run(downmixCommand, capture_output=True, shell=True, encoding="utf-8")
	remove(filepath)

def downmix(demuxLocation,dict_dict_stream):
	print("Downmixing")
	pool = mp.Pool() # As many workers as logical cores
	iterable =[]
	for filename2 in listdir(demuxLocation):
		filepath = path.join(demuxLocation, filename2)
		if path.isfile(filepath) and filename2.find("_downmix") == -1 and dict_dict_stream[filepath]['channels']=='6':
			codec = dict_dict_stream[filepath]['codec_name']
			filenameSeparated=filename2.rsplit(sep=".")
			filenameNoExt = "".join(filenameSeparated[:len(filenameSeparated)-1])
			downmixCommand = "".join([ffmpegExe," -i \"",filepath,"\" -c ",codec," -af ",algoritmoDownix," \"",path.join(demuxLocation,filenameNoExt),"_downmix.",codec,"\""])
			dict_dict_stream[path.join(demuxLocation,"".join([filenameNoExt,"_downmix.",codec]))] = dict_dict_stream[filepath]
			del dict_dict_stream[filepath]
			iterable.append((filepath,downmixCommand))
	pool.imap_unordered(runDownmix,iterable)
	pool.close()
	pool.join()

def remux(root,demuxLocation,filename,dict_dict_stream,filesToDownmix):
	print("Remuxing")
	delay = arguments = ""
	inputFile = path.join(root,filename)
	remuxLocation = path.join(dir_remux,path.join(root[len(dir_inputs)+1:]))
	missingStructure=path.split(root[len(dir_inputs)+1:])
	createFolderStructure(dir_remux,missingStructure)
	remuxedFile = path.join(remuxLocation,filename)
	if(filesToDownmix == True):
		for audioStream in listdir(demuxLocation):
			filepath = path.join(demuxLocation, audioStream)
			if path.isfile(filepath):
				if('TAG:language' in dict_dict_stream[filepath]):
					arguments = "".join([arguments," --language 0:", dict_dict_stream[filepath]['TAG:language']])
				if('DISPOSITION:default' in dict_dict_stream[filepath] and dict_dict_stream[filepath]['DISPOSITION:default'] == '1'):
					arguments += " --default-track-flag 0:1"
				else:
					arguments += " --default-track-flag 0:0"
				if('start_time' in dict_dict_stream[filepath] and float(dict_dict_stream[filepath]['start_time']) != float ("0.000000")):
					delay = int(1000*float(dict_dict_stream[filepath]['start_time']))
					arguments += " --sync 0:"+str(delay)
				arguments = "".join([arguments," \"",filepath,"\""])
			remuxCommand = "".join([mkvmergeExe," -o \"",remuxedFile,"\" -A \"",inputFile,"\" ",arguments])
			run(remuxCommand, capture_output=True, shell=True, encoding="utf-8")
	else:
		replace(inputFile, remuxedFile)
	rmtree(demuxLocation)

if __name__ == '__main__':
	start_time = dt.now()
	foldersToCreate = (dir_inputs,dir_demux,dir_remux)
	for folder in foldersToCreate:
		try:
			mkdir(folder)
		except OSError as error:
			if(error.errno != 17): # 17: "File already exists"
				print(error)
	print("---------------------------------------------------------------------------------------------------")
	for root, dirs, files in walk(dir_inputs):
		for filename in files:
			if(filename.rsplit(sep=".")[-1] == "mkv"):
				filepath = path.join(root,filename)
				print("".join(["Processing ",filepath]))
				list_streams = probe(filepath)
				demuxLocation = path.join(dir_demux,path.join(root[len(dir_inputs)+1:],filename))
				dict_dict_stream,filesToDownmix = demux(root,filename,demuxLocation,list_streams)
				downmix(demuxLocation,dict_dict_stream)
				remux(root,demuxLocation,filename,dict_dict_stream,filesToDownmix)
				del dict_dict_stream
	print("\033[92m--------------------------------------------- DONE ---------------------------------------------\033[0m")
	print("se tardo: "+str(dt.now()-start_time))
	system("pause")
