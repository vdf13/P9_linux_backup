#!/usr/bin/python3.7
# -*- coding: utf-8 -*-

# Victor De Faria 2020-04-27 2020-05-xx

import os
import datetime

def nom():
    date = datetime.datetime.now()
    texte = "backup-wordpress-{}.tar.gz".format(date.strftime("%Y-%m-%d-%H-%M"))
    return texte

def fichiers(dir_backup):
    fichiers = os.listdir(dir_backup)
    backup_files = []
    for file in fichiers:
        if "backup" in file:
            backup_files.append(file)
    return(backup_files)    

dir_wordpress = "/var/www/html/wordpress/index.php"
dir_backup = "/home/administrateur/backup/"

backup_files = fichiers(dir_backup)
print(backup_files)
nom_backup = nom()
print(nom_backup)

os.system("tar czvf {}{} {}".format(dir_backup, nom_backup, dir_wordpress))
