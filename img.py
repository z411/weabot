# coding=utf-8
import struct
import math
#import random
import os
import subprocess
from StringIO import StringIO

from settings import Settings
from database import *
from framework import *

try: # Windows needs stdio set for binary mode.
  import msvcrt
  msvcrt.setmode (0, os.O_BINARY) # stdin  = 0
  msvcrt.setmode (1, os.O_BINARY) # stdout = 1
except ImportError:
  pass

def processImage(post, data, t, originalname, spoiler=False):
  """
  Take all post data from <post>, process uploaded file in <data>, and calculate
  file names using datetime <t>
  Returns updated <post> with file and thumb values
  """
  board = Settings._.BOARD
  
  used_filetype = None
  
  # get image information
  content_type, width, height, size, duration = getImageInfo(data)
  
  # check the size is fine
  if size > int(board["maxsize"])*1024:
    raise UserError, _("File too big. The maximum file size is: %s") % board['maxsize']
  
  # check if file is supported
  for filetype in board['filetypes']:
    if content_type == filetype['mime']:
      used_filetype = filetype
      break
    
  if not used_filetype:
    raise UserError, _("File type not supported.")
  
  # check if file is already posted
  is_duplicate = checkFileDuplicate(data)
  if checkFileDuplicate(data)[0]:
    raise UserError, _("This image has already been posted %s.") % ('<a href="' + Settings.BOARDS_URL + board['dir'] + '/res/' + str(is_duplicate[1]) + '.html#' + str(is_duplicate[2]) + '">' + _("here") + '</a>')
  
  # prepare file names
  if used_filetype['preserve_name'] == '1':
    file_base = os.path.splitext(originalname)[0] # use original filename
  else:
    file_base = '%d' % int(t * 1000) # generate timestamp name
  file_name = file_base + "." + used_filetype['ext']
  file_thumb_name = file_base + "s.jpg"
  
  # prepare paths
  file_path = Settings.IMAGES_DIR + board["dir"] + "/src/" + file_name
  file_thumb_path = Settings.IMAGES_DIR + board["dir"] + "/thumb/" + file_thumb_name
  file_mobile_path = Settings.IMAGES_DIR + board["dir"] + "/mobile/" + file_thumb_name
  file_cat_path = Settings.IMAGES_DIR + board["dir"] + "/cat/" + file_thumb_name
  
  # write file
  f = open(file_path, "wb")
  try:
    f.write(data)
  finally:
    f.close()
  
  # set maximum dimensions
  if post["parentid"] == '0':
    maxsize = Settings.MAX_DIMENSION_FOR_OP_IMAGE
  else:
    maxsize = Settings.MAX_DIMENSION_FOR_REPLY_IMAGE
  
  post["file"] = file_name
  post["image_width"] = width
  post["image_height"] = height
  
  # Do we need to thumbnail it?
  if not used_filetype['image']:
    if spoiler:
      post["thumb"] = 'spoil'
    else:
      # make thumbnail
      file_thumb_width, file_thumb_height = getThumbDimensions(width, height, maxsize)
      
      if used_filetype['ffmpeg_thumb'] == '1':
        # use ffmpeg to make thumbnail
        logTime("Generating thumbnail")
        
        
        if used_filetype['mime'][:5] == 'video':
          duration_half = str(int(duration / 2))
          retcode = subprocess.call([
            './ffmpeg', '-strict', '-2', '-ss', '0', '-i', file_path,
            '-v', 'quiet', '-an', '-vframes', '1', '-f', 'mjpeg', '-vf', 'scale=%d:%d' % (file_thumb_width, file_thumb_height),
            '-threads', '1', file_thumb_path])       
        elif used_filetype['mime'][:5] == 'audio':
          # we do an exception and use png for audio waveform thumbnails since they
          # 1. are smaller
          # 2. allow for transparency
          file_thumb_name = file_thumb_name[:-3] + "png"
          file_thumb_path = file_thumb_path[:-3] + "png"
          file_mobile_path = file_mobile_path[:-3] + "png"
          file_cat_path = file_cat_path[:-3] + "png"
          
          file_thumb_width = 250
          file_thumb_height = 180
          retcode = subprocess.call([
            './ffmpeg', '-i', file_path,
            '-filter_complex', 'showwavespic=s=250x180:split_channels=1', '-frames:v', '1',
            '-threads', '1', file_thumb_path])
        
        if retcode != 0:
          os.remove(file_path)
          raise UserError, _("Thumbnail creation failure.") + ' ('+str(retcode)+')'
      else:
        # use imagemagick to make thumbnail
        # use first frame in gifs
        if used_filetype['ext'] == 'gif':
          file_path += '[0]'
        
        # generate thumbnails
        logTime("Generating thumbnail")
        retcode = subprocess.call([Settings.CONVERT_PATH, file_path, "-limit" , "thread", "1", "-background", "white", "-flatten", "-resize",  "%dx%d" % (file_thumb_width, file_thumb_height), "-quality", str(Settings.THUMB_QUALITY), file_thumb_path])
        if retcode != 0:
          os.remove(file_path)
          raise UserError, _("Thumbnail creation failure.") + ' ('+str(retcode)+')'
      
      # check if thumbnail was truly created
      try:
        open(file_thumb_path)
      except:
        os.remove(file_path)
        raise UserError, _("Thumbnail creation failure.")
        
      # create extra thumbnails (catalog/mobile)
      subprocess.call([Settings.CONVERT_PATH, file_thumb_path, "-limit" , "thread", "1", "-resize",  "100x100", "-quality", "30", file_mobile_path])
      if not post["parentid"]:
        subprocess.call([Settings.CONVERT_PATH, file_thumb_path, "-limit" , "thread", "1", "-resize",  "150x150", "-quality", "50", file_cat_path])
      
      post["thumb"] = file_thumb_name
      post["thumb_width"] = file_thumb_width
      post["thumb_height"] = file_thumb_height
  else:
    # Don't thumbnail and use mime image
    post["thumb"] = used_filetype['image']
  
  post["file_size"] = len(data)
  #if Settings.IMAGE_SIZE_UNIT == "B":
  #  post["file_size_formatted"] = str(post["file_size"]) + " B"
  #else:
  #  post["file_size_formatted"] = str(long(post["file_size"] / 1024)) + " KB"
  
  # if the name changed, put the original one in the stamp
  if used_filetype['preserve_name'] == '0':
    #post["file_size_formatted"] += ', ' + originalname
    post["file_original"] = originalname
  
  # file md5
  post["file_hex"] = getMD5(data)

  return post

