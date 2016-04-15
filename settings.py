# coding=utf-8
import threading

class SettingsLocal(threading.local):
  USING_SQLALCHEMY = False	# If SQLAlchemy is installed, set to True to use it
  
  # Ignore these
  BOARD = None
  CONN = None
  MODBROWSE = False

class Settings(object):
  LANG = "es"
  
  # *************** PATH INFORMATION ***************
  NAME = ""
  DOMAIN = ""
  ROOT_DIR = ""
  HOME_DIR = ""
  IMAGES_DIR = ""
  STATIC_DIR = ""
  HOME_URL = ""
  BOARDS_URL = "/"
  CGI_URL = "/cgi/"	# Path to folder containing the script
  IMAGES_URL = "/"
  STATIC_URL = "/static/"
  USE_MULTITHREADING = False
  MAX_PROGRAM_THREADS = 8 # Maximum threads this Python application can start (must be 2 or greater)
                          # Setting this too high can cause the program to terminate before finishing
                          # (Only needed if multithreading is on)
  
  # *************** DATABASE INFORMATION ***************
  DATABASE_HOST = "localhost"
  DATABASE_USERNAME = ""
  DATABASE_PASSWORD = ""
  DATABASE_DB = ""
  # The following two entries apply only if USING_SQLALCHEMY is set to True
  DATABASE_POOL_SIZE = 5					# Initial number of database connections
  DATABASE_POOL_OVERFLOW = 21				# Maximum number of database connections
  
  # *************** HOME PAGE INFORMATION ***************
  SITE_TITLE = ""
  SITE_LOGO = STATIC_URL + "logo.png"
  SITE_SLOGAN = ""
  MAINTENANCE = False
  # Set this to True if you are making changes to the server so the users can't post
  ENABLE_RSS = False
  
  # *************** BANNER INFORMATION ***************
  ENABLE_BANNERS = True
  banners_folder = STATIC_URL + "img/"		# Folder containing banners
  banners = {'default': [],}
  BANNER_WIDTH = 300
  BANNER_HEIGHT = 100
  
  # *************** IMAGES ***************
  IMAGE_SIZE_UNIT = "KB"	# B or KB

  CONVERT_PATH = "convert" # Location to ImageMagick's convert tool
  # CONVERT_PATH = "C:\\Utils\\ImageMagick-6.7.0-Q16\\convert"
  MAX_DIMENSION_FOR_OP_IMAGE = 250
  MAX_DIMENSION_FOR_REPLY_IMAGE = 250
  MAX_DIMENSION_FOR_IMAGE_CATALOG = 50
  THUMB_QUALITY = 75							# Image quality for thumbnails (0-100)
  spoilop_filename = HOME_URL + "spoiler.gif"	# OP Spoiler image path, should be a square image of the dimensions MAX_DIMENSION_FOR_OP_IMAGE above
  spoil_filename = HOME_URL + "spoiler.gif"		# Reply Spoiler image path, should be a square image of the dimensions MAX_DIMENSION_FOR_REPLY_IMAGE above
  flash_filename = HOME_URL + "flash.png"
  
  # *************** IDs ***************
  IPHASH_LENGTH = 8 # Unused
  IPHASH_SAGEWORD = '???'
  
  # *************** Bans ***************
  HTACCESS_GEN = False # Set to True to use .htaccess for bans (needed for blind bans!)
  
  # *************** April Fool's ***************
  ATTACKHEAL_ENABLE = False
  ATTACK_RANGE = (10, 200) # Rango probable de los puntos que se hace daño/cura (min/max)
  HEAL_RANGE = (100, 200)
  MP_REGEN_RANGE = (10, 100) # Rango probable en que el MP se regenera por cada post que se hace (min/max)
  
  # *************** BOARDS ***************
  MAX_THREADS = 500
  THREADS_SHOWN_ON_FRONT_PAGE = 10
  REPLIES_SHOWN_ON_FRONT_PAGE = 10
  REPLIES_SHOWN_ON_FRONT_PAGE_STICKY = 3
  CLOSE_THREAD_ON_REPLIES = 1000
  TRIM_METHOD = 0 # Which threads are trimmed first (0 = oldest like futaba, 1 = inactive like 2ch, 2 = least bumped like 4chan)
  
  MOBILE_THREADS_SHOWN_ON_FRONT_PAGE = 15
  MAX_AGE_ALERT = 0.15 # Multiplier for thread expiration alert
  
  TXT_MAX_THREADS = 150
  TXT_THREADS_SHOWN_ON_FRONT_PAGE = 15
  TXT_THREADS_SHOWN_ON_THREAD_LIST = 50
  TXT_REPLIES_SHOWN_ON_FRONT_PAGE = 10
  TXT_REPLIES_SHOWN_ON_FRONT_PAGE_STICKY = 5
  TXT_CLOSE_THREAD_ON_REPLIES = 1000
  TXT_TRIM_METHOD = 1
  
  SECONDS_BETWEEN_NEW_THREADS = 300       # Time to wait between a new thread
  SECONDS_BETWEEN_REPLIES = 10            # Time to wait between a new post
  DEFAULT_SAGE = 'sage'
  DEFAULT_NOKO = 'noko'
  
  SECRET = '9s48fj4sf8jsfiosdfw34opiefme49fk4fo4kfoirjxg' # Random seed for secure tripcodes, change it to something random
  ALLOW_SECURE_TRIPCODES = False
  
  POST_LINE_WIDTH = 160                   # Maximum width of posts
  POST_MAX_LINES = 40                     # Maximum lines for posts (when outside a thread)

  MAX_DAYS_THREADS = 1                    # Time limit for popular threads (home)

  HOME_NEWS = 1                           # News posts shown on home page
  HOME_LASTPOSTS = 10                     # Last posts shown on home page
  HOME_LASTPOSTS_LENGTH = 85

  MODNEWS_MAX_POSTS = 30                  # Maximum posts in the Manage front page

  REPORTS_ENABLE = True                   # Enable or disable report system
  REPORTS_REASON_LONG = 100
  REPORTS_PER_PAGE = 30

  RECYCLEBIN_POSTS_PER_PAGE = 30

  SHOW_NAVBAR = True                      # If you set this to True, edit navbar.html
  DEFAULT_STYLE = "Futaba"                # Futaba or Burichan
  
  USE_MARKDOWN = False
  
  PRIVACY_LOCK = False
  
  _ = SettingsLocal() # Used when running multiple threads
