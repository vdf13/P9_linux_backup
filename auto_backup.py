#!/usr/bin/python3.7
# -*- coding: utf-8 -*-

# Victor De Faria 2020-04-27 2020-05-xx

# IMPORTATION DES MODULES
import os
import datetime

# DEFINITION DES FONCTIONS
def nom():
    # Fonction qui génère un nom de fichier en fonction de la date et heure de la sauvegarde
    date = datetime.datetime.now()
    texte = "backup-wordpress-{}.tar.gz".format(date.strftime("%Y-%m-%d-%H-%M"))
    return texte


def fichiers(dir_backup):
    '''
    Fonction qui récupère la liste des fichiers du répertoire backup
    et ne renvoie que ceux dont le nom contient 'backup'.
    Si 8 fichiers dans le répertoire, alors le plus ancien est supprimé.
    '''
    fichiers = os.listdir(dir_backup)
    backup_files = []
    for file in fichiers:
        if "backup" in file:
            backup_files.append(file)
    backup_files = sorted(backup_files)
    if len(backup_files) > 7:
        os.remove(dir_backup + backup_files[0])
        backup_files.remove(backup_files[0])
    return(backup_files)    

# Définition des constantes des répertoires
dir_wordpress = "/var/www/html/wordpress/index.php"
dir_backup = "/home/administrateur/backup/"


#  //  MAIN PROGRAM // PROGRAMME PRINCIPAL //
# Récupération de la liste des copies de sauvegarde
backup_files = fichiers(dir_backup)
print(backup_files)
# Définition du nom de la sauvegarde du jour
nom_backup = nom()
print(nom_backup)

os.system("tar czvf {}{} {}".format(dir_backup, nom_backup, dir_wordpress))
