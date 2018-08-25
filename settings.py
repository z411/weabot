# coding=utf-8
import threading

class SettingsLocal(threading.local):
  USING_SQLALCHEMY = False # If SQLAlchemy is installed, set to True to use it
  
  # Ignore these
  BOARD = None
  CONN = None
  MODBROWSE = False
  
  IS_TOR = None
  IS_PROXY = None
  HOST = None

class Settings(object):
  LANG = "es"
  
  # *************** PATH INFORMATION ***************
  NAME = "weabot"
  DOMAIN = ".weabot.org"
  ROOT_DIR = "/weabot/"
  HOME_DIR = "/weabot/"
  IMAGES_DIR = "/weabot/"
  STATIC_DIR = "/weabot/static/"
  HOME_URL = "/"
  BOARDS_URL = "/"
  CGI_URL = "/cgi/"       # URL to folder containing the script
  IMAGES_URL = "/"
  STATIC_URL = "/static/"
  USE_MULTITHREADING = False
  MAX_PROGRAM_THREADS = 8 # Maximum threads this Python application can start (must be 2 or greater)
    # Setting this too high can cause the program to terminate before finishing
    # (Only needed if multithreading is on)
  
  # *************** DATABASE INFORMATION ***************
  DATABASE_HOST = "localhost"
  DATABASE_USERNAME = "weabot"
  DATABASE_PASSWORD = "CHANGEME"
  DATABASE_DB = "weabot"
  # The following two entries apply only if USING_SQLALCHEMY is set to True
  DATABASE_POOL_SIZE = 5        # Initial number of database connections
  DATABASE_POOL_OVERFLOW = 21   # Maximum number of database connections
  
  # *************** HOME PAGE INFORMATION ***************
  SITE_TITLE = "weabot"
  SITE_LOGO = STATIC_URL + "img/logo.png"
  SITE_SLOGAN = ""
  MAINTENANCE = False # Set to True if you are making changes to the server so users can't post
  FULL_MAINTENANCE = False
  ENABLE_RSS = True
  
  # *************** BANNER INFORMATION ***************
  ENABLE_BANNERS = True
  banners_folder = STATIC_URL + "img/"    # Folder containing banners
  banners = {        # filename, width, height
        'default':   [("default.png", "500", "81")],
        '0':         [("cero.gif", "350", "120")],
        'anarkia':   [("anarkia.jpg", "380", "250")],
        'bai':       [("bai.jpg", "600", "110")],
        'juegos':    [("juegos1.jpg", "584", "120"), ("juegos2.jpg", "536", "120")],
        'letras':    [("letras1.png", "565", "130"), ("letras2.png", "479", "130"), ("letras3.png", "512", "130"),
                      ("letras4.jpg", "511", "150")],
        'musica':    [("musica1.jpg", "480", "150")],
        'noticias':  [("noticias.png", "442", "83")],
        'tech':      [("tech1.png", "560", "120"), ("tech2.jpg", "506", "120"), ("tech3.png", "500", "120"),
                      ("tech4.jpg", "500", "120"), ("tech5.jpg", "643", "120"), ("tech6.png", "432", "120")],
        'polka':     [("weird-al.jpg", "960", "150")],
        'salon2d':   [("salon2d_1.png", "400", "140")],
        'tv':        [("tv1.png", "490", "135")],
        'world':     [("world.gif", "600", "240")],
        'zonavip':   [("zonavip1.jpg", "500", "120"), ("zonavip2.gif", "500", "120"), ("zonavip3.png", "500", "120"),
                      ("zonavip4.jpg", "500", "120"), ("zonavip5.gif", "500", "120"), ("zonavip6.png", "500", "120"),
                      ("zonavip7.gif", "500", "120"), ("zonavip8.png", "500", "120"), ("zonavip9.jpg", "500", "120")],
  }
  
  # *************** IMAGES ***************
  CONVERT_PATH = "convert"                    # Location to ImageMagick's convert tool
  # CONVERT_PATH = "C:\\Utils\\ImageMagick-6.7.0-Q16\\convert"
  THUMB_QUALITY = 85                          # Image quality for thumbnails (0-100)

  # *************** Bans ***************
  HTACCESS_GEN = True                         # Set to True to use .htaccess for bans (needed for blind bans!)
  EXCLUDE_GLOBAL_BANS = ['anarkia', 'bai']    # Excludes the following boards from global bans (not board specific bans)
  
  # 'Name': ('Tripcode', 'New name', 'New tripcode', 'New ID', Hide Slip[bool])
  CAPCODES = {
  'Ejemplo': ('xxxxxxxxxx', 'Ejemplo ★', '', 'CAP_USER', True),
  }

  # *************** BOARDS ***************
  MAX_THREADS = 500            # IB
  THREADS_SHOWN_ON_FRONT = 110
  TXT_MAX_THREADS = 10000      # BBS

  TRIM_METHOD = 0              # Which threads are trimmed first:
  TXT_TRIM_METHOD = 1          # 0 = oldest (Futaba), 1 = inactive (2ch), 2 = least bumped (4chan)

  CLOSE_THREAD_ON_REPLIES = 1000
  TXT_CLOSE_THREAD_ON_REPLIES = 1000

  MAX_AGE_ALERT = 0.1 # Multiplier for thread expiration alert

  SECRET = 'CHANGEME' # Random seed for secure tripcodes, change it to something random
  ALLOW_SECURE_TRIPCODES = False
  TRIP_CHAR = '◆'

  HOME_NEWS = 10               # News posts shown on home page
  HOME_LASTPOSTS = 20         # Last posts shown on home page
  HOME_LASTPOSTS_LENGTH = 100

  MODNEWS_MAX_POSTS = 30      # Max posts in the Manage front page
  REPORTS_ENABLE = True       # Enable or disable report system
  REPORTS_PER_PAGE = 100
  RECYCLEBIN_POSTS_PER_PAGE = 25
  
  DELETE_FORBID_LENGTH = 5    # User can't delete own thread if replies exceed this
  ARCHIVE_MIN_LENGTH = 5      # Minimum thread length to archive (0 = archive always)
  
  STYLES = ('Rene', 'Dickgirl', 'Red', 'Photon', 'Night', 'Futaba', 'Burichan', 'Putaba')
  STYLES_DEFAULT = 0
  
  TXT_STYLES = ('4am', 'Ayashii', 'Baisano', 'Blue Moon', 'Ciber', 'Futanari', 'Headline', 'Picnic')
  TXT_STYLES_DEFAULT = 2
  
  TIME_ZONE = -3
  USE_MARKDOWN = False
  USE_HTML = False
  VIDEO_THUMBS = True
  VIDEO_THUMBS_LIMIT = 5
  GOOGLE_API_KEY = 'CHANGEME' # Used for Youtube thumbnails

  _ = SettingsLocal()    # Used when running multiple threads