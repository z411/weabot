-- phpMyAdmin SQL Dump
-- version 4.7.7
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Aug 24, 2018 at 09:12 PM
-- Server version: 10.1.35-MariaDB
-- PHP Version: 5.6.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `weabot`
--

-- --------------------------------------------------------

--
-- Table structure for table `archive`
--

CREATE TABLE `archive` (
  `id` int(10) UNSIGNED NOT NULL,
  `boardid` smallint(5) UNSIGNED NOT NULL,
  `timestamp` int(20) UNSIGNED NOT NULL,
  `subject` varchar(255) CHARACTER SET latin1 NOT NULL,
  `length` smallint(5) UNSIGNED NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `bans`
--

CREATE TABLE `bans` (
  `id` mediumint(6) UNSIGNED NOT NULL,
  `ip` int(15) UNSIGNED NOT NULL,
  `netmask` int(15) UNSIGNED DEFAULT NULL,
  `boards` text NOT NULL,
  `added` int(10) UNSIGNED NOT NULL,
  `until` int(10) UNSIGNED NOT NULL,
  `staff` varchar(50) NOT NULL,
  `reason` text NOT NULL,
  `note` text NOT NULL,
  `blind` tinyint(1) UNSIGNED NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `boards`
--

CREATE TABLE `boards` (
  `id` tinyint(3) UNSIGNED NOT NULL,
  `dir` varchar(16) NOT NULL,
  `name` varchar(64) NOT NULL,
  `longname` varchar(128) NOT NULL,
  `subname` char(3) NOT NULL,
  `postarea_desc` text NOT NULL,
  `postarea_extra` text NOT NULL,
  `force_css` varchar(255) NOT NULL,
  `board_type` tinyint(1) UNSIGNED NOT NULL,
  `anonymous` varchar(128) NOT NULL DEFAULT 'Sin Nombre',
  `subject` varchar(64) NOT NULL DEFAULT 'Sin asunto',
  `message` varchar(128) NOT NULL DEFAULT 'Sin mensaje',
  `disable_name` tinyint(1) UNSIGNED NOT NULL DEFAULT '0',
  `disable_subject` tinyint(1) UNSIGNED NOT NULL DEFAULT '0',
  `useid` tinyint(1) UNSIGNED NOT NULL DEFAULT '1',
  `slip` tinyint(1) UNSIGNED NOT NULL DEFAULT '0',
  `countrycode` tinyint(1) UNSIGNED DEFAULT '0',
  `recyclebin` tinyint(1) UNSIGNED NOT NULL DEFAULT '1',
  `locked` tinyint(1) UNSIGNED NOT NULL DEFAULT '0',
  `secret` tinyint(1) UNSIGNED NOT NULL DEFAULT '0',
  `allow_spoilers` tinyint(1) UNSIGNED NOT NULL DEFAULT '0',
  `allow_oekaki` tinyint(1) UNSIGNED NOT NULL DEFAULT '0',
  `allow_noimage` tinyint(1) UNSIGNED NOT NULL DEFAULT '1',
  `allow_images` tinyint(1) UNSIGNED NOT NULL DEFAULT '1',
  `allow_image_replies` tinyint(1) UNSIGNED NOT NULL DEFAULT '1',
  `maxsize` smallint(5) UNSIGNED NOT NULL DEFAULT '500',
  `thumb_px` smallint(3) UNSIGNED NOT NULL DEFAULT '250',
  `numthreads` tinyint(2) UNSIGNED NOT NULL DEFAULT '10',
  `numcont` tinyint(2) UNSIGNED NOT NULL DEFAULT '10',
  `numline` tinyint(3) UNSIGNED NOT NULL DEFAULT '20',
  `maxage` smallint(3) UNSIGNED NOT NULL DEFAULT '0',
  `maxinactive` smallint(3) UNSIGNED NOT NULL DEFAULT '0',
  `archive` tinyint(1) UNSIGNED NOT NULL DEFAULT '0',
  `threadsecs` smallint(4) UNSIGNED NOT NULL DEFAULT '600',
  `postsecs` tinyint(3) UNSIGNED NOT NULL DEFAULT '30'
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `boards_filetypes`
--

CREATE TABLE `boards_filetypes` (
  `boardid` smallint(5) UNSIGNED NOT NULL,
  `filetypeid` smallint(5) UNSIGNED NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `boards_filetypes`
--

INSERT INTO `boards_filetypes` (`boardid`, `filetypeid`) VALUES
(13, 5),
(13, 2),
(13, 1),
(10, 2),
(10, 1),
(10, 3),
(1, 2),
(1, 1),
(1, 3),
(5, 2),
(5, 1),
(5, 3),
(15, 2),
(15, 1),
(15, 3),
(4, 2),
(4, 1),
(4, 3),
(8, 4),
(8, 2),
(8, 1),
(8, 3),
(103, 5),
(0, 9),
(21, 3),
(21, 1),
(21, 2),
(22, 2),
(22, 1),
(22, 3),
(23, 2),
(23, 1),
(23, 3),
(0, 5),
(28, 2),
(28, 1),
(28, 3),
(3, 5),
(29, 5),
(29, 2),
(29, 1),
(3, 2),
(39, 5),
(37, 5),
(37, 2),
(37, 1),
(37, 3),
(3, 1),
(29, 3),
(39, 2),
(0, 4),
(0, 10),
(35, 2),
(30, 9),
(30, 5),
(3, 3),
(46, 5),
(0, 2),
(103, 2),
(103, 1),
(33, 9),
(33, 10),
(33, 7),
(34, 9),
(34, 5),
(34, 4),
(34, 10),
(34, 2),
(34, 7),
(34, 6),
(34, 11),
(34, 8),
(34, 1),
(30, 10),
(39, 1),
(39, 3),
(30, 2),
(30, 7),
(30, 6),
(30, 8),
(30, 1),
(30, 3),
(0, 7),
(13, 3),
(33, 6),
(44, 2),
(44, 1),
(44, 3),
(103, 3),
(45, 5),
(45, 2),
(45, 1),
(33, 11),
(0, 6),
(0, 8),
(0, 1),
(0, 3),
(45, 3),
(46, 2),
(46, 1),
(46, 3),
(33, 8),
(34, 3);

-- --------------------------------------------------------

--
-- Table structure for table `filetypes`
--

CREATE TABLE `filetypes` (
  `id` smallint(5) UNSIGNED NOT NULL,
  `ext` varchar(16) COLLATE utf8_unicode_ci NOT NULL,
  `mime` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `image` varchar(32) COLLATE utf8_unicode_ci NOT NULL,
  `preserve_name` tinyint(1) NOT NULL,
  `ffmpeg_thumb` tinyint(1) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `filters`
--

CREATE TABLE `filters` (
  `id` int(10) UNSIGNED NOT NULL,
  `boards` text NOT NULL,
  `type` tinyint(1) NOT NULL,
  `action` tinyint(1) NOT NULL,
  `from` varchar(255) NOT NULL,
  `from_trip` varchar(30) NOT NULL,
  `to` text NOT NULL,
  `reason` varchar(255) NOT NULL,
  `seconds` int(20) UNSIGNED NOT NULL,
  `blind` tinyint(1) NOT NULL,
  `redirect_url` varchar(40) NOT NULL,
  `redirect_time` tinyint(3) UNSIGNED NOT NULL,
  `staff` varchar(50) NOT NULL,
  `added` int(20) UNSIGNED NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `last`
--

CREATE TABLE `last` (
  `id` int(5) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `logs`
--

CREATE TABLE `logs` (
  `id` int(11) NOT NULL,
  `timestamp` int(20) UNSIGNED NOT NULL,
  `staff` varchar(75) NOT NULL,
  `action` text NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `news`
--

CREATE TABLE `news` (
  `id` smallint(5) UNSIGNED NOT NULL,
  `type` tinyint(1) NOT NULL,
  `staffid` tinyint(3) UNSIGNED NOT NULL,
  `staff_name` varchar(50) NOT NULL,
  `title` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `name` varchar(255) NOT NULL,
  `timestamp_formatted` varchar(255) NOT NULL,
  `timestamp` int(20) UNSIGNED NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `posts`
--

CREATE TABLE `posts` (
  `id` int(10) UNSIGNED NOT NULL,
  `boardid` smallint(5) UNSIGNED NOT NULL,
  `parentid` mediumint(10) UNSIGNED NOT NULL,
  `timestamp` int(20) UNSIGNED DEFAULT NULL,
  `timestamp_formatted` varchar(50) NOT NULL,
  `name` varchar(255) NOT NULL,
  `tripcode` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `password` varchar(255) NOT NULL,
  `file` varchar(75) NOT NULL,
  `file_hex` varchar(75) NOT NULL,
  `file_size` int(20) UNSIGNED NOT NULL,
  `image_width` smallint(5) UNSIGNED NOT NULL,
  `image_height` smallint(5) UNSIGNED NOT NULL,
  `thumb` varchar(255) NOT NULL,
  `thumb_width` smallint(5) UNSIGNED NOT NULL,
  `thumb_height` smallint(5) UNSIGNED NOT NULL,
  `ip` int(15) UNSIGNED NOT NULL,
  `IS_DELETED` tinyint(1) NOT NULL,
  `bumped` int(20) UNSIGNED NOT NULL,
  `last` int(20) UNSIGNED NOT NULL,
  `locked` tinyint(1) NOT NULL,
  `expires` int(20) UNSIGNED NOT NULL,
  `expires_formatted` varchar(30) NOT NULL,
  `expires_alert` tinyint(1) NOT NULL,
  `length` smallint(4) UNSIGNED NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `reports`
--

CREATE TABLE `reports` (
  `id` mediumint(8) UNSIGNED NOT NULL,
  `board` varchar(16) NOT NULL,
  `postid` int(10) UNSIGNED NOT NULL,
  `parentid` int(10) UNSIGNED NOT NULL,
  `link` varchar(64) NOT NULL,
  `ip` varchar(15) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `reporterip` varchar(15) NOT NULL,
  `timestamp` int(20) UNSIGNED NOT NULL,
  `timestamp_formatted` varchar(50) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `search`
--

CREATE TABLE `search` (
  `id` int(10) NOT NULL,
  `boardid` smallint(5) NOT NULL,
  `timestamp` int(20) NOT NULL,
  `subject` varchar(255) CHARACTER SET latin1 NOT NULL,
  `message` text CHARACTER SET latin1 NOT NULL,
  `parentid` int(10) NOT NULL,
  `parenttime` int(20) NOT NULL,
  `parentsub` varchar(255) CHARACTER SET latin1 NOT NULL,
  `num` smallint(5) NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `search_kako`
--

CREATE TABLE `search_kako` (
  `id` int(10) UNSIGNED NOT NULL,
  `boardid` smallint(5) UNSIGNED NOT NULL,
  `pid` int(10) UNSIGNED NOT NULL,
  `subject` varchar(255) CHARACTER SET latin1 NOT NULL,
  `message` text CHARACTER SET latin1 NOT NULL,
  `parentid` int(10) UNSIGNED NOT NULL,
  `num` smallint(5) UNSIGNED NOT NULL,
  `timestamp_formatted` varchar(50) CHARACTER SET latin1 NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `search_log`
--

CREATE TABLE `search_log` (
  `id` int(10) UNSIGNED NOT NULL,
  `timestamp` int(20) UNSIGNED NOT NULL,
  `keyword` varchar(255) CHARACTER SET latin1 NOT NULL,
  `ita` varchar(16) CHARACTER SET latin1 NOT NULL,
  `ip` int(20) UNSIGNED NOT NULL,
  `res` smallint(5) UNSIGNED NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Table structure for table `staff`
--

CREATE TABLE `staff` (
  `id` tinyint(3) UNSIGNED NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `added` int(10) UNSIGNED NOT NULL,
  `lastactive` int(10) UNSIGNED NOT NULL,
  `rights` tinyint(1) UNSIGNED NOT NULL DEFAULT '0'
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `staff` (`id`, `username`, `password`) VALUES (NULL, 'admin', '21232f297a57a5a743894a0e4a801fc3');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `archive`
--
ALTER TABLE `archive`
  ADD PRIMARY KEY (`id`,`boardid`);

--
-- Indexes for table `bans`
--
ALTER TABLE `bans`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ip` (`ip`);

--
-- Indexes for table `boards`
--
ALTER TABLE `boards`
  ADD PRIMARY KEY (`id`),
  ADD KEY `dir` (`dir`);

--
-- Indexes for table `filetypes`
--
ALTER TABLE `filetypes`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `filters`
--
ALTER TABLE `filters`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `logs`
--
ALTER TABLE `logs`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `news`
--
ALTER TABLE `news`
  ADD PRIMARY KEY (`type`,`id`);

--
-- Indexes for table `posts`
--
ALTER TABLE `posts`
  ADD PRIMARY KEY (`boardid`,`id`),
  ADD KEY `parentid` (`parentid`),
  ADD KEY `bumped` (`bumped`);

--
-- Indexes for table `reports`
--
ALTER TABLE `reports`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `search`
--
ALTER TABLE `search`
  ADD PRIMARY KEY (`id`,`boardid`);
ALTER TABLE `search` ADD FULLTEXT KEY `message` (`message`);
ALTER TABLE `search` ADD FULLTEXT KEY `subject` (`subject`);

--
-- Indexes for table `search_kako`
--
ALTER TABLE `search_kako`
  ADD PRIMARY KEY (`id`,`boardid`);
ALTER TABLE `search_kako` ADD FULLTEXT KEY `kakoindex` (`message`,`subject`);

--
-- Indexes for table `search_log`
--
ALTER TABLE `search_log`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `staff`
--
ALTER TABLE `staff`
  ADD PRIMARY KEY (`id`),
  ADD KEY `username` (`username`,`password`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bans`
--
ALTER TABLE `bans`
  MODIFY `id` mediumint(6) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=815;

--
-- AUTO_INCREMENT for table `boards`
--
ALTER TABLE `boards`
  MODIFY `id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=47;

--
-- AUTO_INCREMENT for table `filetypes`
--
ALTER TABLE `filetypes`
  MODIFY `id` smallint(5) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `filters`
--
ALTER TABLE `filters`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=58;

--
-- AUTO_INCREMENT for table `logs`
--
ALTER TABLE `logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1787;

--
-- AUTO_INCREMENT for table `news`
--
ALTER TABLE `news`
  MODIFY `id` smallint(5) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `posts`
--
ALTER TABLE `posts`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `reports`
--
ALTER TABLE `reports`
  MODIFY `id` mediumint(8) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=759;

--
-- AUTO_INCREMENT for table `search_kako`
--
ALTER TABLE `search_kako`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=62656;

--
-- AUTO_INCREMENT for table `search_log`
--
ALTER TABLE `search_log`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2532;

--
-- AUTO_INCREMENT for table `staff`
--
ALTER TABLE `staff`
  MODIFY `id` tinyint(3) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=53;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
