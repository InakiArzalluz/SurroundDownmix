# SurroundDownmix

Python script capable of automatically downmixing audio in movies from 5.1 to 2.0 while retaining the voice volume

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