# SurroundDownmix

Python script to (batch) downmix audio (5.1 -> 2.0) in movies while retaining voice volume

 ### Pre-requirements
 + python 3.9+
 + ffmpeg and ffprobe (from [ffmpeg](https://ffmpeg.org/download.html))
 + mkvmerge (optional) (from [mkvtoolnix](https://mkvtoolnix.download/downloads.html))

 ### Limitations
 + Only takes mkv files as input (currently)
 + ~~Doesn't respect the folder structure present inside the input folder~~ 

 ### Usage
 + if it's the first time using it, run 'python main.py' in a terminal
 to create the necessary folders 
 + Drop the movies to process inside the 'A-Input' folder
 + run 'python main.py' in a terminal