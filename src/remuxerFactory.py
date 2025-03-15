from src.prober import Prober
from src.demuxer import Demuxer, Mkvmerge_Demuxer, FFMPEG_Demuxer
from src.downmixer import Downmixer
from src.muxer import Muxer, Mkvmerge_Muxer, FFMPEG_Muxer
from src.remuxer import Remuxer


class RemuxerFactory:

    __atsc: str = '\"pan=stereo|c0 < 1.0*c0 + 0.707*c2 + 0.707*c4|c1 < 1.0*c1 + 0.707*c2 + 0.707*c5\"'
    __atscboost: str = '\"volume=2.0,pan=stereo|c0 < 1.0*c0 + 0.707*c2 + 0.707*c4|c1 < 1.0*c1 + 0.707*c2 + 0.707*c5\"'
    __lfe: str = '\"pan=stereo|c0=0.5*c2+0.707*c0+0.707*c4+0.5*c3|c1=0.5*c2+0.707*c1+0.707*c5+0.5*c3\"'
    __night: str = '\"pan=stereo|c0=c2+0.30*c0+0.30*c4|c1=c2+0.30*c1+0.30*c5\"'

    def getRemuxer(self, muxer_str: str, algorithm: str) -> Remuxer:
        prober_inst: Prober = Prober()
        if muxer_str == 'mkvmerge':
            prober_inst: Prober = Prober(limitedToAudio=True)
            demuxer_inst: Demuxer = Mkvmerge_Demuxer()
            muxer_inst: Muxer = Mkvmerge_Muxer()
        elif muxer_str == 'ffmpeg':
            prober_inst: Prober = Prober(limitedToAudio=False)
            demuxer_inst: Demuxer = FFMPEG_Demuxer()
            muxer_inst: Muxer = FFMPEG_Muxer()
        else:
            print('invalid muxer, using ffmpeg by default')
            print('list of valid muxers: getmuxers()')
            print()
            demuxer_inst: Demuxer = FFMPEG_Demuxer()
            muxer_inst: Muxer = FFMPEG_Muxer()

        if algorithm == 'atsc':
            downmixer_inst: Downmixer = Downmixer(RemuxerFactory.__atsc)
        elif algorithm == 'atscboost':
            downmixer_inst: Downmixer = Downmixer(RemuxerFactory.__atscboost)
        elif algorithm == 'lfe':
            downmixer_inst: Downmixer = Downmixer(RemuxerFactory.__lfe)
        elif algorithm == 'night':
            downmixer_inst: Downmixer = Downmixer(RemuxerFactory.__night)
        else:
            print('invalid downmix algorithm, using atscboost by default')
            print('get valid downmix options: getalgorithms()')
            downmixer_inst: Downmixer = Downmixer(RemuxerFactory.__atscboost)

        return Remuxer(prober_inst, demuxer_inst, downmixer_inst, muxer_inst)

    def getmuxers(self) -> list[str]:
        return ['ffmpeg', 'mkvmerge']

    def getalgorithms(self) -> dict[str, str]:
        algorithms = {}
        algorithms['atsc'] = 'ffmpeg default algorithm'
        algorithms['atscboost'] = 'atsc, plus voice volume boost'
        algorithms['lfe'] = 'doesn\'t discard the LFE channel'
        algorithms['night'] = 'useful for watching movies at night'
