import os
import requests
import time
import socket
import re
import uuid

from config import loadConfig
from datetime import datetime
from open import isRun
from opensign import OpenSign
from opensign.canvas import OpenSignCanvas
from trains import loadDeparturesForStation
from PIL import ImageFont, Image, ImageDraw


maxLineLength = 25

def formatTime(timeString):
    # Format as 00:00
    return f"{timeString}".rjust(5, "0")


def formatCurrentTime():
    rawTime = datetime.now().time()
    hour, minute, _ = str(rawTime).split(':')
    return formatTime(f"{hour}:{minute}")


def loadData(apiConfig, journeyConfig, config):
    runHours = []
    if config['hoursPattern'].match(apiConfig['operatingHours']):
        runHours = [int(x) for x in apiConfig['operatingHours'].split('-')]

    if len(runHours) == 2 and isRun(runHours[0], runHours[1]) is False:
        return False, False, journeyConfig['outOfHoursName']

    # set rows to 10 (max allowed) to get as many departure as poss
    rows = "10"

    try:
        departures, stationName = loadDeparturesForStation(
            journeyConfig, apiConfig["apiKey"], rows)

        if departures is None:
            return False, False, stationName

        firstDepartureDestinations = departures[0]["calling_at_list"]
        return departures, firstDepartureDestinations, stationName
    except requests.RequestException as err:
        print("Error: Failed to fetch data from OpenLDBWS")
        print(err.__context__)
        return False, False, journeyConfig['outOfHoursName']


# Board is 25.5 chars wide at this font size.
def buildDepartureLine(destinationName, aimedDepartureTime, expectedDepartureTime):
    delayed = expectedDepartureTime != "On time"
    destinationNameMaxLength = 9 if delayed else 19

    destinationNameTruncated = destinationName[:destinationNameMaxLength]
    destinationNamePadded = destinationNameTruncated.rjust(destinationNameMaxLength, " ")

    # Format as 00:00
    aimedDepartureTimePadded = formatTime(aimedDepartureTime)
    expectedDepartureTimePadded = formatTime(expectedDepartureTime) 

    if delayed:
        return f"{aimedDepartureTimePadded} {destinationNamePadded} Exp {expectedDepartureTimePadded}"
    
    return f"{aimedDepartureTimePadded} {destinationNamePadded}"


def buildText(departureData):
    if len(departureData) == 0:
        return "No departure data"

    departureList = departureData[0]
    filteredDepartureList = []
    filterToStations = ("Blackfriars", "London Bridge")
    for departure in departureList:
        for station in filterToStations:
            if station in departure["calling_at_list"]:
                filteredDepartureList.append(departure)
                break

    firstDepartureLine = ""
    if len(filteredDepartureList) > 0:
        firstDeparture = filteredDepartureList[0]
        firstDepartureLine = buildDepartureLine(
            firstDeparture["destination_name"], 
            firstDeparture["aimed_departure_time"], 
            firstDeparture["expected_departure_time"])

    secondDepartureLine = ""
    if len(filteredDepartureList) > 1:
        secondDeparture = filteredDepartureList[1]
        secondDepartureLine = buildDepartureLine(
            secondDeparture["destination_name"], 
            secondDeparture["aimed_departure_time"], 
            secondDeparture["expected_departure_time"])

    currentTime = formatCurrentTime().center(maxLineLength)

    return f"{firstDepartureLine}\n{secondDepartureLine}\n{currentTime}"


def renderSign(departureData, sign):
    message = OpenSignCanvas()
    message.opacity = .5
    message.add_font("monospace", "./fonts/VeraMono.ttf", 9)
    message.add_text(buildText(data), color=(252, 177, 0))
    sign.show(message)


try:
    config = loadConfig()
    sign = OpenSign(rows=32, columns=64, chain=2, gpio_mapping='adafruit-hat', slowdown_gpio=4)
    while True:
        data = loadData(config["api"], config["journey"], config)
        renderSign(data, sign)
        time.sleep(15)



except KeyboardInterrupt:
    pass
except ValueError as err:
    print(f"Error: {err}")
