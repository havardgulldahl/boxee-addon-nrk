﻿""" init script for Boxee NRK App

This file is part of the Boxee NRK App by havard.gulldahl@nrk.no

Released under a GPL3 license, see LICENSE.txt
"""

import mc
import httplib
import os.path
import urlparse
import urllib
import datetime
import re
import hls
import simplejson
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup

# use constants with a value that match the localized strings in boxee
# http://developer.boxee.tv/Localization
LABEL_LIVE = 54075
LABEL_RECENT = 54063
LABEL_GENRES = 135
LABEL_PROGRAMS = 350
LABEL_FAVORITES = 52111
LABEL_PLAYLIST = 559
LABEL_SEARCH = 137

# some defaults
MAX_SAVED_LIST_LENGTH = 10

def utf8(s):
	if isinstance(s, str): 
		return s
	else: 
		return unicode(s).encode('utf-8')

def setLabel(id, str):
	return mc.GetActiveWindow().GetLabel(id).SetLabel(utf8(str))

def main():
	mc.ActivateWindow(14000)
	mc.ShowDialogWait() # show spinner
	
	# initialise menu
	initMenu()
	mc.HideDialogWait() # remove spinner

def initMenu():
	menu = [LABEL_LIVE, LABEL_RECENT, LABEL_GENRES, LABEL_PROGRAMS, LABEL_FAVORITES, LABEL_PLAYLIST, LABEL_SEARCH]
	items = mc.ListItems()
	for _id in menu:
		item = mc.ListItem(mc.ListItem.MEDIA_VIDEO_CLIP)
		item.SetLabel(mc.GetLocalizedString(_id)) # this'll give us a localized menu for free
		item.SetProperty("id", str(_id)) # keep the constant for later
		items.append(item)
		
	mc.GetActiveWindow().GetList(100).SetItems(items)

def menuClicked(item):
	mc.ShowDialogWait()
	mc.GetActiveWindow().GetLabel(1110).SetVisible(False)
	mc.GetActiveWindow().GetLabel(1120).SetVisible(False)
	mc.GetActiveWindow().GetLabel(1130).SetVisible(False)
	
	lbl = int(item.GetProperty("id"), 10) # get the menu item constant -- see initMenu()
	# print "menulabel clicked : %s" % lbl
	
	if lbl == LABEL_LIVE: # live
		listLive()
	elif lbl in [LABEL_RECENT,]:
		videoitems = getRecent()
		listVideoItems(videoitems)
	elif lbl in [LABEL_PROGRAMS,]:
		listPrograms()
	elif lbl in [LABEL_FAVORITES,LABEL_PLAYLIST]:
		videoitems = getSavedList(lbl)
		if len(videoitems) > 0:
			listVideoItems(videoitems)
		else:
			showError(1120)
	elif lbl == LABEL_GENRES:
		listGenres()
	elif lbl == LABEL_SEARCH:
		videoitems = doSearch()
		if len(videoitems) > 0:
			listVideoItems(videoitems)
		else:
			showError(1130)
	mc.HideDialogWait()
	
def showError(controlid):
	"Get a control id for an error label and make sure it's visible, and hide all other controls"
	mc.GetActiveWindow().GetList(110).SetVisible(False)
	mc.GetActiveWindow().GetList(120).SetVisible(False)
	mc.GetActiveWindow().GetList(130).SetVisible(False)
	mc.GetActiveWindow().GetLabel(1110).SetVisible(False)
	mc.GetActiveWindow().GetLabel(1120).SetVisible(False)
	mc.GetActiveWindow().GetLabel(1130).SetVisible(False)
	mc.GetActiveWindow().GetLabel(controlid).SetVisible(True)
	
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
	# print repr(nrk1t)

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
	
def listPrograms(genre=None,letter=None):
	print "listprogs: genre %s -- letter %s" % (genre, letter)
	items = mc.ListItems()
	
	return items
	
