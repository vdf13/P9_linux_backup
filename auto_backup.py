#!/usr/bin/python3.7
# -*- coding: utf-8 -*-

# Victor De Faria 2020-04-27 2020-05-18
# Algorythme du programme
#   |
#   |-> Générer le nom de la sauvevarde  <- Source fichier data.yml
#   |-> Sauvegarder les données sur le serveur local
#      |-> Récupérer la liste des fichiers sauvegarde du serveur FTP
#      |-> Supprimer les plus anciennes sauvegardes
#       |-> Transférer la sauvegarde sur le serveur FTP

# IMPORTATION DES MODULES
import os, sys, re, datetime, glob, netrc, ftplib, yaml, tarfile

# DEFINITION DES FONCTIONS

def nom(texte, base_name):
    '''
    Fonction qui génère un nom de fichier en fonction de
    la date et heure de la sauvegarde
    un nom donné en variable pour différencier les serveurs
    '''
    date = datetime.datetime.now()
    texte = f'backup-{base_name}-{texte}-{date.strftime("%Y-%m-%d-%H-%M")}.tar.gz'
    return texte


def supp_old_backup(texte, base_name, dir_back):
    '''
    Fonction qui récupère la liste des fichiers du répertoire backup
    ne renvoie que ceux dont le nom contient 'backup' + 'nom_spécifié' . Utilise les expressions régulières.
    Si les fichiers dans le répertoire sont plus ancien que 'delai_retention'  alors ils sont supprimés.
    Renvoie la liste des fichiers de sauvegarde. Utile en cas de DEBUG
    '''
    fichiers = glob.glob(dir_back + "*")
    fichiers.sort(key=os.path.getmtime)
    backup_files = []
    now = datetime.datetime.now()
    for file in fichiers:
        reg = re.search(rf'backup-{base_name}-{texte}(-[0-9]+)+.tar.gz', file)
        if reg is not None:
            # Suppression des fichiers sauvegardes + ancien que la valeur 'delai' du fichier yaml
            file_date = datetime.datetime.fromtimestamp(os.path.getmtime(file))
            delta = now - file_date
            if delta.days < int(delai_retention):
                backup_files.append(reg.group(0))
                #print("Récent : ", file)    # DEBUG
            else:
                print(f"La Sauvegarde de plus de {delai_retention} jours va être supprimé du serveur {wp_host}: ", file)    # Message qui sera récupéré par le logger lors de l'execution
                os.remove(file)
            
    return(backup_files)    

def supp_old_ftp_backup(texte, base_name):
    '''
    Fonction qui récupère la liste des fichiers du répertoire de backup sur le serveur FTP 
    ne renvoie que ceux dont le nom contient 'backup' + 'nom_spécifié' . Utilise les expressions régulières.
    Si les fichiers dans le répertoire sont plus ancien que 'delai_retention'  alors ils sont supprimés.
    Renvoie la liste des fichiers de sauvegarde. Utile en cas de DEBUG
    '''
    # On récupère la liste des fichiers
    now = datetime.datetime.now()
    with ftplib.FTP(ftp_host, auth_ftp[0], auth_ftp[2]) as ftp:
        try:
            ftp.cwd(dir_ftp)
            fichiers = []
            backup_ftp_files = []
            ftp.retrlines('LIST -tr', fichiers.append)
            for file in fichiers:
                reg = re.search(rf'backup-{base_name}-{texte}(-[0-9]+)+.tar.gz', file)
                if reg is not None:
                    data = ftp.sendcmd('MDTM ' + reg.group())
                    file_date = datetime.datetime.strptime(data[4:], "%Y%m%d%H%M%S")
                    delta = now - file_date
                    if delta.days < int(delai_retention):
                        backup_ftp_files.append(reg.group())
                        #print(f"Moins de {delai_retention} jours. : ", reg.group()) # DEBUG
                        
                    else:
                        print(f"La Sauvegarde de plus de {delai_retention} jours va être supprimé du serveur {ftp_host}: ", reg.group())
                        ftp.delete(reg.group())
                        pass

        except ftplib.all_errors as e:
            print('FTP error :', e)

    return(backup_ftp_files)


