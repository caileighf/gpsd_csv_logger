# gpsd_csv_logger
Logger that generates a csv from streaming gpsd data. Includes systemd unit file for auto starting at boot.

 You must have `gpsd` already installed and set up.
 __gpsd must be configured to stream JSON or the logging script will not work.__

# Using the `systemd` unit file for auto starting the GPS logger

## Location of Data Directory and Filename Formats
All csv data is either stored in the current working directory or, in the "WorkingDirectory" variable if running with `systemd`. 

### `gps` Logger - filenames, formats
The gpsd csv service creates a single file at boot (each time the service is restarted a new file is created). If run directly the filename structure is still the same: 
```
track_20210826T163155Z.nmea
      |   | |  | | | |___________ Timezone. This will depend on the machines timezone
      |   | |  | | |_____________ Second
      |   | |  | |_______________ Minute
      |   | |  |_________________ Hour
      |   | |____________________ Day
      |   |______________________ Month
      |__________________________ Year
```

#### TODO: Find example csv output file (I think I know where some are..)

### Install dependencies and copy files to directory for `systemd`

#### dependencies:

This utility was written for a raspberry pi 4. Maybe more install scripts will show up for different platforms.

Run:
```bash
sudo /home/ubuntu/gpsd_csv_logger/install_RPI4_ubuntu20.04amd64.sh # this will use apt to install the required dependencies
```

#### `systemd`:
_If not using `systemd`, skip this section_

For `systemd` to run this service, this unit file must be placed in the correct directory with the correct permissions. On a raspberry pi 4 running ubuntu 20.04 server (amd64) that means `/etc/systemd/system/`

```bash
sudo cp ~/gpsd_csv_logger/gpsd_csv_logger.service /etc/systemd/system/
```

Make sure all the paths are correct in the config files in this repo and match this unit file being copied.

### gpsd_csv_logger bash script

`~/gpsd_csv_logger/utils/log_gps.sh` is run by the user or a `systemd` unit file. It depends on `gpspipe` and `jq` to create a csv file containing the timestamp, latitude (decimal degrees), longitude (decimal degrees) on each row (for quick plotting in the field).

SUPER useful link for "TPV" time-position-velocity report sentences and their fields: https://gpsd.gitlab.io/gpsd/gpsd_json.html#_tpv

```bash
#!/bin/bash

while true
do
	track_filename=track_$(date +'%Y%m%dT%H%M%S%Z').nmea
	gpspipe -w | grep TPV | grep lat | jq --unbuffered -r '"\(.time),\(.lat),\(.lon)"' > ${track_filename}
done
```

`~/gpsd_csv_logger/utils/log_gps_toa.sh` (untested)
for epoch at time of arrival (system time so no need to correct for leap seconds),time,lat,lon

```bash
#!/bin/bash

while true
do
	track_filename=track_$(date +'%Y%m%dT%H%M%S%Z').nmea
	gpspipe -w | grep TPV | grep lat | jq --unbuffered -r '"\(.time),\(.lat),\(.lon)"' |\
	cat "$(date +'%s')," /dev/stdin > ${track_filename}
done
```

## Starting/stopping GPS logger launched with `systemd` on RPi4 running ubuntu 20.04 server (amd64)

`systemd` manages the `gpsd_csv_logger.service` daemon. The unit file for `gpsd_csv_logger.service` is below:

```bash
[Unit]
Description=GPSDCSV Echogram GPSD CSV Logger

[Service]
Type=simple
Restart=always
RestartSec=2
User=ubuntu

WorkingDirectory=/home/ubuntu/gpsd_csv_logger/data
ExecStart=/home/ubuntu/gpsd_csv_logger/utils/log_gps.sh

[Install]
WantedBy=multi-user.target
```

```bash
# Example systemd commands using systemctl
sudo systemctl start gpsd_csv_logger.service
sudo systemctl stop gpsd_csv_logger.service
sudo systemctl status gpsd_csv_logger.service
sudo systemctl restart gpsd_csv_logger.service
```

To follow the output using `journalctl` run:

`journalctl -f -u gpsd_csv_logger.service`

## Configuring the system to auto atart at boot
Running the following command will set the service to auto start at the next boot (this behavior will persist for future boots but _will not_ start any services during the current boot).
```bash
sudo systemctl enable gpsd_csv_logger.service
```

## Configuring the system for manual start
Running the following command will make sure the service is _not_ started on the next boot (this behavior will persist for future boots but _will not_ stop an actively running service).
```bash
sudo systemctl disable gpsd_csv_logger.service
```