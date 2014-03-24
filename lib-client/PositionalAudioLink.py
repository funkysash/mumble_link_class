#!/usr/bin/python

# import guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed

# import python libraries
import lib.posix_ipc as pos #shared memory handling
import os #get uid
import mmap #shared memory access

from ctypes import *
from _multiprocessing import address_of_buffer


#Globals
SHORTNAME = u'PositionalAudioLink'
DESCRIPTION = u'This is a Link between avango.gua and the Mumble Link plugin'


class ShmError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class LinkedMem(Structure):
  _fields_ = [("uiVersion", c_uint32), #1 or 2; 1 ignores camera, identity and context
              ("uiTick", c_uint32),  #counter to check for updated information
              #
              ("fAvatarPosition", c_float * 3),
              ("fAvatarFront", c_float * 3),
              ("fAvatarTop", c_float * 3),
              ("name", c_wchar * 256), #name of plugin
              ("fCameraPosition", c_float * 3),
              ("fCameraFront", c_float * 3),
              ("fCameraTop", c_float * 3),
              ("identity", c_wchar * 256), #player identity must be unique
              #
              ("context_len", c_uint32), 
              #
              ("context", c_ubyte * 256), #player context must be the same for positional audio
              ("description", c_wchar * 2048)] #plugin description; usage unknown


class PositionalAudioLink(avango.script.Script):
  
  _map = None
  _lm = LinkedMem() #shared memory between plugin and class


  # constructor
  def __init__(self):
    self.super(PositionalAudioLink).__init__()

  # my constructor
  # @param Identity unique User identifier
  # @param Context shared context name - must be the same for all clients recieving positional audio
  # @param Graph Scenegraph containing Avatar (and Camera)
  # @param AvatarName Name of Client's avatar/head transformation node
  # @param CameraName Name of Client's camera transformation node - same as head transformation in most cases
  def my_constructor(self, Identity, Context, Graph, AvatarName, CameraName):
    self._Identity = Identity
    self._Context = Context

    self._Graph = Graph
    self._AvatarName = AvatarName
    self._CameraName = CameraName


    #open shared memory
    _name = "/MumbleLink." + str(os.getuid()) #name of shared memory
    #TODO: next line crashes if mumble isn't running. Maybe add Error output
    try:
      _mem = pos.SharedMemory(_name, flags=0, size=sizeof(LinkedMem))   #flag 0 means access
      print _mem.name
      self._map = mmap.mmap(_mem.fd, _mem.size)
      _mem.close_fd()
      addr, size = address_of_buffer(self._map)
      assert size == sizeof(LinkedMem)
    
    except:
      #print "Error while opening shared memory. Propably Mumble is not running !"
      raise ShmError('Error while opening shared memory. Propably Mumble is not running !')

    self._lm = LinkedMem.from_address(addr)
    self._lm.uiTick = 1 #start with a number other than 0 so the first updated isn't skipped'''
    
    #init trigger callback
    #relying on field has changed could lead to mumble assuming the application died
    self.frame_trigger = avango.script.nodes.Update(Callback = self.update, Active = True)
  
  def update(self):
    
    self._lm.uiTick = self._lm.uiTick + 1 #increase tick with every update
    self._lm.name = SHORTNAME
    self._lm.description = DESCRIPTION
    self._lm.uiVersion =  c_uint32(2);


    if self._Graph[self._AvatarName] and self._Graph[self._CameraName]:


      AvatarTransformation = (self._Graph[self._AvatarName]).WorldTransform

      CameraTransformation = self._Graph[self._CameraName].WorldTransform


      # Matrix Decomposition
      # Positions
      avatar_pos = AvatarTransformation.value.get_translate()

      camera_pos = CameraTransformation.value.get_translate()


      # Avatar Rotation
      avatar_quat = AvatarTransformation.value.get_rotate_scale_corrected()
      avatar_rot = avango.gua.make_rot_mat(avatar_quat.get_angle(),avatar_quat.get_axis())

      front = avango.gua.Vec3(0,0,-1)
      up = avango.gua.Vec3(0,1,0)

      avatar_front = avatar_rot * front
      avatar_up = avatar_rot * up
      #avatar_up.normalize()


      #Camera Rotation
      camera_quat = CameraTransformation.value.get_rotate_scale_corrected()
      camera_rot = avango.gua.make_rot_mat(camera_quat.get_angle(),camera_quat.get_axis())

      camera_front = camera_rot * front
      camera_up = camera_rot * up
      #camera_up.normalize()





      #Left handed coordinate system.
      #X positive towards "right".
      #Y positive towards "up".
      #Z positive towards "front".
      #1 unit = 1 meter

      # z inverted for mumble coordinate system

      #Unit vector pointing out of the avatars eyes (here Front looks into scene).
      self._lm.fAvatarFront[0] = c_float(avatar_front[0]);
      self._lm.fAvatarFront[1] = c_float(avatar_front[1]);
      self._lm.fAvatarFront[2] = c_float(-avatar_front[2]);


      #Unit vector pointing out of the top of the avatars head (here Top looks straight up).
      self._lm.fAvatarTop[0] = c_float(avatar_up[0]);
      self._lm.fAvatarTop[1] = c_float(avatar_up[1]);
      self._lm.fAvatarTop[2] = c_float(-avatar_up[2]);


      #Position of the avatar
      self._lm.fAvatarPosition[0] = c_float(avatar_pos[0]);
      self._lm.fAvatarPosition[1] = c_float(avatar_pos[1]);
      self._lm.fAvatarPosition[2] = c_float(-avatar_pos[2]);


      #Same as avatar but for the camera.
      self._lm.fCameraPosition[0] = c_float(camera_pos[0]);
      self._lm.fCameraPosition[1] = c_float(camera_pos[1]);
      self._lm.fCameraPosition[2] = c_float(-camera_pos[2]);

      self._lm.fCameraFront[0] = c_float(camera_front[0]);
      self._lm.fCameraFront[1] = c_float(camera_front[1]);
      self._lm.fCameraFront[2] = c_float(-camera_front[2]);

      self._lm.fCameraTop[0] = c_float(camera_up[0]);
      self._lm.fCameraTop[1] = c_float(camera_up[1]);
      self._lm.fCameraTop[2] = c_float(-camera_up[2]);

      #Identifier which uniquely identifies a certain player in a context (e.g. the ingame Name).
      self._lm.identity = self._Identity

      #Context should be equal for players which should be able to hear each other positional
      self._lm.context = (c_ubyte * 256)(*[c_ubyte(ord(c)) for c in self._Context[:len(self._Context)]])
      self._lm.context_len = len(self._Context);

  def __del__(self):
    if self._map:
      self._map.close()
