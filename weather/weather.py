
# -*- coding: utf-8 -*- 
import math, time
import xml.etree.ElementTree as ET
import md5
import urllib2
import urllib, cStringIO
import os,sys
import Image, ImageDraw, ImageFont
import string, textwrap
import codecs
import locale
locale.setlocale(locale.LC_ALL, 'de_DE.utf8')


searchUrl = 'http://api.wetter.com/forecast/weather'
projectName = 'rasberrypi'
apiKey = '8cd0874a702ede55175d0d8981738c03'
home = 'DE2925533'

resultSize = 1024,768

#g = ImageFont.load('/mnt/misc/rasberry/weather/fonts/lubB19.pil')
f = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 19)
g = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSansBold.ttf', 19)

class Quote:
	def __init__(self):
		self.quote = ''
		self.author = ''
		self.authorUrl = ''
		
	def __str__(self):
		return self.quote + '\n[' + self.author + '] ' + self.authorUrl

class Forecast:
	def __init__(self):
		self.date = ''
		self.weather = ''
		self.weatherText = ''
		self.windDirection = ''
		self.windDirectionText = ''
		self.windSpeed = 0
		self.maxTemp = ''
		self.minTemp = ''
		self.possibleRain = 0
	
	def __str__(self):
		return 'Date: ' + self.date + '\nWeather: ' + self.weatherText + ' (' + self.weather + ')\n' + 'Wind: ' + self.windDirection + ' (' + self.windDirectionText + ')\n' + 'Speed: ' + self.windSpeed + '\n' + 'Temperatur: ' + self.minTemp + '/' + self.maxTemp + '\n' + 'Rain: ' + self.possibleRain + '%'

def loadForecast(location):
	m = md5.new()
	m.update(projectName)
	m.update(apiKey)
	m.update(location)
	hash = m.hexdigest()

	url = searchUrl + '/city/' + location + '/project/' + projectName + '/cs/' + hash
	response = urllib2.urlopen(url)
	content = response.read()
	xml = ET.fromstring(content)
	return xml

def parseSingleForecast(forecastXml):
	print 'parseSingleForecast'
	forecast = Forecast()
	
	forecast.weather = forecastXml.findall('./w')[0].text
	forecast.weatherText = forecastXml.findall('./w_txt')[0].text
	forecast.windDirection = forecastXml.findall('./wd')[0].text
	forecast.windDirectionText = forecastXml.findall('./wd_txt')[0].text
	forecast.windSpeed = forecastXml.findall('./ws')[0].text
	forecast.maxTemp = forecastXml.findall('./tx')[0].text
	forecast.minTemp = forecastXml.findall('./tn')[0].text
	forecast.possibleRain = forecastXml.findall('./pc')[0].text
	forecast.date = forecastXml.attrib['value']
	
	
	return forecast
	
def parseForecast(xml):
	print 'parseForecast'
	datesXml = xml.findall('./forecast/date')
	today = parseSingleForecast(datesXml[0])
	tomorrow = parseSingleForecast(datesXml[1])
	dayAfterTomorrow = parseSingleForecast(datesXml[2])
		
	return today, tomorrow, dayAfterTomorrow

def generateBaseImage(xml):
	print 'generateBaseImage'
	baseImage = Image.new('RGBA', resultSize, 'white')
	wetterLogo = Image.open('icon/wettercom.jpg')
	baseWidth, baseHeight = baseImage.size
	baseWidth -= 10
	baseHeight -= 10
	logoWidth, logoHeight = wetterLogo.size
	
	creditText = xml.findall('./credit/text')[0].text
	draw = ImageDraw.Draw(baseImage)
#	f = ImageFont.load('fonts/helvr12.pil')
	f = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeMono.ttf',12)
	
	draw.line((0,235, 1024, 235), fill='black')
	
	textsize = draw.textsize(creditText, f)
	creditbox = (baseWidth - logoWidth - textsize[0] - 10, 
	baseHeight - logoHeight + (textsize[1]/(2) + 10) )
	draw.text(creditbox, creditText, font=f, fill = 'black')
	
	logobox = (baseWidth - logoWidth, baseHeight - logoHeight)
	baseImage.paste(wetterLogo, logobox)
	return baseImage

def calcBeaufort(kmh):
	print 'calcBeaufort'
	ms = float(kmh) * 1000.0 / 3600.0
	b = math.pow(ms / 0.8360, 2.0/3.0)

	return int(b)

