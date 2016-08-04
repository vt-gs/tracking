#!/bin/bash
#DATETIME=`date -u +%Y%m%d_%H%M%S.%N_UTC`
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
#DATETIME=`date +%Y%m%d`
DATE=`date -u --date="5 minutes ago" +%Y%m%d`
DMN_NAME=$DATE'_tracking_vul.log' #upstart daemon
TAR_NAME=$DATE'_tracking_logs'
#echo $FILENAME

#create temp folder 
cd /vtgs/scripts
mkdir $TAR_NAME

#copy upstart daemon log to scripts directory and change name 
cd /var/log/upstart
cp tracking_vul.log /vtgs/scripts/$TAR_NAME/$DMN_NAME

#move all MD01 and VTP logs to scripts folder
cd /vtgs/daemon/tracking/vul/log
mv *.log /vtgs/scripts/$TAR_NAME/

#compress the folder full of logs and ove it to the NAS
cd /vtgs/scripts/
tar -zcpf /mnt/log/tracking/$TAR_NAME'.tar.gz'  *.log
chmod 666 /mnt/log/tracking/$TAR_NAME'.tar.gz'
rm -rf ./$TAR_NAME
