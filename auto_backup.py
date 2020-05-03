#!/usr/bin/python3.7
# -*- coding: utf-8 -*-

# Victor De Faria 2020-04-27 2020-05-xx

import os
import datetime

def nom():
    date = datetime.datetime.now()
    texte = "backup-wordpress-{}.tar.gz".format(date.strftime("%Y-%m-%d-%H-%M"))
    return texte
texte = nom()
print(texte)
