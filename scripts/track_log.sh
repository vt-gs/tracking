#!/bin/bash
#DATETIME=`date -u +%Y%m%d_%H%M%S.%N_UTC`
DATETIME=`date +%Y%m%d`
FILENAME=$DATETIME'_tracking_daemon.log'
echo $FILENAME
cp /var/log/upstart/tracking_daemon.log /mnt/log/eddie/tracking/$FILENAME
