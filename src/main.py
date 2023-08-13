import os
import time

import requests
import time

from datetime import datetime
from PIL import ImageFont, Image, ImageDraw

from trains import loadDeparturesForStation
from config import loadConfig
from open import isRun

from opensign import OpenSign
from opensign.canvas import OpenSignCanvas


import socket, re, uuid


def formatTime(timeString):
    # Format as 00:00
    return f"{hour}:{minute}".ljust(5, "0")


def formatCurrentTime(draw, width, *_):
    rawTime = datetime.now().time()
    hour, minute = str(rawTime).split('.')[0].split(':')
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


def buildDepartureLine(destinationName, aimedDepartureTime, expectedDepartureTime):
    # TODO: Use a monospace font so this always lines up.
    lineLength = 30

    destinationNameMaxLength = 14
    destinationNameTruncated = destinationName[:destinationNameMaxLength]
    destinationNamePadded = destinationNameTruncated.rjust(destinationNameMaxLength, " ")
    print(destinationNamePadded)

    # Format as 00:00
    departureTimeMaxLength = 5
    aimedDepartureTimePadded = formatTime(aimedDepartureTime)
    expectedDepartureTimePadded = formatTime(expectedDepartureTime) 
    print(aimedDepartureTimePadded)
    print(expectedDepartureTimePadded)

    print(f"{aimedDepartureTimePadded destinationNamePadded Exp expectedDepartureTimePadded}")
    return f"{aimedDepartureTimePadded destinationNamePadded Exp expectedDepartureTimePadded}"


def buildText(departureData):
    if(len(departureData) == 0)
        return "No departure data"

    departureList = departureData[0]
    filteredDepartureList = []
    filterToStations = ("Blackfriars", "London Bridge")
    for departure in departureList:
        for station in filterToStations:
            if departure["calling_at_list"] contains station:
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
    if len(filteredDepartureList > 1):
        secondDeparture = filteredDepartureList[1]
        secondDepartureLine = buildDepartureLine(
            secondDeparture["destination_name"], 
            secondDeparture["aimed_departure_time"], 
            secondDeparture["expected_departure_time"])

    currentTime = formatCurrentTime

    return f"{firstDepartureLine}\n{secondDepartureLine}\n{currentTime}"


def renderSign(departureData, sign):
    message = OpenSignCanvas()
    message.add_font("dejavu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    message.add_text(buildText(data), color=(254,218,5))
    message.set_shadow()
    sign.show(message)


try:
    print('Starting Train Departure Display v')
    config = loadConfig()
    sign = OpenSign(rows=32, columns=64, chain=2, gpio_mapping='adafruit-hat', slowdown_gpio=4)
    while true:
        data = loadData(config["api"], config["journey"], config)
        print(data)
        renderSign(data, sign)
        time.sleep(60)



except KeyboardInterrupt:
    pass
except ValueError as err:
    print(f"Error: {err}")
