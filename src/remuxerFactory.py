from src.prober import prober
from src.demuxer import demuxer, mkvmerge_demux, ffmpeg_demux
from src.downmixer import downmixer
from src.muxer import muxer, mkvmerge_mux, ffmpeg_mux
from src.remuxer import remuxer


class remuxerFactory:

    __atsc: str = '\"pan=stereo|c0 < 1.0*c0 + 0.707*c2 + 0.707*c4|c1 < 1.0*c1 + 0.707*c2 + 0.707*c5\"'
    __atscboost: str = '\"volume=2.0,pan=stereo|c0 < 1.0*c0 + 0.707*c2 + 0.707*c4|c1 < 1.0*c1 + 0.707*c2 + 0.707*c5\"'
    __lfe: str = '\"pan=stereo|c0=0.5*c2+0.707*c0+0.707*c4+0.5*c3|c1=0.5*c2+0.707*c1+0.707*c5+0.5*c3\"'
    __night: str = '\"pan=stereo|c0=c2+0.30*c0+0.30*c4|c1=c2+0.30*c1+0.30*c5\"'

    def getRemuxer(self, muxer_str: str, algorithm: str) -> remuxer:
        prober_inst: prober = prober()
        if muxer_str == 'mkvmerge':
            prober_inst: prober = prober(limitedToAudio=True)
            demuxer_inst: demuxer = mkvmerge_demux()
            muxer_inst: muxer = mkvmerge_mux()
        elif muxer_str == 'ffmpeg':
            prober_inst: prober = prober(limitedToAudio=False)
            demuxer_inst: demuxer = ffmpeg_demux()
            muxer_inst: muxer = ffmpeg_mux()
        else:
            print('invalid muxer, using ffmpeg by default')
            print('list of valid muxers: getmuxers()')
            print()
            demuxer_inst: demuxer = ffmpeg_demux()
            muxer_inst: muxer = ffmpeg_mux()

        if algorithm == 'atsc':
            downmixer_inst: downmixer = downmixer(remuxerFactory.__atsc)
        elif algorithm == 'atscboost':
            downmixer_inst: downmixer = downmixer(remuxerFactory.__atscboost)
        elif algorithm == 'lfe':
            downmixer_inst: downmixer = downmixer(remuxerFactory.__lfe)
        elif algorithm == 'night':
            downmixer_inst: downmixer = downmixer(remuxerFactory.__night)
        else:
            print('invalid downmix algorithm, using atscboost by default')
            print('get valid downmix options: getalgorithms()')
            downmixer_inst: downmixer = downmixer(remuxerFactory.__atscboost)

        return remuxer(prober_inst, demuxer_inst, downmixer_inst, muxer_inst)

    def getmuxers(self) -> list[str]:
        return ['ffmpeg', 'mkvmerge']

    def getalgorithms(self) -> dict[str, str]:
        algorithms = {}
        algorithms['atsc'] = 'ffmpeg default algorithm'
        algorithms['atscboost'] = 'atsc, plus voice volume boost'
        algorithms['lfe'] = 'doesn\'t discard the LFE channel'
        algorithms['night'] = 'useful for watching movies at night'