# Chargement du fichier yaml et affectation en variables global
if len(sys.argv) == 1:
    print("Usage : script + yaml_file -> python3 auto_backup.py data_backup.yml")
else:
    data_file = sys.argv[1]
with open(data_file) as f:
    try:
        data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print("Ouverture YAML Error :", e)
globals().update(data)

#  //  MAIN PROGRAM // PROGRAMME PRINCIPAL //

# ##### ACTIONS SUR LE SERVEUR WORDPRESS ###### #

# Définition du nom de la sauvegarde du jour pour les fichiers et la base de donnée
nom_backup_file = nom(backup_type[0], base_name)
nom_backup_base = nom(backup_type[1], base_name)

# Sauvegarde de la base de donnée Wordpress , utilisation du fichier protégé .my.cnf pour se connecter
os.system(f"mysqldump -h localhost -u {nom_user_base} --databases {base_name} > /tmp/backup.sql")

# Utilisation du module tarfile pour créer l' archive de la base wordpress 
# Dans un fichier temporaire /tmp/backup.sql qui est ensuite supprimé
tar = tarfile.open(dir_backup + nom_backup_base, 'w:gz')
tar.add('/tmp/backup.sql')
tar.close()
os.remove('/tmp/backup.sql')

# Création du fichier de sauvegarde qui copie tous les fichiers du répertoire wordpress
# Ainsi que le fichier Virtualhost du serveur Apache
tar = tarfile.open(dir_backup + nom_backup_file, 'w:gz')
tar.add(dir_wordpress)
tar.add(dir_site_apache + virtual_host)
tar.close()


# Récupération de la liste des fichiers  de sauvegarde pour serveur local et FTP
backup_files = supp_old_backup(backup_type[0], base_name, dir_backup)
backup_bases = supp_old_backup(backup_type[1], base_name, dir_backup)

# ##### ACTIONS SUR LE SERVEUR FTP ###### #

# Récupération des informations de connexion du serveur ftp contenu dans le fichier protégé .netrc
try:
    netrc = netrc.netrc()
    auth_ftp = netrc.authenticators(ftp_host)
except FileNotFoundError:
    print('Warning : Fichier d\'identification FTP non présent. L\'accès au serveur impossible')
    sys.exit(2)

# Partie de connexion au serveur FTP et transfert des fichiers de sauvegarde 
with ftplib.FTP(host= ftp_host, user=auth_ftp[0], passwd=auth_ftp[2]) as ftp:
    try:
        print(ftp.getwelcome())
        ftp.cwd(dir_ftp)
        ftp.storbinary('STOR ' + nom_backup_file, open(dir_backup + nom_backup_file , 'rb'))
        ftp.storbinary('STOR ' + nom_backup_base, open(dir_backup + nom_backup_base , 'rb'))
        ftp.quit()
    except ftplib.all_errors as e:
        print('FTP erreur : ', e)

# Récupération de la liste des fichiers et Suppression du fichier de sauvegarde les plus ancien
ftp_files = supp_old_ftp_backup(backup_type[0], base_name)
ftp_bases = supp_old_ftp_backup(backup_type[1], base_name)

# Message de fin signalant la réussite de l'opération . Pour être tracé dans les logs
print(f" {nom_backup_file} a été transféré sur le serveur {ftp_host}")
print(f" {nom_backup_base} a été transféré sur le serveur {ftp_host}")

# Tests des résultats des répertoires   en cas besoins de DEBUGAGE. Listes obtenus par les fonctions 'supp_old_xx'
#print("WP FILES :\n", backup_files, len(backup_files))   # DEBUG
#print("WP BASES :\n", backup_bases, len(backup_bases))   # DEBUG

#print("FTP FILES :\n", ftp_files, len(ftp_files))   # DEBUG
#print("FTP BASES :\n", ftp_bases, len(ftp_bases))   # DEBUG




