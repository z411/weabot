# coding=utf-8
import tenjin
import random
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
    "is_page": "false",
    "noindex": noindex,
    "replythread": 0,
    "home_url": Settings.HOME_URL,
    "boards_url": Settings.BOARDS_URL,
    "images_url": Settings.IMAGES_URL,
    "static_url": Settings.STATIC_URL,
    "cgi_url": Settings.CGI_URL,
    "banner_url": None,
    "banner_width": Settings.BANNER_WIDTH,
    "banner_height": Settings.BANNER_HEIGHT,
    "anonymous": None,
    "forced_anonymous": None,
    "disable_subject": None,
    "tripcode_character": None,
    "default_style": Settings.DEFAULT_STYLE,
    "maxdimensions": Settings.MAX_DIMENSION_FOR_OP_IMAGE,
    "unique_user_posts": None,
    "page_navigator": "",
    "navbar": Settings.SHOW_NAVBAR,
    "modbrowse": Settings._.MODBROWSE,
    "reports_enable": Settings.REPORTS_ENABLE,
    "force_css": ""
  }
  
  engine = tenjin.Engine()
  
  if template == "board.html" or template == "threadlist.html" or template == "catalog.html" or template == "kako.html" or template[0:3] in ["txt", "swf", "url"]:
    board = Settings._.BOARD
    
    # TODO HACK
    if board['dir'] == '0' and template == 'board.html':
      template = template[:-4] + '0.html'
    elif board['dir'] == 'jp' and (template == 'board.html' or template == 'catalog.html'):
      template = template[:-4] + 'jp.html'
    
    try:
      banners = Settings.banners[board['dir']]
    except KeyError:
      banners = Settings.banners['default']
    
    values.update({
      "board": board["dir"],
      "board_name": board["name"],
      "board_type": board["board_type"],
      "anonymous": board["anonymous"],
      "oek_finish": 0,
      "forced_anonymous": (board["forced_anonymous"] == '1'),
      "disable_subject": (board["disable_subject"] == '1'),
      "tripcode_character": board["tripcode_character"],
      "postarea_extra_html_top": board["postarea_extra_html_top"],
      "postarea_extra_always": (board["postarea_extra_always"] == '1'),
      "postarea_extra_html_bottom": board["postarea_extra_html_bottom"],
      "allow_images": (board["allow_images"] == '1'),
      "allow_image_replies": (board["allow_image_replies"] == '1'),
      "allow_noimage": (board["allow_noimage"] == '1'),
      "allow_spoilers": (board["allow_spoilers"] == '1'),
      "allow_oekaki": (board["allow_oekaki"] == '1'),
      "archive": (board["archive"] == '1'),
      "force_css": board["force_css"],
      "board_locked": (board["locked"] == '1'),
      "useid": board["useid"],
      "maxsize": board["maxsize"],
      "supported_filetypes": board["filetypes_ext"],
      "spoilop_image": Settings.spoilop_filename,
      "spoil_image": Settings.spoil_filename,
      "flash_image": Settings.flash_filename,
      "prevrange": '',
      "nextrange": '',
    })
  else:
    banners = Settings.banners['default']
  
  if Settings.ENABLE_BANNERS:
    random_number = random.randrange(0, len(banners))
    BANNER_URL = Settings.banners_folder + banners[random_number]
    values.update({"banner_url": BANNER_URL})
  
  values.update(template_values)
  
  # We replace to select languages in necessary cases
  #replace = {'board.html': 'board.es.html',
  #           'manage.html': 'manage.es.html',
  #           'txt_board.html': 'txt_board.es.html',
  #           'txt_thread.html': 'txt_thread.es.html',
  #           'txt_threadlist.html': 'txt_threadlist.es.html'}
  #if template in replace:
  #  template = replace[template]
  
  # Use mobile folder for mobile mode
  if mobile:
    template_folder = "templates/mobile/"
  else:
    template_folder = "templates/"
  
  return engine.render(template_folder + template, values)