def processOekakiImage(post, image, width, height, timetaken):
  """
  Esta rutina esta hecha especialmente para imagenes Oekaki,
  ya que no hay que volver a subirlas.
  """
  board = Settings._.BOARD
  
  file_extension = ".png"
  ani_extension = ".pch"
          
  file_name = image
  file_thumb_name = file_name + "s" + file_extension
  file_name += file_extension
  
  file_path = Settings.IMAGES_DIR + board["dir"] + "/src/" + file_name
  file_ani_path = Settings.IMAGES_DIR + board["dir"] + "/src/" + image + ani_extension
  file_thumb_path = Settings.IMAGES_DIR + board["dir"] + "/thumb/" + file_thumb_name
  file_mobile_path = Settings.IMAGES_DIR + board["dir"] + "/mobile/" + file_thumb_name
  file_cat_path = Settings.IMAGES_DIR + board["dir"] + "/cat/" + file_thumb_name
    
  # Mover el archivo
  try:
    import shutil
    shutil.move(Settings.ROOT_DIR + 'oek_temp/' + image + file_extension, file_path)
  except:
    raise UserError, "Error al mover el archivo temporal."
  
  try:
    shutil.move(Settings.ROOT_DIR + 'oek_temp/' + image + ani_extension, file_ani_path)
    post["animation"] = image
  except:
    # No hay animacion
    post["animation"] = "-1"
  
  post["time_taken"] = elapsed_time(timetaken)
  
  if post["parentid"] == 0:
    maxsize = Settings.MAX_DIMENSION_FOR_OP_IMAGE
  else:
    maxsize = Settings.MAX_DIMENSION_FOR_REPLY_IMAGE
  
  file_thumb_width, file_thumb_height = getThumbDimensions(width, height, maxsize)

  logTime("Generating thumbnail")
  # thumbnail
  os.system("convert %s -resize %dx%d -quality %d %s" % (file_path, file_thumb_width, file_thumb_height, Settings.THUMB_QUALITY, file_thumb_path))
  # mobile thumbnail
  os.system("convert %s -resize 100x100 -quality 30 %s" % (file_thumb_path, file_mobile_path))
  # catalog thumbnail
  if not post["parentid"]:
    os.system("convert %s -resize 50x50 -quality 30 %s" % (file_mobile_path, file_cat_path))
  
  try:
    open(file_thumb_path)
  except:
    raise UserError, _("Thumbnail creation failure.")

  post["file"] = file_name
  post["image_width"] = width
  post["image_height"] = height
  
  post["thumb"] = file_thumb_name
  post["thumb_width"] = file_thumb_width
  post["thumb_height"] = file_thumb_height

  return post
    
