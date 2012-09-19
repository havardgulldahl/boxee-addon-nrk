""" init script for Boxee NRK App

This file is part of the Boxee NRK App by havard.gulldahl@nrk.no

Released under a GPL3 license, see LICENSE.txt
"""


import httplib
import simplejson

def getEpg(channelname):
	conn = httplib.HTTPConnection("tv.nrk.no")
	print "/livebufferepgentriesjson/%s" % channelname.lower() 
	conn.request("GET", "/livebufferepgentriesjson/%s" % channelname.lower())
	res = conn.getresponse()
	print res.status, res.reason
	epg = simplejson.loads(res.read().decode("utf-8"))
	print epg
	return epg

import mc
 
mc.ActivateWindow(14000)
