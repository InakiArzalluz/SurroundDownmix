import os
from src.tools import tools
from src.prober import prober
from src.demuxer import demuxer
from src.downmixer import downmixer
from src.muxer import muxer


class remuxer:
    """

    """
    def __init__(self, prober: prober, demuxer: demuxer, downmixer: downmixer, muxer: muxer):
        self.__prober_inst: prober = prober
        self.__downmixer_inst: downmixer = downmixer
        self.__demuxer_inst: demuxer = demuxer
        self.__muxer_inst: muxer = muxer

    def remux(self, inputfile_path: str, remuxfile_path: str):
        """
        Remuxes a video file, downmixing all audio from 5.1 to 2.0

        inputfile_path: name and location of the input file
        remuxfile_path: name and location for the output file
        """

        dir_demux = os.path.join(os.getcwd(), 'Demux')
        try:
            os.mkdir(dir_demux)
        except OSError as error:
            if error.errno != 17:
                print(error)

        list_streams = self.__prober_inst.probe(inputfile_path)
        print('Demuxing')
        dict_dict_stream = self.__demuxer_inst.demux(inputfile_path, dir_demux, list_streams)

        print("Downmixing")
        # TODO: Concurrency
        keys = list(dict_dict_stream.keys()).copy()
        for key in keys:
            if key[0:1] != '/' and dict_dict_stream[key]['channels'] == '6':
                codec = dict_dict_stream[key]['codec_name']
                newkey: str = self.__downmixer_inst.downmix(key, codec)
                dict_dict_stream[newkey] = dict_dict_stream[key]
                del dict_dict_stream[key]

        print("Muxing")
        self.__muxer_inst.mux(inputfile_path, remuxfile_path, dict_dict_stream)

        del dict_dict_stream
        tools.cleanFolder(dir_demux)
