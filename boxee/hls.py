""" HLS (HTTP Live Stream) module for boxee

Based on public example from
http://developer.boxee.tv/Examples:_HLS_(HTTP_Live_Streaming)

This file is part of the Boxee NRK App by havard.gulldahl@nrk.no

Released under a GPL3 license, see LICENSE.txt
"""

import mc
from urllib import quote_plus, urlencode

NRKSTREAMS = { # from takoi in http://forum.xbmc.org/showthread.php?tid=52824&page=32
"NRK1":"http://nrk1-i.akamaihd.net/hls/live/201543/nrk1/master_Layer5.m3u8", # NRK1 live
"NRK2":"http://nrk2-i.akamaihd.net/hls/live/201544/nrk2/master_Layer5.m3u8", # NRK2 live
"NRK3":"http://nrk3-i.akamaihd.net/hls/live/201545/nrk3/master_Layer5.m3u8", # NRK3/NRKSuper live
"VID23":"http://hlswebvid23-i.akamaihd.net/hls/live/204296/hlswebvid23/master_Layer6.m3u8",
"VID24":"http://hlswebvid24-i.akamaihd.net/hls/live/204297/hlswebvid24/master_Layer6.m3u8",
"VID25":"http://hlswebvid25-i.akamaihd.net/hls/live/204298/hlswebvid25/master_Layer6.m3u8",
"VID26":"http://hlswebvid26-i.akamaihd.net/hls/live/203761/hlswebvid26/master_Layer6.m3u8",
"VID27":"http://hlswebvid27-i.akamaihd.net/hls/live/203543/hlswebvid27/master_Layer6.m3u8",
"VID28":"http://hlswebvid28-i.akamaihd.net/hls/live/203544/hlswebvid28/master_Layer6.m3u8",
"VID29":"http://hlswebvid29-i.akamaihd.net/hls/live/203545/hlswebvid29/master_Layer6.m3u8",

}

def HLSListItem(url, **kwargs):
    """Create a playable ListItem from an HLS resource"""
    quality = kwargs.get('quality', 'A') #set playlist stream bandwith, 0, 1, A (low, high, adaptive)
    title = kwargs.get('title', 'My funky HLSListItem')
    if url in NRKSTREAMS.keys(): # 'url' is a key in NRKSTREAMS dict
        title = url
        url = NRKSTREAMS(url)
    playlist_url = "playlist://%s?%s" % (quote_plus(url), urlencode({'quality':quality}))

    print playlist_url

    item = mc.ListItem(mc.ListItem.MEDIA_VIDEO_EPISODE)
    item.SetPath(playlist_url)
    item.SetLabel(title)
    item.SetContentType('application/vnd.apple.mpegurl')
    return item # and then mc.GetPlayer().Play(item)
    
    