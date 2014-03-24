#!/bin/bash

# Gets the configuration file as first command line parameter

#murmur path
MURMUR_PATH="./murmur-static_x86-1.2.5-245-g221a5d7"

# kill running python apps
./stop-all.sh $1

# get IP of server pc
IP=$(hostname -I)

# get directory of script
DIR="$( cd "$( dirname "$0" )" && pwd )"

# get all hosts to run a client from configuration file
HOSTS=$(grep '<hostname' "$1" | cut -f2 -d ">" | cut -f1 -d "<")

# remove double hostnames such that start-clients.sh is just
# called once per host
# the script will then realize multiple clients if applicable
# remove new line characters and use spaces instead
HOSTS="$(echo "$HOSTS"| sort | uniq | tr "\n" " ")"

#start murmur (PositionalAudioLink Server)
cd $MURMUR_PATH;
./murmur.x86 -ini murmur.ini &
cd $DIR;
#$MURMUR_PATH/murmur.x86 &

# iterate over hosts and start clients
for host in $HOSTS; do
  ssh $host "$DIR"/start-clients.sh $IP $1 &
  sleep 0.2
done

sleep 1

# start server process
./start-server.sh $1 &
