#!/bin/bash

# Gets the server ip address and the configuration file as command line parameters

# get directory of script
DIR="$( cd "$( dirname "$0" )" && pwd )"

# assuming a local guacmole version is located properly
LOCAL_GUACAMOLE="$DIR/../../../guacamole"
LOCAL_AVANGO="$DIR/../../../avango"

# if not, this path will be used
GUACAMOLE=/opt/guacamole/master
AVANGO=/opt/avango/master

# third party libs
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/boost/current/lib:/opt/openscenegraph/3.0.1/lib64/:/opt/zmq/current/lib

# schism
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/schism/current/lib/linux_x86

# avango
export LD_LIBRARY_PATH="$LOCAL_AVANGO/lib":$AVANGO/lib:$LD_LIBRARY_PATH
export PYTHONPATH="$LOCAL_AVANGO/lib/python2.7":"$LOCAL_AVANGO/examples":$AVANGO/lib/python2.7:$AVANGO/examples:$PYTHONPATH

# guacamole
export LD_LIBRARY_PATH="$LOCAL_GUACAMOLE/lib":$GUACAMOLE/lib:$LD_LIBRARY_PATH



# parse configuration file for hostnames
cd "$DIR"
HOSTS=$(grep '<hostname' "$2" | cut -f2 -d ">" | cut -f1 -d "<")
OWNHOST=$(hostname)
HOSTARRAY=($HOSTS)

# launch a client daemon if the client is not the server
OWNIP=$(hostname -I)
OWNIP=$(echo $OWNIP | tr -d ' ')

if [ "$OWNIP" != "$1" ]; then
	python ./lib-client/ClientDaemon.py > /dev/null &
fi

# determine platform ids for which this host will be responsible for
# launch a client for each platform
cnt=0
for host in "${HOSTARRAY[@]}"; do
	if [ "${HOSTARRAY[$cnt]}" == "$OWNHOST" ]; then
	  #start mumble client (PositionalAudioLink)
	  export DISPLAY=:0.0
	  mumble -m "mumble://${HOSTARRAY[$cnt]}@$1/?version=1.2.0" &&
	  echo "mumble://${HOSTARRAY[$cnt]}@$1/?version=1.2.0"

      cd "$DIR" && python ./lib-client/main.py $1 $cnt $2 > client_log$cnt
	fi
	cnt=$[$cnt+1]
done
