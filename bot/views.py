from django.shortcuts import render

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from urllib.request import urlopen
from xml.etree.ElementTree import parse

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

def get_weather(location):
	url = "http://opendata.cwb.gov.tw/opendataapi?dataid=F-C0032-001&authorizationkey={key}".format(key = settings.WEATHER_AUTHORIZATION_KEY)
	response = urlopen(url)
	tree = parse(response)
	root = tree.getroot()
	# namespace means xmlns in xml file
	namespace = '{urn:cwb:gov:tw:cwbcommon:0.1}'

	for item in root.iterfind(".//{namespace}location".format(namespace = namespace)):
		if location in item[0].text:
			weather = item.find(".//{namespace}parameterName".format(namespace = namespace))
			return item[0].text + weather.text
	return "Can't find " + location

@csrf_exempt
def callback(request):
	if request.method == 'POST':
		signature = request.META['HTTP_X_LINE_SIGNATURE']
		body = request.body.decode('utf-8')
		location_list = ["臺北", "新北", "桃園", "臺中", "臺南", "高雄", "基隆",\
						 "新竹", "苗栗", "彰化", "南投", "雲林", "嘉義", "屏東",\
						"宜蘭", "花蓮", "台東", "澎湖", "金門", "連江"]

		try:
			events = parser.parse(body, signature)
		except InvalidSignatureError:
			return HttpResponseForbidden()
		except LineBotApiError:
			return HttpResponseBadRequest()

		for event in events:
			if isinstance(event, MessageEvent):
				if isinstance(event.message, TextMessage):
					if "天氣" in event.message.text:
						output = get_weather("臺南")
						for location in location_list:
							if location in event.message.text:
								if location == "新竹":
									if "新竹縣" in event.message.text:
										output = get_weather("新竹縣")
									else:
										output = get_weather("新竹市")
								elif location == "嘉義":
									if "嘉義縣" in event.message.text:
										output = get_weather("嘉義縣")
									else:
										output = get_weather("嘉義市")
								else:
									output = get_weather(location)
								break;
					else:
						output = event.message.text

					line_bot_api.reply_message(
						event.reply_token,
						TextSendMessage(text = output)
					)

		return HttpResponse()
	else:
		return HttpResponseBadRequest()