def listVideoItems(items):
	# print "listitems: %s" % items

	# add videos to videoitem panel
 	mc.GetActiveWindow().GetList(130).SetItems(items)
	# hide other panels
	mc.GetActiveWindow().GetList(120).SetVisible(False)
	mc.GetActiveWindow().GetList(110).SetVisible(False)
	# show videoitem panel
	mc.GetActiveWindow().GetList(130).SetVisible(True)
	mc.GetActiveWindow().GetList(130).SetFocus()	
	
def listGenres():
	items = mc.ListItems()
	for genre in getGenres():
		item = mc.ListItem(mc.ListItem.MEDIA_VIDEO_CLIP)
		item.SetLabel(genre['title'])
		item.SetTitle(genre['title'])
		item.SetProperty('url', genre['url'])
		items.append(item)

	mc.GetActiveWindow().GetList(120).SetItems(items)
	
	mc.GetActiveWindow().GetList(110).SetVisible(False)
	mc.GetActiveWindow().GetList(130).SetVisible(False)
	mc.GetActiveWindow().GetList(120).SetVisible(True)
	mc.GetActiveWindow().GetList(120).SetFocus()

def getSavedList(kind):
	config = mc.GetApp().GetLocalConfig() # hook up to persistant store for playlist and favorites
	items = mc.ListItems()
	if kind == LABEL_PLAYLIST: # get current playlist
		jsonlist = config.GetValue("playlist")
		simpleitems = config.Implode('||', 'playlist').split('||')
	elif kind == LABEL_FAVORITES: # get favorited items or shows
		jsonlist = config.GetValue("favorites")
		simpleitems = config.Implode('||', 'favorites').split('||')
	# print "got json list from storage: %s" % repr(jsonlist)
	print "got list from storage: %s" % repr(simpleitems)
	# try:
		# simpleitems = simplejson.loads(jsonlist)
	# except ValueError: # empty list
		# return mc.ListItems()
	for i in simpleitems:
		ii = {'id':i, 'ThumbUrl':'http://gfx.nrk.no%s' % config.GetValue(i)}
		print "got simpleitem from list: %s " % ii
		items.append(simplestructToItem(ii))
	return items
		
def addToSavedList(item, listname):
	config = mc.GetApp().GetLocalConfig() # hook up to persistant store for playlist and favorites
	print "addTo saved list: %s listname:%s" % (item.GetLabel(), listname)
	print "currentlist: --%s--" % repr(config.Implode(", ", listname))
	config.PushBackValue(listname, item.GetProperty('id'))
	config.SetValue(item.GetProperty('id'), urlparse.urlparse(item.GetProperty('ThumbUrl'))[2]) # add the thumbnail (just the path) to 'cache'
	print "newlist: --%s--" % repr(config.Implode(", ", listname))
	return True
		
def genreClicked(genre):
	# print "genre cliked: %s" % genre.GetLabel()
	mc.ShowDialogWait()
	#http://tv.nrk.no/listobjects/recentlysentbycategory/barn.json/page/1
	url = 'http://tv.nrk.no/listobjects/recentlysentbycategory/%s.json/page/0' % os.path.basename(genre.GetProperty('url'))
	# print url
	items = listObjectsToItems(url, genre.GetLabel())
	listVideoItems(items)
	mc.HideDialogWait()

def getRecent():
	url = "http://tv.nrk.no/listobjects/recentlysent.json/page/0"
	return listObjectsToItems(url)

