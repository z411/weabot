# coding=utf-8
import tenjin
import random
import re
from tenjin.helpers import * # Used when templating

from settings import Settings
from database import *

def renderTemplate(template, template_values={}, mobile=False, noindex=False):
  """
  Run Tenjin on the supplied template name, with the extra values
  template_values (if supplied)
  """
  values = {
    "title": Settings.NAME,
    "board": None,
    "board_name": None,
    "board_long": None,
    "is_page": "false",
    "noindex": None,
    "replythread": 0,
    "home_url": Settings.HOME_URL,
    "boards_url": Settings.BOARDS_URL,
    "images_url": Settings.IMAGES_URL,
    "static_url": Settings.STATIC_URL,
    "cgi_url": Settings.CGI_URL,
    "banner_url": None,
    "banner_width": None,
    "banner_height": None,
    "disable_name": None,
    "disable_subject": None,
    "styles": Settings.STYLES,
    "styles_default": Settings.STYLES_DEFAULT,
    "txt_styles": Settings.TXT_STYLES,
    "txt_styles_default": Settings.TXT_STYLES_DEFAULT,
    "page_navigator": "",
    "modbrowse": Settings._.MODBROWSE,
    "reports_enable": Settings.REPORTS_ENABLE,
    "force_css": ""
  }
  
  engine = tenjin.Engine(pp=[tenjin.TrimPreprocessor(True)])
  board = Settings._.BOARD
  
  #if board:
  if template in ["board.html", "threadlist.html", "catalog.html", "kako.html", "paint.html"] or template[0:3] == "txt": 
    # TODO HACK
    if board['dir'] == 'world' and not mobile and (template == 'txt_board.html' or template == 'txt_thread.html'):
      template = template[:-4] + 'en.html'
    elif board['dir'] == '2d' and template == 'board.html' and not mobile:
      template = template[:-4] + 'jp.html'

    try:
      banners = Settings.banners[board['dir']]
      if banners:
        banner_width = Settings.banners[board['dir']]
        banner_height = Settings.banners[board['dir']]
    except KeyError:
      banners = Settings.banners['default']
      banner_width = Settings.banners['default']
      banner_height = Settings.banners['default']

    values.update({
      "board": board["dir"],
      "board_name": board["name"],
      "board_long": board["longname"],
      "board_type": board["board_type"],
      "oek_finish": 0,
      "disable_name": (board["disable_name"] == '1'),
      "disable_subject": (board["disable_subject"] == '1'),
      "default_subject": board["subject"],
      "postarea_desc": board["postarea_desc"],
      "postarea_extra": board["postarea_extra"],
      "allow_images": (board["allow_images"] == '1'),
      "allow_image_replies": (board["allow_image_replies"] == '1'),
      "allow_noimage": (board["allow_noimage"] == '1'),
      "allow_spoilers": (board["allow_spoilers"] == '1'),
      "allow_oekaki": (board["allow_oekaki"] == '1'),
      "archive": (board["archive"] == '1'),
      "force_css": board["force_css"],
      "noindex": (board["secret"] == '1'),
      "useid": board["useid"],
      "maxsize": board["maxsize"],
      "maxage": board["maxage"],
      "maxdimensions": board["thumb_px"],
      "supported_filetypes": board["filetypes_ext"],
      "prevrange": '',
      "nextrange": '',
    })
  else:
    banners = Settings.banners['default']
    banner_width = Settings.banners['default']
    banner_height = Settings.banners['default']
  
  if Settings.ENABLE_BANNERS:
    if len(banners) > 1:
      random_number = random.randrange(0, len(banners))
      BANNER_URL = Settings.banners_folder + banners[random_number][0]
      BANNER_WIDTH = banners[random_number][1]
      BANNER_HEIGHT = banners[random_number][2]
    else:
      BANNER_URL = Settings.banners_folder + banners[0][0]
      BANNER_WIDTH = banners[0][1]
      BANNER_HEIGHT = banners[0][2]
    
    values.update({"banner_url": BANNER_URL, "banner_width": BANNER_WIDTH, "banner_height": BANNER_HEIGHT})
  
  values.update(template_values)

  if mobile:
    template_folder = "templates/mobile/"
  else:
    template_folder = "templates/"
  
  return engine.render(template_folder + template, values)