def getSubstring(content, startMarker, endMarker):
	start = string.find(content, startMarker)
	end = string.find(content, endMarker, start)
	return content[start + len(startMarker):end]

	
def loadQuote():
	print 'loadQuote'
	quote = Quote()
	
	response = urllib2.urlopen('http://zitate.net/zitate.html')
	content = response.read()
	encoding = response.headers['content-type'].split('charset=')[-1]
	print encoding
	content = unicode(content, encoding)
	quote.quote = getSubstring(content, '<td class="quote" id="quote">', '<p class="author" id="author">')
	quote.author = getSubstring(content, '<img alt="', '" height="')
	quote.authorUrl = getSubstring(content, ' id="image" src="', '" title="')
	
	return quote
	
def cleanUmlauts(str):
#	return str.replace("ä", 'ae').replace("ö", 'oe').replace("ü", 'ue').replace("ß", 'ss')
	return str

def quoteOfTheDay(img, quote):
	print 'quoteOfTheDay'
	draw = ImageDraw.Draw(img)

	draw.text((15, 15), 'Spruch des Tages',
	font = g, fill='black')

	try:
		authorImg = Image.open(cStringIO.StringIO(urllib.urlopen(quote.authorUrl).read()))
		img.paste(authorImg, (10, 65))

	        draw.text((10, 175), cleanUmlauts(quote.author),
        	font=f, fill='grey')
	except:
		None

	lines = textwrap.wrap(quote.quote, 70)
	i = 0
	for line in lines:
		draw.text((85, 70 + (i * 25)), cleanUmlauts(line),
		font = f, fill='black')
		i += 1
	
	
	return img
	
def addForecastsToImage(img, forecasts):
	print 'addForecastToImage'
	draw = ImageDraw.Draw(img)
	
	segmentWidth = img.size[0] * (1 / 3.0)
	
	i = 0
	for forecast in forecasts:
		realDate = time.strptime(forecast.date, '%Y-%m-%d')
		header = time.strftime('%A, %d. %B %Y', realDate)
		
		segmentStart = img.size[0] * (i / 3.0)
		segmentMiddle = segmentStart + (segmentWidth / 2.0)
		
		segmentLabelWidth = segmentStart + (segmentWidth / 8.0)
		segmentTextWidth = segmentStart + (segmentWidth / 8.0 * 5.75)
		
		draw.text((segmentMiddle - draw.textsize(header, f)[0]/2.0, 275),
		header, font = g, fill='black')
		
		draw.text((int(segmentLabelWidth), 350),
		'Vorhersage: ', font = f, fill='black')
		weatherIcon = Image.open('icon/weather/d_' + forecast.weather[0:1] + '_b.png')
		img.paste(weatherIcon, (int(segmentTextWidth), 340), weatherIcon)
		
		draw.text((int(segmentLabelWidth), 425),
		'Min. Temp:  ', font = f, fill='black')
		draw.text((int(segmentTextWidth), 425),
		forecast.minTemp + ' \xb0C', font = f, fill='black')

		draw.text((int(segmentLabelWidth), 475),
		'Max. Temp:  ', font = f, fill='black')
		draw.text((int(segmentTextWidth), 475),
		forecast.maxTemp + ' \xb0C', font = f, fill='black')

		draw.text((int(segmentLabelWidth), 550),
		'Regenwahrsch.:  ', font = f, fill='black')
		draw.text((int(segmentTextWidth), 550),
		forecast.possibleRain + '%', font = f, fill='black')
		
		draw.text((int(segmentLabelWidth), 625),
		'Windrichtung:', font = f, fill='black')
		windIcon = Image.open('icon/weather/' + forecast.windDirectionText + '.png')
		img.paste(windIcon, (int(segmentTextWidth), 615), windIcon)

		draw.text((int(segmentLabelWidth), 675),
		'Windst\xe4rke:  ', font = f, fill='black')
		
		draw.text((int(segmentTextWidth), 675),
		str(calcBeaufort(forecast.windSpeed)) + ' bft', font = f, fill='black')
				
		i = i + 1
		
	return img

xml = loadForecast(home)
forecasts = parseForecast(xml)
quote = loadQuote()
img = generateBaseImage(xml)
quoteOfTheDay(img, quote)
addForecastsToImage(img, forecasts)
img.save('output.png')
