#!/usr/bin/python

## @file
# Client application for the distributed viewing setup.

# import guacamole libraries
import avango
import avango.script
import avango.gua
import avango.oculus

# import framework libraries
import ClientConfigFileParser
import ClientMaterialUpdaters

from PositionalAudioLink import PositionalAudioLink

from ClientDesktopUser import *
from ClientOVRUser import *
from ClientPowerWallUser import *

# import python libraries
import sys

# Command line parameters:
# client.py SERVER_IP PLATFORM_ID CONFIG_FILE
# @param SERVER_IP The IP address on which the server process is running.
# @param PLATFORM_ID The platform id for which this client is responsible for.
# @param CONFIG_FILE The filname of the configuration file to parse.

## Main method for the client application.
def start():

  # get the server ip
  server_ip = str(sys.argv[1])

  # get the platform id
  platform_id = str(sys.argv[2])

  # get the configuration filename
  config_file = str(sys.argv[3])

  # get own hostname
  hostname = open('/etc/hostname', 'r').readline()

  print "This client is running on", hostname, "and listens to server", server_ip
  print "It is responsible for platform", platform_id

  # process config file to find out user attributes
  user_list = ClientConfigFileParser.parse(config_file, platform_id)
  print user_list

  # create distribution node
  nettrans = avango.gua.nodes.NetTransform(
                Name = "net",
                # specify role, ip, and port
                #Groupname = "AVCLIENT|127.0.0.1|7432"
                Groupname = "AVCLIENT|{0}|7432".format(server_ip)
                )

  # create a dummy scenegraph to be extended by distribution
  graph = avango.gua.nodes.SceneGraph(Name = "scenegraph")
  graph.Root.value.Children.value = [nettrans]

  # create material updaters as this cannot be distributed
  avango.gua.load_shading_models_from("data/materials")
  avango.gua.load_materials_from("data/materials")

  timer = avango.nodes.TimeSensor()

  water_updater = ClientMaterialUpdaters.TimedMaterialUniformUpdate()
  water_updater.MaterialName.value = "data/materials/Water.gmd"
  water_updater.UniformName.value = "time"
  water_updater.TimeIn.connect_from(timer.Time)


  # create a viewer
  viewer = avango.gua.nodes.Viewer()

  # positional audio
  _first_run = True
  _pos_audio_link = PositionalAudioLink()
  

  # create viewing setups for each user
  for user_attributes in user_list:

    _user = None
    
    # desktop user case
    if user_attributes[0] == "DesktopUser":
      _user = ClientDesktopUser()
      _user.my_constructor(graph, viewer, user_attributes)
 
    # small powerwall user case
    elif user_attributes[0] == "SmallPowerWallUser":
      _user = ClientPowerWallUser()
      _user.my_constructor(graph, viewer, user_attributes, "small")

    # large powerwall user case
    elif user_attributes[0] == "LargePowerWallUser":
      _user = ClientPowerWallUser()
      _user.my_constructor(graph, viewer, user_attributes, "large")

    # ovr user case
    elif user_attributes[0] == "OVRUser":
      _user = ClientOVRUser()
      _user.my_constructor(graph, viewer, user_attributes)

    if _first_run:

        #_head_transform = (_user.SCENEGRAPH["/net/platform_" + str(_user.platform_id) + "/" + _user.node_pretext + "_head_" + str(_user.user_id)]).Transform
        _head_name = "/net/platform_" + str(_user.platform_id) + "/" + _user.node_pretext + "_head_" + str(_user.user_id) 
        _pos_audio_link.my_constructor(str(_user.user_id),"ctx",graph,_head_name,_head_name)
        _first_run = False

  viewer.SceneGraphs.value = [graph]

  # start rendering process
  viewer.run()

if __name__ == '__main__':
  start()
