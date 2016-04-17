SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS `archive` (
  `id` int(10) unsigned NOT NULL,
  `boardid` smallint(5) unsigned NOT NULL,
  `timestamp` int(20) unsigned NOT NULL,
  `subject` varchar(255) CHARACTER SET latin1 NOT NULL,
  `length` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`,`boardid`)
);

CREATE TABLE IF NOT EXISTS `bans` (
  `id` mediumint(5) unsigned NOT NULL AUTO_INCREMENT,
  `ip` int(15) unsigned NOT NULL,
  `netmask` int(15) unsigned DEFAULT NULL,
  `boards` text NOT NULL,
  `added` int(20) unsigned NOT NULL,
  `until` int(20) unsigned NOT NULL,
  `staff` varchar(75) NOT NULL,
  `reason` text NOT NULL,
  `note` text NOT NULL,
  `blind` tinyint(4) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ip` (`ip`)
);

CREATE TABLE IF NOT EXISTS `boards` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `dir` varchar(75) NOT NULL,
  `name` varchar(128) NOT NULL,
  `board_type` tinyint(3) unsigned NOT NULL,
  `anonymous` varchar(512) NOT NULL DEFAULT 'Sin Nombre',
  `subject` varchar(128) NOT NULL DEFAULT 'Sin asunto',
  `message` varchar(512) NOT NULL DEFAULT 'Sin mensaje',
  `forced_anonymous` tinyint(1) NOT NULL,
  `useid` tinyint(3) unsigned NOT NULL,
  `recyclebin` tinyint(3) unsigned NOT NULL,
  `disable_subject` tinyint(1) NOT NULL,
  `allow_images` tinyint(1) NOT NULL DEFAULT '1',
  `allow_image_replies` tinyint(1) NOT NULL DEFAULT '1',
  `allow_noimage` tinyint(1) NOT NULL,
  `allow_spoilers` tinyint(1) NOT NULL DEFAULT '1',
  `allow_oekaki` tinyint(1) NOT NULL,
  `secret` tinyint(1) NOT NULL,
  `lockable` tinyint(1) NOT NULL DEFAULT '1',
  `locked` tinyint(1) NOT NULL,
  `tripcode_character` varchar(8) NOT NULL DEFAULT '!',
  `postarea_extra_html_top` text NOT NULL,
  `postarea_extra_always` tinyint(1) NOT NULL,
  `postarea_extra_html_bottom` text NOT NULL,
  `force_css` varchar(256) NOT NULL,
  `maxsize` int(10) unsigned NOT NULL DEFAULT '2000',
  `maxage` int(10) NOT NULL,
  `maxinactive` int(10) NOT NULL,
  `archive` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dir` (`dir`)
);

CREATE TABLE IF NOT EXISTS `filetypes` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `ext` varchar(16) COLLATE utf8_unicode_ci NOT NULL,
  `mime` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `image` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `preserve_name` tinyint(1) NOT NULL,
  `ffmpeg_thumb` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
);

INSERT INTO `filetypes` (`id`, `ext`, `mime`, `image`, `preserve_name`, `ffmpeg_thumb`) VALUES
(1, 'jpg', 'image/jpeg', '', 0, 0),
(2, 'png', 'image/png', '', 0, 0),
(3, 'gif', 'image/gif', '', 0, 0),
(4, 'swf', 'application/x-shockwave-flash', 'mime/x-shockwave-flash.png', 1, 0),
(5, 'webm', 'video/webm', '', 0, 1),
(6, 'ogg', 'audio/ogg', '', 0, 1),
(7, 'opus', 'audio/opus', '', 0, 1);

CREATE TABLE IF NOT EXISTS `filetypes` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `ext` varchar(16) COLLATE utf8_unicode_ci NOT NULL,
  `mime` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `image` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `preserve_name` tinyint(1) NOT NULL,
  `ffmpeg_thumb` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `filters` (
  `id` int(10) NOT NULL AUTO_INCREMENT,
  `boards` text NOT NULL,
  `type` tinyint(1) NOT NULL,
  `action` tinyint(1) NOT NULL,
  `from` varchar(255) NOT NULL,
  `from_trip` varchar(30) NOT NULL,
  `to` text NOT NULL,
  `reason` text NOT NULL,
  `seconds` int(20) unsigned NOT NULL,
  `blind` tinyint(1) NOT NULL,
  `redirect_url` varchar(40) NOT NULL,
  `redirect_time` int(3) NOT NULL,
  `staff` varchar(75) NOT NULL,
  `added` int(20) unsigned NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `logs` (
  `timestamp` int(20) unsigned NOT NULL,
  `staff` varchar(75) NOT NULL,
  `action` text NOT NULL
);

CREATE TABLE IF NOT EXISTS `news` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `type` tinyint(2) NOT NULL,
  `staffid` int(10) NOT NULL,
  `staff_name` varchar(255) NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `name` varchar(255) NOT NULL,
  `timestamp_formatted` varchar(255) NOT NULL,
  `timestamp` int(20) NOT NULL,
  PRIMARY KEY (`type`,`id`)
);

CREATE TABLE IF NOT EXISTS `posts` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `boardid` smallint(5) unsigned NOT NULL,
  `parentid` int(10) unsigned NOT NULL,
  `timestamp` int(20) DEFAULT NULL,
  `name` varchar(255) NOT NULL,
  `tripcode` varchar(30) NOT NULL,
  `email` varchar(255) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `password` varchar(255) NOT NULL,
  `file` varchar(75) NOT NULL,
  `file_hex` varchar(75) NOT NULL,
  `file_original` varchar(255) NOT NULL,
  `file_size` int(20) NOT NULL,
  `image_width` smallint(5) unsigned NOT NULL,
  `image_height` smallint(5) unsigned NOT NULL,
  `animation` varchar(75) NOT NULL,
  `time_taken` varchar(10) NOT NULL,
  `thumb` varchar(255) NOT NULL,
  `thumb_width` smallint(5) unsigned NOT NULL,
  `thumb_height` smallint(5) unsigned NOT NULL,
  `ip` int(15) unsigned NOT NULL,
  `timestamp_formatted` varchar(50) NOT NULL,
  `IS_DELETED` tinyint(1) NOT NULL,
  `bumped` int(20) unsigned NOT NULL,
  `last` int(20) unsigned NOT NULL,
  `locked` tinyint(1) NOT NULL,
  `expires` int(20) NOT NULL,
  `expires_formatted` varchar(30) NOT NULL,
  `expires_alert` tinyint(1) NOT NULL,
  `length` int(5) NOT NULL,
  PRIMARY KEY (`boardid`,`id`),
  KEY `parentid` (`parentid`),
  KEY `bumped` (`bumped`)
);

-- --------------------------------------------------------

--
-- Table structure for table `reports`
--

CREATE TABLE IF NOT EXISTS `reports` (
  `id` int(10) NOT NULL AUTO_INCREMENT,
  `board` varchar(75) NOT NULL,
  `postid` int(10) NOT NULL,
  `parentid` int(10) NOT NULL,
  `ip` varchar(15) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `reporterip` varchar(15) NOT NULL,
  `timestamp` int(20) NOT NULL,
  `timestamp_formatted` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `staff` (
  `id` smallint(5) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(75) NOT NULL,
  `password` varchar(255) NOT NULL,
  `added` int(20) unsigned NOT NULL,
  `lastactive` int(20) unsigned NOT NULL,
  `rights` tinyint(1) unsigned NOT NULL DEFAULT '0',
  `boards` text NOT NULL,
  PRIMARY KEY (`id`),
  KEY `username` (`username`,`password`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=34 ;

INSERT INTO `weabot`.`staff` (`id`, `username`, `password`, `added`, `lastactive`, `rights`, `boards`)
VALUES (NULL, 'admin', '21232f297a57a5a743894a0e4a801fc3', '0', '0', '0', '');


/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
