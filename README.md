weabot
======
weabot is a Python textboard and imageboard script made for Bienvenido a Internet BBS/IB. It's based on PyIB.

New features
------------
- Textboards
- Home page
- Report system
- Thread locking and permasaging
- Mobile website
- IDs
- Noko
- View and delete posts by IP
- Oekaki
- Flexible filetypes (such as Flash)
- Wordfilters
- Proper markdown and HTML
- Many bugfixes and security improvements, and other minor improvements

Requirements
------------
* Python 2.x
* MySQL
* WSGI/FastCGI (Optional)

Installation
------------
1. Set up your web server to run Python scripts as CGI or FastCGI (see .htaccess example)
2. Create a MySQL database and import the weabot.sql file
3. Navigate to http://yoursite.com/weabot_folder/weabot.py/manage
4. Log-in with credentials admin/123456 - then create your own staff account and delete admin

Authors
-------
weabot fork by Bienvenido a Internet N.P.O. <burocracia@bienvenidoainternet.org>
Original work by tslocum <tslocum@gmail.com> https://github.com/tslocum/PyIB

License
-------
weabot is licensed under the AGPLv3, with portions under the GPLv3.
If you run weabot, even on a web server, you must publish any changes of the source code, and under the same license.
Please read the full text of the license for more details (LICENSE file).
If you don't agree with the license terms, please choose one of the alternatives to weabot listed below.

Alternatives
------------
Some alternatives to weabot are:

* [Wakaba/Kareha](http://wakaba.c3.cx/s/web/wakaba_kareha)
* [TinyIB](https://github.com/tslocum/TinyIB)
* [Tinyboard](http://tinyboard.org/)
* [PyIB](https://github.com/tslocum/PyIB)