def simplestructToItem(struct):
	"We only have a id, we need to look it up"
	metadata = getMetadataForId(struct['id'])
	# {u'availableFrom': 1349549912000L, u'startBitrateIndex': 3, u'available': True, u'mediaAnalyticScript': {u'category': u'dokumentar-og-fakta', u'title': u'den-vidunderlige-kysten-78', u'playerId': u'flash', u'deliveryType': u'O', u'contentLength': u'55-60 min', u'show': u'den-vidunderlige-kysten', u'pageReferrer': u'document.referrer', u'pageUrl': u'document.URL', u'device': u'desktop'}, u'playerType': u'flash', u'mediaURL': u'http://nordond20b-f.akamaihd.net/z/no/open/a2/a2047f62cde7cc5c1534d159065fa1f7d41129a6/a2047f62cde7cc5c1534d159065fa1f7d41129a6_,141,316,563,1266,2250,.mp4.csmil/manifest.f4m', u'maximumBitrateIndex': 4, u'availableTo': 1352195100000L, u'title': u'Den vidunderlige kysten', u'mediaElementType': u'Program', u'mediaType': u'Video', u'messageType': u'NoMessage', u'imageId': u'V5bAD_fJWWJtfA55ofthKQ', u'live': False, u'geoBlocked': True, u'scoresStatsScript': {u'springStreamContentType': u'desktop', u'springStreamSite': u'nrkstream', u'springStreamStream': u'programspiller/odm/dokumentar-og-fakta/den-vidunderlige-kysten/s01e07.den-vidunderlige-kysten.koid24002611', u'springStreamProgramId': u'KOID24002611'}, u'legalAge': u'A', u'id': u'koid24002611', u'channel': False, u'description': u'Br. dokumentarserie. Det britiske kystprogrammet er kommet til naboen i nord\xf8st, Norge. Her utforskes vestlandskysten og den overhengende rasfaren som truer den vakre bygda Geiranger. Mark Horton leter etter opphavet til vikingskipets design. Er det en forbindelse mellom den og moderne b\xe5ter? (Coast) (7:8)'}
	if metadata.has_key('mediaURL'):
		struct['MediaURL'] = getPathForMediaURL(metadata['mediaURL'])
	if metadata.has_key('description'):
		struct['Description'] = metadata['description']
	if metadata.has_key('title'):
		struct['Title'] = metadata['title']
	struct['Url'] = '/program/%s' % struct['id']
	return structToItem(struct)
	
def structToItem(i):
	item = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN) # MEDIA_UNKOWN is the only type where http thumbnails show up
	item.SetLabel(utf8(i['Title']))
	item.SetTitle(utf8(i['Title']))
	item.SetProperty('url', utf8(i['Url']))
	if i.has_key('ImageUrl'):
		item.SetThumbnail(utf8(i['ImageUrl']))
		item.SetProperty('thumbUrl', utf8(i['ImageUrl']))
	if i.has_key('Description'):
		item.SetDescription(utf8(i['Description']))
	if i.has_key('Genres') and len(i['Genres'])>0:
		item.SetProperty('genres', utf8(','.join(i['Genres'])))
		item.SetGenre(utf8(i['Genres'][0]))
	if i.has_key('ViewCount'):
		item.SetProperty('viewCount', utf8(i['ViewCount']))
	if i.has_key('MediaURL'):
		item.SetPath(utf8(i['MediaURL']))
	if i.has_key('id'):
		item.SetProperty('id', utf8(i['id']))
	iteminfo = parsePath(utf8(i['Url']))
	if not i.has_key('id') and iteminfo.has_key('id'): 
		item.SetProperty('id', iteminfo['id']) # this will get us our mediaURL later on
	if iteminfo.has_key('showtitle'): # TV Show title
		item.SetProperty('showtitle', iteminfo['showtitle'])
	if iteminfo.has_key('airdate'): # date first aired, datetime.date object
		item.SetDate(iteminfo['airdate'].year, iteminfo['airdate'].month, iteminfo['airdate'].day)
	if iteminfo.has_key('season'): # TV series season	
		item.SetProperty('season', str(iteminfo['season']))
	if iteminfo.has_key('episode'): # TV series episode
		item.SetProperty('episode', str(iteminfo['episode']))
	return item
	
