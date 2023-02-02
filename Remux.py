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
dir_inputs = parentFolder+"\\A-Inputs"
ffmpegExe = "\""+parentFolder+"\\Tools\\ffmpeg\\ffmpeg.exe\""
for filename in os.listdir(dir_inputs):
	print("--------------------------------------------- FFPROBE ---------------------------------------------")
	print(filename)
	ffprobeCommand = "\""+parentFolder+"\\Tools\\ffmpeg\\ffprobe.exe\" -v error -show_entries stream=index,codec_name,codec_type,channels:stream_tags=language,filename:disposition=default,forced \""+dir_inputs+"\\"+filename+"\""
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
	typeCounter_dict = {'v':0, 'a':0, 's':0, 'NoLoSe':0, 't':0}
	streams = ""
	attachments = ""
	dict_dict_stream = {} # key=filename(que tiene un unico stream), value=dict de info de ese unico stream
	for stream in list_streams:
		stream_dict = {}
		infos = stream.rsplit(sep="\n")
		infos.remove("")
		for info in infos:
			dict_entry = info.rsplit(sep="=")
			stream_dict[dict_entry[0]] = dict_entry[1]
		codec = stream_dict["codec_name"]
		file2Write=stream_dict["index"]+"_"+filename.rsplit(sep=".")[0]+"_"+stream_dict["codec_type"]

		if('DISPOSITION:forced' in stream_dict and stream_dict['DISPOSITION:forced'] == '1'):
			file2Write += "_forced"
		if('TAG:language' in stream_dict):
			file2Write += "_"+stream_dict['TAG:language']
		codec = stream_dict["codec_name"]
		if (codec in extensions_dict):
			file2Write += "."+extensions_dict[codec] # por h264, subrip, etc.
		else:
			file2Write += "."+codec

		if(stream_dict["codec_type"] == 'attachment'):
			attachments += "-dump_attachment:" + stream_dict["index"] + " \""+parentFolder+"\\Demux\\" 
			if("TAG:filename" in stream_dict):
				file2Write = stream_dict["TAG:filename"]
			attachments += file2Write+"\" "
		else:
			streams += "-map 0:" + stream_dict["index"] + " -c copy " +"\""+parentFolder+"\\Demux\\" +file2Write+"\" "
		dict_dict_stream[file2Write]=stream_dict
		print(file2Write)

	ffmpegCommand =	ffmpegExe + " -y -i " + "\""+parentFolder+"\\A-Inputs\\"+filename+"\" " + streams
	print('\033[92m'+"ffmpegCommand: "+'\033[0m')
	print(ffmpegCommand)
	subprocess.run(ffmpegCommand, capture_output=True, shell=True, encoding="utf-8")
	if(attachments != ""):
		attachmentsCommand = ffmpegExe +" "+attachments+ "-i " + "\""+parentFolder+"\\A-Inputs\\"+filename+"\""
		print('\033[92m'+"attachments command: "+'\033[0m')
		print(attachmentsCommand)
		subprocess.run(attachmentsCommand, capture_output=True, shell=True, encoding="utf-8")
	# MkvExtractCommand = "\""+parentFolder+"\\Tools\\mkvtoolnix\\mkvextract.exe\"  \""+parentFolder+"\\A-Inputs\\"+filename+"\""

	print("--------------------------------------------- Downmixing ---------------------------------------------")

	directory = parentFolder+"\\Demux"
	for filename2 in os.listdir(directory):
	    filepath = os.path.join(directory, filename2)
	    if os.path.isfile(filepath):
	    	if (filename2.find("_downmix") != '-1'): #Dudoso, no se si -1 es un string o no
		    	if('channels' in dict_dict_stream[filename2]  and dict_dict_stream[filename2]['channels']=='6'):
		    		print(filename2)
		    		codec = dict_dict_stream[filename2]['codec_name']
		    		# ffmpeg -i "sourcetrack.dts" -c dca -af "pan=stereo|c0=c2+0.30*c0+0.30*c4|c1=c2+0.30*c1+0.30*c5" "stereotrack.dts"
		    		filenameNoExt=filename2.rsplit(sep=".")[0]
		    		downmixCommand = ffmpegExe + " -i " + "\""+filepath+"\"" + " -c " + codec + " -af " + algoritmoDownix + " "  + "\""+directory+"\\"+filenameNoExt+"_downmix."+codec+"\""
		    		subprocess.run(downmixCommand, capture_output=True, shell=True, encoding="utf-8")
		    		dict_dict_stream[filenameNoExt+"_downmix."+codec] = dict_dict_stream[filename2]
		    		del dict_dict_stream[filename2]
		    		os.remove(filepath)
	    		
	print("--------------------------------------------- Remuxing ---------------------------------------------")

	maps = metadata = imports = dispositions = ""
	counter = 0
	typeCounter_dict = {'v':0, 'a':0, 's':0, 'NoLoSe':0, 't':0}
	for filename3 in os.listdir(directory):
	    filepath = os.path.join(directory, filename3)
	    if os.path.isfile(filepath):
	    	extension = filename3.rsplit(sep=".")[-1]
	    	imports += " -i " + "\""+filepath+"\""
	    	maps += " -map "+str(counter)+":0"
	    	metadataType = dict_dict_stream[filename3]['codec_type'][0]
	    	if('TAG:language' in dict_dict_stream[filename3]):
	    		metadata += " -metadata:s:"+metadataType+":"+str(typeCounter_dict[metadataType])+" language="+dict_dict_stream[filename3]['TAG:language']

	    	if('DISPOSITION:default' in dict_dict_stream[filename3] and dict_dict_stream[filename3]['DISPOSITION:default'] == '1'):
	    		print("sets "+ filename3 + " as default " +dict_dict_stream[filename3]['codec_type'])
	    		dispositions += " -disposition:"+metadataType+":"+str(typeCounter_dict[metadataType])+" +default"

	    	if('DISPOSITION:forced' in dict_dict_stream[filename3] and dict_dict_stream[filename3]['DISPOSITION:forced'] == '1'):
	    		print("sets "+ filename3 + " as forced " +dict_dict_stream[filename3]['codec_type'])
	    		dispositions+="+forced"
	    		#dispositions += " -disposition:"+metadataType+":"+str(typeCounter_dict[metadataType])+" forced"
	    	typeCounter_dict[dict_dict_stream[filename3]['codec_type'][0]] +=1
	    	counter += 1
	remuxCommand = ffmpegExe + imports + " -c copy" + maps + metadata + dispositions + " \""+parentFolder+"\\Remux\\"+filename+"\""
	print(remuxCommand)
	subprocess.run(remuxCommand, capture_output=True, shell=True, encoding="utf-8")

	for filename2 in os.listdir(directory):
	    filepath = os.path.join(directory, filename2)
	    if os.path.isfile(filepath):
	    	os.remove(filepath)
	os.system("cls")

print('\033[92m'+"--------------------------------------------- DONE ---------------------------------------------"+'\033[0m')
os.system("pause")