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
  content_type, width, height, size, extra = getImageInfo(data)
  
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
  
  # remove EXIF data if necessary for privacy
  if content_type == 'image/jpeg':
    data = removeExifData(data)
  
  # write file
  f = open(file_path, "wb")
  try:
    f.write(data)
  finally:
    f.close()
  
  # set maximum dimensions
  maxsize = int(board['thumb_px'])
  
  post["file"] = file_name
  post["image_width"] = width
  post["image_height"] = height
  
  # Do we need to thumbnail it?
  if not used_filetype['image']:
    # make thumbnail
    file_thumb_width, file_thumb_height = getThumbDimensions(width, height, maxsize)
    
    if used_filetype['ffmpeg_thumb'] == '1':
      # use ffmpeg to make thumbnail
      logTime("Generating thumbnail")
      
      if used_filetype['mime'][:5] == 'video':
        #duration_half = str(int(extra['duration'] / 2))
        retcode = subprocess.call([
          './ffmpeg', '-strict', '-2', '-ss', '0', '-i', file_path,
          '-v', 'quiet', '-an', '-vframes', '1', '-f', 'mjpeg', '-vf', 'scale=%d:%d' % (file_thumb_width, file_thumb_height),
          '-threads', '1', file_thumb_path])
        if spoiler or board['dir'] == 'polka':
          args = [Settings.CONVERT_PATH, file_thumb_path, "-limit", "thread", "1", "-background", "white", "-flatten", "-resize",  "%dx%d" % (file_thumb_width, file_thumb_height), "-blur", "0x12", "-gravity", "center", "-fill", "rgba(0,0,0, .6)", "-draw", "rectangle 0,%d,%d,%d" % ((file_thumb_height/2)-10, file_thumb_width, (file_thumb_height/2)+7), "-fill", "white", "-annotate", "0", "Alerta de spoiler", "-quality", str(Settings.THUMB_QUALITY), file_thumb_path]
          retcode = subprocess.call(args)
      elif used_filetype['mime'][:5] == 'audio':
        # we do an exception and use png for audio waveform thumbnails since they
        # 1. are smaller 2. allow for transparency
        file_thumb_name = file_thumb_name[:-3] + "png"
        file_thumb_path = file_thumb_path[:-3] + "png"
        file_mobile_path = file_mobile_path[:-3] + "png"
        file_cat_path = file_cat_path[:-3] + "png"
        
        if int(board['thumb_px']) > 149:
          file_thumb_width = board['thumb_px']
          file_thumb_height = float(int(board['thumb_px'])/2)
        else:
          file_thumb_width = 150
          file_thumb_height = 75

        retcode = subprocess.call([
          './ffmpeg', '-t', '300', '-i', file_path,
          '-filter_complex', 'showwavespic=s=%dx%d:split_channels=1' % (int(file_thumb_width), int(file_thumb_height)),
          '-frames:v', '1', '-threads', '1', file_thumb_path])
#       elif used_filetype['mime'] == 'application/x-shockwave-flash' or used_filetype['mime'] == 'mime/x-shockwave-flash':
#         retcode = subprocess.call([
#           './ffmpeg', '-i', file_path, '-vcodec', 'mjpeg', '-vframes', '1', '-an', '-f', 'rawvideo',
#           '-vf', 'scale=%d:%d' % (file_thumb_width, file_thumb_height), '-threads', '1', file_thumb_path])

      if retcode != 0:
        os.remove(file_path)
        raise UserError, _("Thumbnail creation failure.") + ' ('+str(retcode)+')'
    else:
      # use imagemagick to make thumbnail
      args = [Settings.CONVERT_PATH, file_path, "-limit", "thread", "1", "-background", "white", "-flatten", "-resize",  "%dx%d" % (file_thumb_width, file_thumb_height)]
      if spoiler:
        args += ["-blur", "0x12", "-gravity", "center", "-fill", "rgba(0,0,0, .6)", "-draw", "rectangle 0,%d,%d,%d" % ((file_thumb_height/2)-10, file_thumb_width, (file_thumb_height/2)+7), "-fill", "white", "-annotate", "0", "Alerta de spoiler"]
      args += ["-quality", str(Settings.THUMB_QUALITY), file_thumb_path]

      # generate thumbnails
      logTime("Generating thumbnail")
      retcode = subprocess.call(args)
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
    subprocess.call([Settings.CONVERT_PATH, file_thumb_path, "-limit" , "thread", "1", "-resize",  "100x100", "-quality", "75", file_mobile_path])
    if not post["parentid"]:
      subprocess.call([Settings.CONVERT_PATH, file_thumb_path, "-limit" , "thread", "1", "-resize",  "150x150", "-quality", "60", file_cat_path])
    
    post["thumb"] = file_thumb_name
    post["thumb_width"] = file_thumb_width
    post["thumb_height"] = file_thumb_height
  else:
    # Don't thumbnail and use mime image
    post["thumb"] = used_filetype['image']
    if board["board_type"] == '1':
      post["thumb_width"] = '55'
      post["thumb_height"] = '75'
    else:
      post["thumb_width"] = '90'
      post["thumb_height"] = '122'
  
  # calculate size (bytes)
  post["file_size"] = len(data)
  
  # add additional metadata, if any
  post["message"] += extraInfo(content_type, file_name, file_path)
  
  # file md5
  post["file_hex"] = getMD5(data)

  return post