def doSearch():
	items = mc.ListItems()
	itemsperrow = 4
	q = mc.ShowDialogKeyboard('Søk i hele NRK', '', False)
	if q:
		mc.ShowDialogWait()
		search = getSearch(q)
		i = 0
		for itm in search['direct']:
			items.append(structToItem(itm))
			i = i + 1
		if i > 0: # only if we've started filling items
			for y in range(itemsperrow - i % itemsperrow): # fill remaining items in this row with blanks
				itm = mc.ListItem(mc.ListItem.MEDIA_UNKNOWN)
				itm.SetLabel('')
				itm.SetThumbnail('')
				items.append(itm)
		for itm in search['reference']:
			items.append(structToItem(itm))
		mc.HideDialogWait()
	return items
	
def listObjectsToItems(url, genre=None):
	jsondoc = GET(url, Accept='application/json')
	res = simplejson.loads(jsondoc.read().decode('utf-8'))
	items = mc.ListItems()
	# {"ListObjectViewModels":[{"Title":"Danseakademiet 26:27","ImageUrl":"http://gfx.nrk.no/djo0urdjx-AdYOjj1csrrgU66bPW3i_pzxxfXn9ym8yg","Url":"/serie/danseakademiet/msui33007510/sesong-2/episode-26","ViewCount":0,"Categories":[{"Url":"/kategori/barn","Id":"barn","DisplayValue":"Barn"}]}
	for i in res['ListObjectViewModels']:
		item = structToItem(i)
		if genre is not None:
			item.SetGenre(genre)
		items.append(item)
	return items

def parsePath(url):
	# break up paths to extract as much info as possible
	# examples:
	# /serie/moffene/obui12005409/22-09-2012
	# /serie/danseakademiet/msui33007510/sesong-2/episode-26
	# /program/koid23007309
	# http://tv.nrk.no/serie/superkviss/msub17001412/09-05-2012#sok=dyrevenn
	# http://tv.nrk.no/serie/dyrevenn#sok=dyrevenn
	
	def findVideoId(s):
		return re.search(r'([a-zA-Z]{4}\d{8})', s).group(1)
	
	path = urlparse.urlparse(url)[2]
	print "parsePath: %s" % repr(path)
	components = [p for p in path.split('/') if len(p) > 0]
	ret = {}
	if components[0] == 'serie':
		ret['type'] = 'series'
		ret['showtitle'] = components[1]
		if len(components) == 2:
			return ret
		ret['id'] = components[2]
		try:
			d, m, y = [int(p, 10) for p in components[3].split('-')] # split date
			ret['airdate'] = datetime.date(y, m, d)
		except ValueError:
			# not a date at components[3], try to parse season and episode
			try:
				_info = "%s %s" % (components[3], components[4])
				ret['season'], ret['episode'] = map(int, re.match(r'sesong-(\d+)\ episode-(\d+)', _info).groups())
			except:
				pass

	elif components[0] == 'program':
		ret['type'] = 'program'
		ret['id'] = findVideoId(components[1])
	else:
		# fall back to id parsing
		print "unknown path structure: %s" % path
		try:
			ret['id'] = findVideoId(path)
		except:
			pass
	# print "parsed: %s" % repr(ret)
	return ret
	
def GET(location, **kwargs):
	parsed = urlparse.urlparse(location)
	conn = httplib.HTTPConnection(parsed[1])
	config = {'User-Agent': 'Curl 7.21.1'}
	config.update(kwargs)
	try:
		conn.request("GET", '%s?%s' % (parsed[2], parsed[4]), headers=config)
		res = conn.getresponse()
	except Exception, (e):
		mc.ShowDialogNotification('Problems connecting to the internet. Please check.')
		return None
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
	htmlstub = BeautifulSoup(stub.read().decode("utf-8"), convertEntities=BeautifulStoneSoup.ALL_ENTITIES)
	ret = []
	for el in htmlstub.findAll('img'):
		ret.append( { 'title': utf8(el['alt']), 'url': utf8(el['src']) } )
	return ret

