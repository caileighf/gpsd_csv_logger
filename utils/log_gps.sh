#!/bin/bash

while true
do
	track_filename=track_$(date +'%Y%m%dT%H%M%S%Z').nmea
	gpspipe -w | grep TPV | grep lat | jq --unbuffered -r '"\(.time),\(.lat),\(.lon)"' > ${track_filename}
done