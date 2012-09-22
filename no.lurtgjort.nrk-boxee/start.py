""" init script for Boxee NRK App

This file is part of the Boxee NRK App by havard.gulldahl@nrk.no

Released under a GPL3 license, see LICENSE.txt
"""

import mc
import httplib
import os.path
import urlparse
import datetime
import hls
import simplejson
from BeautifulSoup import BeautifulSoup

def utf8(str):
	return unicode(str).encode('utf-8')

def setLabel(id, str):
	return mc.GetActiveWindow().GetLabel(id).SetLabel(unicode(str).encode('utf-8'))

def main():
	mc.ActivateWindow(14000)
	mc.ShowDialogWait() # show spinner
	
	# initialise menu
	initMenu()
	mc.HideDialogWait()

def initMenu():
	menu = ['Direkte', 'Aktuelt', 'Sjangrer', 'Program', 'Favoritter', 'Søk', ]
	items = mc.ListItems()
	for p in menu:
		item = mc.ListItem(mc.ListItem.MEDIA_VIDEO_CLIP)
		item.SetLabel(p)
		items.append(item)
		
	mc.GetActiveWindow().GetList(100).SetItems(items)

def menuClicked(item):
	mc.ShowDialogWait()
	mc.GetActiveWindow().GetLabel(1110).SetVisible(False)
	mc.GetActiveWindow().GetLabel(1120).SetVisible(False)
	
	lbl = item.GetLabel()
	
	setLabel(99, lbl)

	if lbl == 'Direkte': # live
		listLive()
	elif lbl in ['Aktuelt', 'Program']:
		progs = getShow(lbl)
		listProgs(progs)
	elif lbl in ['Favoritter', ]:
		progs = getFavorites()
		listProgs(progs)
	elif lbl == 'Søk':
		pass
	mc.HideDialogWait()
	
def listLive():
	items = mc.ListItems()
	
	now = datetime.datetime.now().hour
	ISSUPERTIME = now < 20 and now > 6
	print "IS SUPER TIME: %s" % ISSUPERTIME

	def nrkItem(channel, title, playthumb):
		print "nrkItem: %s %s %s" % (channel, title , playthumb)
		i = hls.LiveChannel(channel) 
		i.SetProviderSource('Norsk Rikskringkasting')
		i.SetThumbnail(playthumb)
		i.SetTitle(title)
		return i
	
	# get thumbs
	nrk1t, nrk2t, nrk3t = getNowPlayingThumbs()
	print repr(nrk1t)

	nrk1 = nrkItem('nrk1', nrk1t['title'], nrk1t['url'])
	nrk2 = nrkItem('nrk2', nrk2t['title'], nrk2t['url'])
	nrk3 = nrkItem('nrk3', nrk3t['title'], nrk3t['url'])

	# nrk1.SetProperty('streamid', 'id')
	
	nrk1.SetDescription(formatEpg(getEpg('NRK1')))
	nrk2.SetDescription(formatEpg(getEpg('NRK2')))
	nrk3.SetDescription(formatEpg(getEpg('NRK3')))
	
	items.append(nrk1)
	items.append(nrk2)
	items.append(nrk3)

	mc.GetActiveWindow().GetList(110).SetItems(items)

	mc.GetActiveWindow().GetList(120).SetVisible(False)
	mc.GetActiveWindow().GetList(130).SetVisible(False)
	mc.GetActiveWindow().GetList(110).SetVisible(True)
	mc.GetActiveWindow().GetList(110).SetFocus()	
	
def listProgs(progs):
	print "listprogs: %s" % progs
	
def GET(location):
	parsed = urlparse.urlparse(location)
	conn = httplib.HTTPConnection(parsed[1])
	conn.request("GET", parsed[2])
	res = conn.getresponse()
	print res.status, res.reason
	return res

def getEpg(channelname):
	res = GET("http://tv.nrk.no/livebufferepgentriesjson/%s" % channelname.lower())
	epg = simplejson.loads(res.read().decode("utf-8"))
	# print epg
	return epg

def getNowPlayingThumbs():
	#http://tv.nrk.no/getnownext/nrk3?districtChannel=	
	stub = GET("http://tv.nrk.no/getnownext/nrk3")
	htmlstub = BeautifulSoup(stub.read().decode("utf-8"))
	ret = []
	for el in htmlstub.findAll('img'):
		ret.append( { 'title': utf8(el['alt']), 'url': utf8(el['src']) } )
	return ret

def putImage(url):
	f = os.path.join(mc.GetTempDir(), os.path.basename(url))
	print "putImage: %s -> %s" % (url, f)
	o = open(f, 'w+b')
	o.write(GET(url).read())
	print "closing..."
	o.close()
	return f

def play(item):
	confirm = mc.ShowDialogConfirm('NRK', 'Would you like to play "%s"?' % item.GetLabel(), 'Cancel', 'Play')
	if confirm:
		mc.LogInfo("play item: %s" % item)
		mc.GetPlayer().Play(item)

def setBitrate(idx):
	print "setbitrate:%s" % idx

def formatEpg(seq):
	return ("\n".join( ["%s\n>> %s" % (e["PlannedStartTimeShortString"], e["Title"]) for e in seq] ).encode('utf-8'))

	
main() # run init