def getGenres():
	#http://tv.nrk.no/kategori/
	stub = GET("http://tv.nrk.no/kategori/")
	html = BeautifulSoup(stub.read().decode("utf-8"), convertEntities=BeautifulStoneSoup.ALL_ENTITIES)
	ret = []
	for el in html.find(id='categoryList').findAll('a'):
		ret.append( { 'title': utf8(el.string), 'url': utf8(el['href']) } )
	return ret	

def getSearch(term):
	#http://tv.nrk.no/sok?q=hedda+gabler&filter=rettigheter	
	print "searching for term: %s" % term
	res = GET("http://tv.nrk.no/sok?q=%s&filter=rettigheter" % urllib.quote_plus(term))
	html = BeautifulSoup(res.read().decode("utf-8"), convertEntities=BeautifulStoneSoup.ALL_ENTITIES)
	def classre(cl):
		"Helper function to search throuch class attribute contents for single class match"
		return {'class': re.compile(r'\b%s\b' % cl)}
		
	def parselistobject(li):
		"Helper to parse listobject html to something that might pass as listobject json"
		# print "parselistobject: %s %s" % (type(li), li)
		ret = {}
		ret['Url'] = li.find('a', classre('listobject-link'))['href']
		ret['ImageUrl'] = li.find('a', classre('listobject-link')).find('img')['src']
		ret['Title'] = li.find('a', classre('listobject-link')).find('span', classre('listobject-title')).strong.string
		ret['Description'] = li.find('p').renderContents().replace('<b>', '[B]').replace('</b>', '[/B]').replace('<br>', '[CR]')
		try:
			ret['Genres'] = [os.path.basename(a['href']) for a in li.find('div', classre('stack-links')).findAll('a') if a['href'].startswith('http://tv.nrk.no/kategori')]
		except:
			pass
		try:
			ret['EpisodeUrls'] = [a['href'] for a in li.find('ul', classre('episode-links')).findAll('a')]
			if len(ret['EpisodeUrls']) > 0:
				ret['Url'] = ret['EpisodeUrls'][0] # replace with first episode link, since it's always explicitly pointing to an episode
		except Exception, (e):
			print str(e)
		return ret

	resultsblock = html.find(id='searchResult')
	hits = {'direct':[], 'reference':[]}
	try:
		# first line hits (title match)
		hits['direct'] = [parselistobject(li) for li in resultsblock.find('ul', classre('prepend-top')).findAll('li', classre('listobject'))]
	except:
		pass
	try:
		# general hits (description match)
		hits['reference'] = [parselistobject(li) for li in resultsblock.find('ul', classre('programList')).findAll('li', classre('listobject'))]
	except:
		pass
	return hits
	
def play(item):
	confirm = mc.ShowDialogConfirm('NRK', 'Would you like to play "%s"?' % item.GetLabel(), 'Cancel', 'Play')
	if confirm:
		print "playing item :%s" % repr(item.GetPath())
		if not item.GetPath():
			mc.ShowDialogWait()
			item.SetPath(getPathForId(item.GetProperty("id")))
			mc.HideDialogWait()
		mc.GetPlayer().Play(item)

def getMetadataForId(videoid):		
	url = "http://nrk.no/serum/api/video/%s" % videoid
	print "getting metadata for id: %s" % url
	json = simplejson.loads(GET(url, Accept='application/json').read().decode('utf-8'))
	# print json
	return json
		
def getPathForId(videoid, bitrate=2):
	if bitrate > 4: bitrate = 3
	json = getMetadataForId(videoid)
	url = getPathForMediaURL(utf8(json['mediaURL']))
	return url

def getPathForMediaURL(mediaURL, bitrate=2):
	url = mediaURL.replace('/z/', '/i/', 1)
	url = url.rsplit('/', 1)[0]
	url = url + '/index_%s_av.m3u8' % bitrate
	return url
	
def setBitrate(idx):
	print "setbitrate:%s" % idx

def formatEpg(seq):
	return ("\n".join( ["%s\n>> %s" % (e["PlannedStartTimeShortString"], e["Title"]) for e in seq] ).encode('utf-8'))

	
main() # run it