def getImageInfo(data):
  data = str(data)
  size = len(data)
  height = -1
  width = -1
  duration = -1
  content_type = ""

  # handle GIFs
  if (size >= 10) and data[:6] in ("GIF87a", "GIF89a"):
    # Check to see if content_type is correct
    content_type = "image/gif"
    w, h = struct.unpack("<HH", data[6:10])
    width = int(w)
    height = int(h)

  # See PNG 2. Edition spec (http://www.w3.org/TR/PNG/)
  # Bytes 0-7 are below, 4-byte chunk length, then 'IHDR'
  # and finally the 4-byte width, height
  elif ((size >= 24) and data.startswith("\211PNG\r\n\032\n")
        and (data[12:16] == "IHDR")):
    content_type = "image/png"
    w, h = struct.unpack(">LL", data[16:24])
    width = int(w)
    height = int(h)

  # Maybe this is for an older PNG version.
  elif (size >= 16) and data.startswith("\211PNG\r\n\032\n"):
    # Check to see if we have the right content type
    content_type = "image/png"
    w, h = struct.unpack(">LL", data[8:16])
    width = int(w)
    height = int(h)

  # handle JPEGs
  elif (size >= 2) and data.startswith("\377\330"):
    content_type = "image/jpeg"
    jpeg = StringIO(data)
    jpeg.read(2)
    b = jpeg.read(1)
    try:
      while (b and ord(b) != 0xDA):
        while (ord(b) != 0xFF): b = jpeg.read
        while (ord(b) == 0xFF): b = jpeg.read(1)
        if (ord(b) >= 0xC0 and ord(b) <= 0xC3):
          jpeg.read(3)
          h, w = struct.unpack(">HH", jpeg.read(4))
          break
        else:
          jpeg.read(int(struct.unpack(">H", jpeg.read(2))[0])-2)
        b = jpeg.read(1)
      width = int(w)
      height = int(h)
    except struct.error:
      pass
    except ValueError:
      pass
  
  # handle WebM
  elif (size >= 4) and data.startswith("\x1A\x45\xDF\xA3"):
    import json
    
    content_type = "video/webm"
    p = subprocess.Popen(['./ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', '-'],
              stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    
    out = p.communicate(input=data)[0]
    info = json.loads(out)
    
    width = info['streams'][0]['width']
    height = info['streams'][0]['height']
    duration = float(info['format']['duration'])
  
  # handle Shockwave Flash
  elif (size >= 3) and data[:3] in ["CWS", "FWS"]:
    content_type = "application/x-shockwave-flash"

  elif (size >= 64) and data[:4] == "OggS":
    if data[28:35] == "\x01vorbis":
      content_type = "audio/ogg"
    elif data[28:36] == "OpusHead":
      content_type = "audio/opus"
    
  return content_type, width, height, size, duration
  

def getThumbDimensions(width, height, maxsize):
  """
  Calculate dimensions to use for a thumbnail with maximum width/height of
  <maxsize>, keeping aspect ratio
  """
  wratio = (float(maxsize) / float(width))
  hratio = (float(maxsize) / float(height))
  
  if (width <= maxsize) and (height <= maxsize):
    return width, height
  else:
    if (wratio * height) < maxsize:
      thumb_height = math.ceil(wratio * height)
      thumb_width = maxsize
    else:
      thumb_width = math.ceil(hratio * width)
      thumb_height = maxsize
  
  return int(thumb_width), int(thumb_height)

def checkFileDuplicate(data):
  """
  Check that the file <data> does not already exist in a live post on the
  current board by calculating its hex and checking it against the database
  """
  board = Settings._.BOARD
  
  file_hex = getMD5(data)
  post = FetchOne("SELECT `id`, `parentid` FROM `posts` WHERE `file_hex` = '%s' AND `boardid` = %s AND IS_DELETED = 0 LIMIT 1" % (file_hex, board['id']))
  if post:
    if int(post["parentid"]) != 0:
      return True, post["parentid"], post["id"]
    else:
      return True, post["id"], post["id"]
  else:
    return False, 0, 0