def extraInfo(mime, file_name, file_path):
  board = Settings._.BOARD
  
  if mime in ['audio/ogg', 'audio/opus', 'audio/mpeg', 'video/webm', 'application/x-shockwave-flash']:
    info = ffprobe_f(file_path)
    extra = {}
    credit_str = ""
    
    if mime == 'video/webm':
      for s in info['streams']:
        if 'width' in s:
          stream = s
    else:
      stream = info['streams'][0]
    
    extra['codec'] = stream.get('codec_name', '').encode('utf-8')
    format = info['format']
    
    if 'bit_rate' in format:
      extra['codec'] += ' ~%d kbps' % int(int(format['bit_rate']) / 1000)
    if 'tags' in format:
      extra['title'] = format['tags'].get('TITLE', format['tags'].get('title', '')).encode('utf-8')
      extra['artist'] = format['tags'].get('ARTIST', format['tags'].get('artist', '')).encode('utf-8')
      if extra['title'] or extra['artist']:
        credit_str = ' - '.join((extra['artist'], extra['title'])) + ' '
    if 'tags' in stream:
      extra['title'] = stream['tags'].get('TITLE', '').encode('utf-8')
      extra['artist'] = stream['tags'].get('ARTIST', '').encode('utf-8')
      if extra['title'] or extra['artist']:
        credit_str = ' - '.join((extra['artist'], extra['title'])) + ' '
    
    return '<hr /><small>%s(%s)</small>' % (credit_str, extra['codec'])
    
  elif mime in ['audio/mod', 'audio/xm', 'audio/s3m']:
    ext = mime.split('/')[1].upper()
    url = '/cgi/play/%s/%s' % (board['dir'], file_name)
    return '<hr /><small>Módulo tracker (%s) [<a href="%s" target="_blank">Clic para escuchar</a>]</small>' % (ext, url)
    
  return ''
    
def getImageInfo(data):
  data = str(data)
  size = len(data)
  height = -1
  width = -1
  extra = {}
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
    content_type = "video/webm"
    info = ffprobe(data)
    
    for stream in info['streams']:
      if 'width' in stream:
        width = stream['width']
        height = stream['height']
        break
    
    extra['duration'] = float(info['format']['duration'])
  
  # handle Shockwave Flash
  elif (size >= 3) and data[:3] in ["CWS", "FWS"]:
    content_type = "application/x-shockwave-flash"

  # handle ogg formats (vorbis/opus)
  elif (size >= 64) and data[:4] == "OggS":
    if data[28:35] == "\x01vorbis":
      content_type = "audio/ogg"
    elif data[28:36] == "OpusHead":
      content_type = "audio/opus"
      
  # handle MP3
  elif (size >= 64) and (data[:3] == "ID3" or data[:3] == "\xFF\xFB"):
    content_type = "audio/mpeg"
  
  # handle MOD
  elif (size >= 64) and data[1080:1084] == "M.K.":
    content_type = "audio/mod"
  
  # handle XM
  elif (size >= 64) and data.startswith("Extended Module:"):
    content_type = "audio/xm"
    
  # handle S3M
  elif (size >= 64) and data[25:32] == "\x00\x00\x00\x1A\x10\x00\x00":
    content_type = "audio/s3m"
  
  return content_type, width, height, size, extra

def ffprobe(data):
  import json
  p = subprocess.Popen(['./ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', '-'],
            stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
  
  out = p.communicate(input=data)[0]
  return json.loads(out)
  
def ffprobe_f(filename):
  import json
  
  p = subprocess.Popen(['./ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filename],
            stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
  
  out = p.communicate()[0]
  return json.loads(out)

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

def getJpegSegments(data):
  if data[0:2] != b"\xff\xd8":
    raise UserError("Given data isn't JPEG.")

  head = 2
  segments = [b"\xff\xd8"]
  while 1:
    if data[head: head + 2] == b"\xff\xda":
        yield data[head:]
        break
    else:
        length = struct.unpack(">H", data[head + 2: head + 4])[0]
        endPoint = head + length + 2
        seg = data[head: endPoint]
        yield seg
        head = endPoint

    if (head >= len(data)):
        raise UserDataError("Wrong JPEG data.")
  
def removeExifData(src_data):
  exif = None
  
  for seg in getJpegSegments(src_data):
    if seg[0:2] == b"\xff\xe1" and seg[4:10] == b"Exif\x00\x00":
      exif = seg
      break
  
  if exif:
    return src_data.replace(exif, b"")
  else:
    return src_data