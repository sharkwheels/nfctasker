#!/usr/bin/python
from __future__ import print_function

import calendar
import datetime
import json
import logging
import os
import random
import requests
import RPi.GPIO as GPIO
import SimpleMFRC522
import time

from random import choice
from datetime import date
from threading import Thread
from time import sleep

from data import holidays, verbs, objects, dates, locations, tasks, absurds, nicknames

from Adafruit_Thermal import *


from flask import Flask, render_template, redirect
from flask_ask import Ask, request, context, session, question, statement, convert_errors

printer = Adafruit_Thermal("/dev/ttyUSB0", 9600, timeout=5)
reader = SimpleMFRC522.SimpleMFRC522()

app = Flask(__name__)
app.secret_key = "19eudhuw9t7rhbalweihfg87"

ask = Ask(app, "/")

log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.DEBUG)
logging.getLogger("flask_ask").setLevel(logging.DEBUG)

#arrayOfcrap = ['oranges','horses','pickles','cats','pliers',"moon"]

speakResp = {"currentResp": "default"}

## random seed this thing
random.seed(datetime.datetime.now())

### HELPER FUNCTION #####################


def timeStamp():
	today = datetime.date.today()					
	day_name = calendar.day_name[today.weekday()]	# thursday
	month = calendar.month_name[today.month]		# october
	day = today.day 								# 5
	t = time.strftime("%-I:%M %p")					# 4:10 PM
	current_time = "{0} {1} {2}th, {3}".format(day_name,month,day,t)
	return current_time

def findHoliday():
	""" Get the current date, and then do a serch through the dict for a holiday that matches it """
	today = datetime.date.today()
	month = calendar.month_name[today.month]
	day = today.day 
	current_time = "{0} {1}".format(month,day)
	print(current_time)

	## append holidays to hols
	hols = []
	for d in holidays:
		if d["day"] == current_time:
			h = d['holiday']
			hols.append(h)
	
	## sometimes there are two entries for a day
	if len(hols) > 0:
		boop = random.choice(hols)
		return boop
	else:
		return "Royal Spaggetti Day"

def makeFortune():
	"""
	Hello [NICKNAMES], happy [HOLIDAY]
	You will [VERB] [OBJECT] [DATE],
	I foresee you will [VERB] [OBJECT]. 
	Watch out for [OBJECT][LOCATION]. 
	Your task is [TASK].

	This is passing the fortune to a dict for speaking, and passing the fortune to the printFortune function for printing.
	"""
	## greeting
	holiday = findHoliday()
	nick = random.choice(nicknames)

	## first scentance
	verb1 = random.choice(verbs)
	object1 = random.choice(objects)
	date = random.choice(dates)

	## second scentence
	verb2 = random.choice(verbs)
	object2 = random.choice(objects)

	## third scentence
	object3 = random.choice(objects)
	location = random.choice(locations)

	## fourth scentance
	task = random.choice(tasks)


	## gonna have to split this up in the JSON because is fucking looooooong
	greeting = "Hello {0}, happy {1}! Your future is as follows:".format(nick,holiday)
	fortunePt1 = "You will {0} {1} {2}.".format(verb1,object1,date)
	foruntePt2 = "I foresee you will {0} {1}.".format(verb2,object2)
	fortunePt3 = "Watch out for {0} {1}.".format(object3,location)
	fortunePt4 = "Your task is: {0}.".format(task)
	
	fortune_list = [greeting,fortunePt1,foruntePt2, fortunePt3,fortunePt4]
	print(fortune_list)

	## pass the fortune as a string to a dict
	speak = "{0} {1} {2} {3} {4}".format(greeting,fortunePt1,foruntePt2, fortunePt3,fortunePt4)
	
	global speakResp
	speakResp.update({'currentResp':speak})

	print("!makeFortune", speakResp)
	
	return fortune_list
	#printFortune(fortune_list)


def printFortune():

	## make the forutne
	fortune = makeFortune()
	ts = timeStamp()
	print(ts,fortune[0],fortune[1],fortune[2],fortune[3],fortune[4])

	## begin printing
	
	printer.setSize('S')
	printer.justify('C')
	printer.println("*****************")
	printer.boldOn()
	printer.println(ts)
	printer.boldOff()
	printer.feed(1)

	printer.setDefault()
	printer.setSize('S')
	printer.justify('L')

	printer.println(fortune[0])
	printer.feed(1)
	printer.println(fortune[1])
	printer.feed(1)
	printer.println(fortune[2])
	printer.feed(1)
	printer.println(fortune[3])
	printer.feed(1)
	printer.println(fortune[4])

	printer.setDefault()
	printer.setSize('S')
	printer.justify('C')
	printer.println("*****************")
	printer.setDefault()
	printer.feed(2)


### APP THINGS #####################

@app.route('/',methods=['GET','POST'])
def index():
	return "hello!"

### ALEXA TTHINGS #####################

@ask.on_session_started
def new_session():
	log.info('new session started')
	log.info(request.locale)
	beep = request.locale
	print(beep)

@ask.launch
def launch():
	### write a thing / testing the nfc ##
	"""
	try:
		item = random.choice(arrayOfcrap)
		reader.write(item)
		print("Written")
		print(item)
		#return statement("writing {}".format(item))
	except Exception as e:
		print(e)
		return statement("couldn't write tag")
	finally:
		GPIO.cleanup()
		
	## read the thing ##
	try:
		id, text = reader.read()
		print(id)
		print(text)
		msgText = "NFC says {}".format(text)

		printer.println("NFC says {}".format(text))
		printer.feed(4)
		printer.sleep()      # Tell printer to sleep
		printer.wake()       # Call wake() before printing again, even if reset
		printer.setDefault() # Restore printer to defaults
		
		return statement(msgText)
	except Exception as e:
		print(e)
		return statement("couldn't read tag")
	finally:
		GPIO.cleanup()
	"""

	## testing the threading
	t = Thread(target=printFortune)
	t.start()

	## test speaking

	#return statement("<speak>{0}<break time='1s' /></speak>".format(to_speak)) ## 3 second break after resp, should extend timeout
	to_say = speakResp['currentResp']
	print(to_say)
	if to_say:
		return statement(to_say)
	else:
		return statement("didn't get the response")



@ask.intent('AMAZON.HelpIntent')
def help():
	help_text = render_template('help')
	return question(help_text).reprompt(help_text)

@ask.intent('AMAZON.StopIntent')
def stop():
	bye_text = render_template('stop')
	return statement(bye_text)

@ask.intent('AMAZON.CancelIntent')
def cancel():
	bye_text = render_template('cancel')
	return statement(bye_text)

@ask.session_ended
def session_ended():
	log.debug("Session Ended")
	print("session ended")
	reset()
	return "{}", 200


@ask.intent('AMAZON.HelpIntent')
def help():
	speech_text = "Looking at things!"
	return question(speech_text).reprompt(speech_text).simple_card('HelloWorld', speech_text)


@ask.session_ended
def session_ended():
	return "{}", 200

if __name__ == '__main__':
	app.config['ASK_VERIFY_REQUESTS'] = False
	app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)