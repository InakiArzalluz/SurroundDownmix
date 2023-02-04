import subprocess
import os

# --------------------------------------------- Downmix Algorithms ---------------------------------------------
#ATSC formula (ffmpeg's default):
# algoritmoDownix = "\"pan=stereo|c0 < 1.0*c0 + 0.707*c2 + 0.707*c4|c1 < 1.0*c1 + 0.707*c2 + 0.707*c5\""

# without discarding the LFE channel:
algoritmoDownix = "\"pan=stereo|c0=0.5*c2+0.707*c0+0.707*c4+0.5*c3|c1=0.5*c2+0.707*c1+0.707*c5+0.5*c3\""

# Nightmode:
# algoritmoDownix = "\"pan=stereo|c0=c2+0.30*c0+0.30*c4|c1=c2+0.30*c1+0.30*c5\""
# ---------------------------------------------------------------------------------------------------------------

extensions_dict = {'h264':'mp4', 'subrip':'srt', 'mjpeg':'jpg'} # mapeo de codec_name a file extension
# 'eac3':'eac3', 'ac3':'ac3','mp2':'mp2', 'aac':'aac', 'hevc':'hevc', 'ass':'ass', 'otf':'otf', 'mp3':'mp3'
# ver como extraer capitulos de Mujer Maravilla
# type_dict = {'mp4':'v', 'srt':'s', 'jpg':'NoLoSe', 'eac3':'a', 'ac3':'a','mp2':'a', 'aac':'a', 'hevc':'v', 'ass':'s', 'otf':'NoLoSe', 'mp3':'a'}

parentFolder = os.getcwd()
dir_inputs = os.path.join(parentFolder,"A-Inputs")
dir_demux = os.path.join(parentFolder,"Demux")
try:
	os.mkdir(dir_inputs)
	os.mkdir(dir_demux)
	os.mkdir(os.path.join(parentFolder,"Remux"))
except OSError as error:
	if(error.errno != 17): # 17: "File already exists"
		print(error)

ffmpegExe = "\""+parentFolder+"\\Tools\\ffmpeg\\ffmpeg.exe\""
mkvmergeExe = "\""+parentFolder+"\\Tools\\mkvtoolnix\\mkvmerge.exe\""
for filename in os.listdir(dir_inputs):
	print("--------------------------------------------- FFPROBE ---------------------------------------------")
	print(filename)
	ffprobeCommand = "\""+parentFolder+"\\Tools\\ffmpeg\\ffprobe.exe\" -v error -show_entries stream=index,codec_name,codec_type,channels,start_time:stream_tags=language,filename:disposition=default \""+dir_inputs+"\\"+filename+"\""
	str_Stdout = subprocess.run(ffprobeCommand, capture_output=True, shell=True, encoding="utf-8").stdout
	list_Stdout = str_Stdout.rsplit(sep="[STREAM]\n")
	list_streams = []
	for parte in list_Stdout:
		suffix="[/STREAM]\n"
		if parte.endswith(suffix):
			parte = parte[:-len(suffix)]
		if parte != "":
			list_streams.append(parte)
	del list_Stdout
	
	print("--------------------------------------------- Demuxing ---------------------------------------------")
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
			codec = stream_dict["codec_name"]
			file2Write=stream_dict["index"]+"_"+filename.rsplit(sep=".")[0]+"_"+stream_dict["codec_type"]
			if('DISPOSITION:forced' in stream_dict and stream_dict['DISPOSITION:forced'] == '1'):
				file2Write += "_forced"
			if('TAG:language' in stream_dict):
				file2Write += "_"+stream_dict['TAG:language']
			file2Write += "."+stream_dict["codec_name"]
			streams += "-map 0:" + stream_dict["index"] + " -c copy " +"\""+parentFolder+"\\Demux\\" +file2Write+"\" "
			dict_dict_stream[file2Write]=stream_dict
			print(file2Write)

	ffmpegCommand =	ffmpegExe + " -y -i " + "\""+parentFolder+"\\A-Inputs\\"+filename+"\" " + streams
	subprocess.run(ffmpegCommand, capture_output=True, shell=True, encoding="utf-8")
	# MkvExtractCommand = "\""+parentFolder+"\\Tools\\mkvtoolnix\\mkvextract.exe\"  \""+parentFolder+"\\A-Inputs\\"+filename+"\""

	print("--------------------------------------------- Downmixing ---------------------------------------------")
	for filename2 in os.listdir(dir_demux):
	    filepath = os.path.join(dir_demux, filename2)
	    if os.path.isfile(filepath):
	    	if (filename2.find("_downmix") == -1):
		    	if('channels' in dict_dict_stream[filename2]  and dict_dict_stream[filename2]['channels']=='6'):
		    		print(filename2)
		    		codec = dict_dict_stream[filename2]['codec_name']
		    		filenameNoExt=filename2.rsplit(sep=".")[0]
		    		downmixCommand = ffmpegExe + " -i " + "\""+filepath+"\"" + " -c " + codec + " -af " + algoritmoDownix + " "  + "\""+dir_demux+"\\"+filenameNoExt+"_downmix."+codec+"\""
		    		subprocess.run(downmixCommand, capture_output=True, shell=True, encoding="utf-8")
		    		dict_dict_stream[filenameNoExt+"_downmix."+codec] = dict_dict_stream[filename2]
		    		del dict_dict_stream[filename2]
		    		os.remove(filepath)
	    		
	print("--------------------------------------------- Remuxing ---------------------------------------------")
	maps = metadata = imports = dispositions = delay = arguments = ""
	counter = 0
	typeCounter_dict = {'v':0, 'a':0, 's':0, 'NoLoSe':0, 't':0}
	for filename3 in os.listdir(dir_demux):
	    filepath = os.path.join(dir_demux, filename3)
	    if os.path.isfile(filepath):
	    	extension = filename3.rsplit(sep=".")[-1]
	    	if('TAG:language' in dict_dict_stream[filename3]):
	    		arguments += " --language 0:" + dict_dict_stream[filename3]['TAG:language']

	    	if('DISPOSITION:default' in dict_dict_stream[filename3] and dict_dict_stream[filename3]['DISPOSITION:default'] == '1'):
	    		print("sets "+ filename3 + " as default " +dict_dict_stream[filename3]['codec_type'])
	    		arguments += " --default-track-flag 0:1"
	    	else:
	    		arguments += " --default-track-flag 0:0"

	    	if('start_time' in dict_dict_stream[filename3] and float(dict_dict_stream[filename3]['start_time']) != float ("0.000000")):
	    		delay = int(1000*float(dict_dict_stream[filename3]['start_time']))
	    		arguments += " --sync 0:"+str(delay)

	    	arguments += " \""+filepath+"\""

	remuxCommand = mkvmergeExe + " -o \""+parentFolder+"\\Remux\\"+filename+"\"" +" -A "+"\""+parentFolder+"\\A-Inputs\\"+filename+"\" "+arguments
	subprocess.run(remuxCommand, capture_output=True, shell=True, encoding="utf-8")

	for filename2 in os.listdir(dir_demux):
	    filepath = os.path.join(dir_demux, filename2)
	    if os.path.isfile(filepath):
	    	os.remove(filepath)
	#os.system("cls")

print('\033[92m'+"--------------------------------------------- DONE ---------------------------------------------"+'\033[0m')
os.system("pause")