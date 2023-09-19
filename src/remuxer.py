import os
from src.tools import tools
from src.prober import prober
from src.demuxer import demuxer
from src.downmixer import downmixer
from src.muxer import muxer


class remuxer:

    def __init__(self, prober: prober, demuxer: demuxer, downmixer: downmixer, muxer: muxer):
        self.__prober_inst: prober = prober
        self.__downmixer_inst: downmixer = downmixer
        self.__demuxer_inst: demuxer = demuxer
        self.__muxer_inst: muxer = muxer

    def remux(self, path_input: str, path_remux: str):
        
        dir_demux = os.path.join(os.getcwd(),'Demux')
        try:
            os.mkdir(dir_demux)
        except OSError as error:
            if error.errno != 17:
                print(error)
        
        list_streams = self.__prober_inst.probe(path_input)
        filename: str = os.path.basename(path_input)
        print('Demuxing')
        dict_dict_stream = self.__demuxer_inst.demux(path_input, dir_demux, list_streams)

        print("Downmixing")
        keys = list(dict_dict_stream.keys()).copy()
        for key in keys:
            if key[0:1] != '/' and dict_dict_stream[key]['channels'] == '6':
                codec = dict_dict_stream[key]['codec_name']
                newkey: str = self.__downmixer_inst.downmix(key, codec)
                dict_dict_stream[newkey] = dict_dict_stream[key]
                del dict_dict_stream[key]
        
        print('-----------------------------------------------------------------------------')
        print("Muxing")
        self.__muxer_inst.mux(path_input, path_remux, dict_dict_stream)
        
        del dict_dict_stream
        tools.cleanFolder(dir_demux)
