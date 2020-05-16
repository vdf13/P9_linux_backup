#!/usr/bin/python3.7
# -*- coding: utf-8 -*-

# Victor De Faria 2020-04-27 2020-05-xx
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
    ''' Fonction qui génère un nom de fichier en fonction de la date et heure de la sauvegarde '''
    date = datetime.datetime.now()
    texte = f'backup-{base_name}-{texte}-{date.strftime("%Y-%m-%d-%H-%M")}.tar.gz'
    return texte


def supp_old_backup(texte, base_name, dir_back):
    '''
    Fonction qui récupère la liste des fichiers du répertoire backup
    et ne renvoie que ceux dont le nom contient 'backup'- expression régulière.
    Si 8 fichiers dans le répertoire, alors le plus ancien est supprimé.
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
                print(f"La Sauvegarde de plus de {delai_retention} jours va être supprimé du serveur {wp_host}: ", file)    # DEBUG
                os.remove(file)
            
    return(backup_files)    

def supp_old_ftp_backup(texte, base_name):
    '''
    Fonction qui récupère la liste des fichiers du répertoire de backup sur le serveur FTP 
    Supprime le plus ancien fichier de backup sur le serveur FTP
    Renvoie la liste des fichiers de sauvegarde après suppression
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


# Récupération de la liste des fichiers  de sauvegarde
backup_files = supp_old_backup(backup_type[0], base_name, dir_backup)
backup_bases = supp_old_backup(backup_type[1], base_name, dir_backup)

# ##### ACTIONS SUR LE SERVEUR FTP ###### #

# Récupération des informations de connexion du serveur ftp contenu dans le fichier protégé .netrc
netrc = netrc.netrc()
auth_ftp = netrc.authenticators(ftp_host)

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

# Récupération de la liste des fichiers et Suppression du fichier de sauvegarde le plus ancien
ftp_files = supp_old_ftp_backup(backup_type[0], base_name)
ftp_bases = supp_old_ftp_backup(backup_type[1], base_name)



# Tests des résultats des répertoires   en cas besoins de DEBUGAGE
#print("WP FILES :\n", backup_files, len(backup_files))   # DEBUG
#print("WP BASES :\n", backup_bases, len(backup_bases))   # DEBUG

#print("FTP FILES :\n", ftp_files, len(ftp_files))   # DEBUG
#print("FTP BASES :\n", ftp_bases, len(ftp_bases))   # DEBUG




