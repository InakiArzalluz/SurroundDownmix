from subprocess import run
from os import getcwd,path,system,mkdir,replace,remove,listdir
from datetime import datetime
def main():
	start_time = datetime.now()

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
	try:
		mkdir(dir_inputs)
		mkdir(dir_demux)
		mkdir(dir_remux)
	except OSError as error:
		if(error.errno != 17): # 17: "File already exists"
			print(error)

	ffmpegExe = "".join(["\"",parentFolder,"\\Tools\\ffmpeg\\ffmpeg.exe\""])
	mkvmergeExe = "".join(["\"",parentFolder,"\\Tools\\mkvtoolnix\\mkvmerge.exe\""])
	Remuxcounter = 0
	suffix="[/STREAM]\n"
	for filename in listdir(dir_inputs):
		system("cls")
		print("---------------------------------------------------------------------------------------------------") #inputFile = os.path.join(dir_inputs,filename)
		print(filename)
		ffprobeCommand = "".join(["\"",parentFolder,"\\Tools\\ffmpeg\\ffprobe.exe\" -v error -show_streams -select_streams a -show_entries stream=index,codec_name,codec_type,channels,start_time:stream_tags=language:disposition=default \"",path.join(dir_inputs,filename),"\""])
		str_Stdout = run(ffprobeCommand, capture_output=True, shell=True, encoding="utf-8").stdout
		list_Stdout = str_Stdout.rsplit(sep="[STREAM]\n")
		list_streams = []
		for parte in list_Stdout:
			if parte.endswith(suffix):
				parte = parte[:-len(suffix)]
			if parte != "":
				list_streams+=parte,
		del list_Stdout
		print("--------------------------------------------- Demuxing ---------------------------------------------")
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
				streams = "".join([streams,"-map 0:",stream_dict["index"]," -c copy \"",path.join(dir_demux,file2Write),"\" "])
				dict_dict_stream[file2Write]=stream_dict
				if(stream_dict['channels']=='6'):
					filesToDownmix = True
					print("".join([file2Write," will be downmixed"]))

		if(filesToDownmix == True):
			ffmpegCommand =	"".join([ffmpegExe," -y -i \"",path.join(dir_inputs,filename),"\" ",streams])
			run(ffmpegCommand, capture_output=True, shell=True, encoding="utf-8")
		print("--------------------------------------------- Downmixing ---------------------------------------------")
		for filename2 in listdir(dir_demux):
			filepath = path.join(dir_demux, filename2)
			if path.isfile(filepath):
				if (filename2.find("_downmix") == -1):
					if('channels' in dict_dict_stream[filename2]  and dict_dict_stream[filename2]['channels']=='6'):
						print(filename2)
						codec = dict_dict_stream[filename2]['codec_name']
						filenameNoExt=filename2.rsplit(sep=".")[0]
						downmixCommand = "".join([ffmpegExe," -i \"",filepath,"\" -c ",codec," -af ",algoritmoDownix," \"",path.join(dir_demux,filenameNoExt),"_downmix.",codec,"\""])
						run(downmixCommand, capture_output=True, shell=True, encoding="utf-8")
						dict_dict_stream["".join([filenameNoExt,"_downmix.",codec])] = dict_dict_stream[filename2]
						del dict_dict_stream[filename2]
						remove(filepath)		
		print("--------------------------------------------- Remuxing ---------------------------------------------")
		delay = arguments = ""
		inputFile = path.join(dir_inputs,filename)
		remuxedFile = path.join(dir_remux,filename)
		if(filesToDownmix == True):
			print("Processing")
			for filename3 in listdir(dir_demux):
				filepath = path.join(dir_demux, filename3)
				if path.isfile(filepath):
					if('TAG:language' in dict_dict_stream[filename3]):
						arguments = "".join([arguments," --language 0:", dict_dict_stream[filename3]['TAG:language']])

					if('DISPOSITION:default' in dict_dict_stream[filename3] and dict_dict_stream[filename3]['DISPOSITION:default'] == '1'):
						arguments += " --default-track-flag 0:1"
					else:
						arguments += " --default-track-flag 0:0"

					if('start_time' in dict_dict_stream[filename3] and float(dict_dict_stream[filename3]['start_time']) != float ("0.000000")):
						delay = int(1000*float(dict_dict_stream[filename3]['start_time']))
						arguments += " --sync 0:"+str(delay)

					arguments = "".join([arguments," \"",filepath,"\""])

			Remuxcounter += 1
			remuxCommand = "".join([mkvmergeExe," -o \"",remuxedFile,"\" -A \"",inputFile,"\" ",arguments])
			run(remuxCommand, capture_output=True, shell=True, encoding="utf-8")
		else:
			replace(inputFile, remuxedFile)

		for filename2 in listdir(dir_demux):
			filepath = path.join(dir_demux, filename2)
			if path.isfile(filepath):
				remove(filepath)
	print("\033[92m--------------------------------------------- DONE ---------------------------------------------\033[0m")
	print("".join(["Se procesaron ",str(Remuxcounter)," videos con audio 5.1"]))
	print("se tardo: "+str(datetime.now()-start_time))
	system("pause")
main()