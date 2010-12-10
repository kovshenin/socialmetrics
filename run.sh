#!/bin/sh
sass ./templates/static/css/application.sass:./templates/static/css/application.css
python2.5 .gae/dev_appserver.py --use_sqlite .

