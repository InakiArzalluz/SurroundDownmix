# SurroundDownmix

Python script to (batch) downmix audio (5.1 -> 2.0) in movies while retaining voice volume

 ### Pre-requirements *(Already included for Windows)*
 + ffmpeg and ffprobe (from [ffmpeg](https://ffmpeg.org/download.html))
 + mkvmerge (from [mkvtoolnix](https://mkvtoolnix.download/downloads.html))

 ### Limitations
 + Only takes mkv files as input
 + ~~Works exclusively on Windows~~
 + ~~Doesn't respect any (folder) structure present inside the input folder~~ 
 + ~~Doesn't seem capable of remuxing files that include H265 video~~
 + ~~Currently doesn't support containers with images included as metadata~~
 + ~~Currently doesn't support containers that include .otf or .ttf files~~

 ### Usage
 + if it's the first time using it, run 'python Remux.py' in a terminal
 to create the necessary folders 
 + Drop the files to downmix inside the auto-created 'A-Input' folder
 + run 'python Remux.py' in a terminal