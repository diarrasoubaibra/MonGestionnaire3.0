import os
from flask import Flask, render_template, request, redirect, url_for,flash, session
import pymysql, string, random
from send_mail import envoicode
from flask_bcrypt import Bcrypt
import re
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import jsonify
from yallikaConfig import envoyer_sms_api


# Créer une instance de l'application Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')
# flash message
app.secret_key = 'message' 

# connexion à la base de donnée
conn = pymysql.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', ''),
    db=os.getenv('DB_NAME', 'dl_sion_compagnie'),
)
# Database connection using pymysql
# def get_db_connection():
#     return pymysql.connect(
#         host=os.getenv('DB_HOST', 'localhost'),
#         user=os.getenv('DB_USER', 'your_local_db_user'),
#         password=os.getenv('DB_PASSWORD', 'your_local_db_password'),
#         db=os.getenv('DB_NAME', 'dl_sion_compagnie'),
#         cursorclass=pymysql.cursors.DictCursor
#     )

# Initialiser l'extension Bcrypt pour le hachage des mots de passe
bcrypt = Bcrypt(app)


UPLOAD_FOLDER = 'static/image/upload'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# conn = get_db_connection()
cursor = conn.cursor()

# hashed_password = bcrypt.generate_password_hash('kra1234')
# print(hashed_password)


#  Exécutez la requête SQL en utilisant des paramètres pour éviter les injections SQL
#sql = "INSERT INTO administrateur (nom, prenom, telephone, email,login, mot_pass) VALUES (%s, %s, %s, %s, %s, %s)"
#values = ('Kra Adelphe', 'Adephe', '56545678', 'sidiksoum344@gmail.com', 'soum1234', hashed_password)

# # # Exécutez la requête SQL en utilisant des paramètres pour éviter les injections SQL
# sql = "INSERT INTO administrateur (nom, prenom, telephone, email,login, mot_pass) VALUES (%s, %s, %s, %s, %s, %s)"
# values = ('Kra', 'Adephe', '0759934211', 'adelphekra@gmail.com', 'kra1234', hashed_password)


# # Exécutez la requête avec les valeurs
# cursor.execute(sql, values)
# conn.commit()
# ===================================Admin espace ==============================

# Définir une route et la fonction associée

@app.route('/')
def accueil():
    # Rendre le template index.html
    return render_template('accueil.html')

@app.route('/login')
def login():
    # Rendre le template index.html
    return render_template('connexion/login.html')

@app.route('/code/')
def code():
    # Rendre le template index.html
    return render_template('connexion/code.html')

@app.route('/nouveau_mot/')
def nouveau_mot():
    # Rendre le template index.html
    return render_template('connexion/nouveau_mot.html')

@app.route('/recuperation/')
def recuperation():
    # Rendre le template index.html
    return render_template('connexion/recuperation.html')

# connexion de l'admin
@app.route('/admin/', methods=["POST", "GET"])
def adminIndex():
    if request.method == 'POST':
        username = request.form.get('login')
        password = request.form.get('password')
        if not (username and password):
            flash('Please fill all the fields', 'danger')
            return redirect('/admin/')
        else:
            cursor = conn.cursor()
            query = "SELECT * FROM administrateur WHERE login=%s"
            cursor.execute(query, (username,))
            admin = cursor.fetchone()
            cursor.close()
            if admin and bcrypt.check_password_hash(admin[6], password):
                session['admin_id'] = admin[0]
                session['admin_name'] = admin[1]
                # flash('Login Successfully', 'success')
                return redirect('/admin/dashboard')
            else:
                flash('Invalid Username or Password', 'danger')
                return redirect(url_for('adminIndex'))
    else:
        return render_template('admin/login.html')


@app.route('/admin/dashboard', methods=["POST", "GET"])
def base():
    if 'admin_id' in session:  # Vérifie si l'administrateur est connecté
        admin_id = session['admin_id']
        cursor = conn.cursor()

        # Récupérer les informations de l'administrateur en utilisant son ID
        cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
        infos_admin = cursor.fetchone()
        filename = infos_admin[7].decode('utf-8')

        # Récupérer le nombre total de ventes actives
        cursor.execute('SELECT count(*) FROM vente WHERE vente.is_active = TRUE')
        total_ventes = cursor.fetchone()[0]

        # Récupérer le montant total du stock
        cursor.execute('SELECT SUM(stock * prix) FROM produit')
        montantstock = cursor.fetchone()[0]

        # Récupérer le nombre total de commandes en cours
        cursor.execute('SELECT count(*) FROM commande WHERE statut = %s', ('En cours',))
        total_commande = cursor.fetchone()[0]

        # Récupérer le nombre total de clients
        cursor.execute('SELECT count(*) FROM client')
        total_client = cursor.fetchone()[0]

        # Récupérer le nombre total de fournisseurs
        cursor.execute('SELECT count(*) FROM fournisseur')
        fournisseur = cursor.fetchone()[0]

        # Récupérer le stock total
        cursor.execute('SELECT SUM(stock) FROM produit')
        stocktotal = cursor.fetchone()[0]

        # Récupérer le chiffre d'affaires total des ventes actives
        cursor.execute('SELECT SUM(montant) FROM vente WHERE vente.is_active = TRUE')
        total_CA = cursor.fetchone()[0]

        # Récupérer les meilleurs produits
        cursor.execute('''
            SELECT produit.image, produit.nom_produit, SUM(vente.quantite) AS total_quantite 
            FROM vente 
            JOIN produit ON produit.id_produit = vente.id_produit 
            WHERE vente.is_active = TRUE 
            GROUP BY produit.image, produit.nom_produit 
            ORDER BY total_quantite DESC 
            LIMIT 100
        ''')
        meilleurs = cursor.fetchall()

        # Transformer les meilleurs produits en une liste de dictionnaires
        products = []
        for produit in meilleurs:
            image = produit[0].decode('utf-8') if isinstance(produit[0], bytes) else produit[0]
            nom_produit = produit[1]
            total_quantite = produit[2]
            products.append({'image': image, 'nom_produit': nom_produit, 'total_quantite': total_quantite})

        # Récupérer les détails des ventes pour le tableau de bord
        cursor.execute('''
            SELECT date_vente, client.nom_prenoms, vente.statut, montant, id_vente
            FROM vente
            JOIN client ON vente.id_client = client.id_client
            ORDER BY date_vente DESC
        ''')
        dash = cursor.fetchall()

        # Calculer le bénéfice
        if montantstock and total_CA:
            benefice = total_CA - montantstock
        else:
            benefice = 0

        # Fermer le curseur
        cursor.close()

        return render_template('admin/dashboard.html', filename=filename, total_ventes=total_ventes,
                               total_commande=total_commande, total_client=total_client,
                               total_CA=total_CA, products=products, dash=dash,
                               montantstock=montantstock, fournisseur=fournisseur,
                               stocktotal=stocktotal, benefice=benefice)
    else:
        flash('Please login first', 'danger')
        return redirect('/admin')


# admin logout
@app.route('/admin/logout')
def adminLogout():
    if 'admin_id' in session:
        session.pop('admin_id')
        session.pop('admin_name')
        session.pop('_flashes', None)
        # flash('You have been logged out', 'success')
    return redirect('/admin/')


# ================================Admin Mot de passe oublié================================

@app.route('/forgot_password', methods=["GET", "POST"])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please provide your email address', 'danger')
            return redirect('/recuperation/')

        cursor = conn.cursor()
        query = "SELECT * FROM administrateur WHERE email=%s"
        cursor.execute(query, (email,))
        admin = cursor.fetchone()
        cursor.close()

        if not admin:
            flash('This email is not registered', 'danger')
            return redirect('/recuperation/')
        code = ''.join(random.choices(string.digits, k=5))
        session['code'] = code
        session['email'] = email
        envoicode(code, email)
        flash('A verification code has been sent to your email', 'success')
        return redirect('/code/')

    return redirect('/recuperation/')

@app.route('/forgot_password_code', methods=["GET", "POST"])
def forgot_password_code():
    if request.method == 'POST':
        code = session.get('code')
        email = session.get('email')
        if not (code and email):
            flash('Invalid code or email', 'danger')
            return redirect('/forgot_password')

        codesaisir = request.form.get("code")
        if codesaisir == code:
            return redirect('/nouveau_mot')
        else:
            flash('Incorrect verification code', 'danger')
            return redirect('/code/')

    return redirect('/code/')


@app.route('/change_password', methods=["GET", "POST"])
def change_password():
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = session.get('email')

        if not (password and confirm_password):
            flash('Please fill all the fields', 'danger')
            return redirect('/change_password')

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect('/change_password')

        cursor = conn.cursor()
        mot_pass = bcrypt.generate_password_hash(password).decode('utf-8')
        query = "UPDATE administrateur SET mot_pass=%s WHERE email=%s"
        cursor.execute(query, (mot_pass, email))
        conn.commit()
        cursor.close()

        flash('Password updated successfully', 'success')
        session.pop('email', None)
        session.pop('code', None)
        return redirect('/')
        
    return render_template('connexion/nouveau_mot.html')
# ==========================Admin update=======================================

@app.route('/admin/modifier_profil', methods=['GET', 'POST'])
def modifier_profil():
    if 'admin_id' not in session:
        flash('Veuillez vous connecter d\'abord.', 'danger')
        return redirect(url_for('adminIndex'))

    admin_id = session['admin_id']
    cursor = conn.cursor()

    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        tel = request.form['tel']
        email = request.form['email']
        image = request.files['image']

        # Sécurisez le nom du fichier
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        # Mettez à jour les informations dans la base de données
        cursor.execute('UPDATE administrateur SET nom = %s, prenom = %s, telephone = %s, email = %s, image = %s WHERE id_admin = %s',
                       (nom, prenom, tel, email, filename, admin_id))
        conn.commit()

        flash('Profil mis à jour avec succès.', 'success')
        return redirect(url_for('profil'))

    # Récupérez les informations actuelles de l'administrateur pour les afficher dans le formulaire
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    admin_info = cursor.fetchone()
    cursor.close()

    return render_template('profil.html', admin_info=admin_info)

@app.route('/admin/modifier_access', methods=['GET', 'POST'])
def modifier_access():
    if 'admin_id' not in session:
        flash('Veuillez vous connecter d\'abord.', 'danger')
        return redirect(url_for('adminIndex'))

    admin_id = session['admin_id']
    cursor = conn.cursor()

    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        confmotpass = request.form['confmotpass']

        # Vérifiez que les mots de passe correspondent
        if password != confmotpass:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('modifier_access'))

        # Hash du mot de passe pour la sécurité
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Mettez à jour le login et le mot de passe dans la base de données
        cursor.execute('UPDATE administrateur SET login = %s, mot_pass = %s WHERE id_admin = %s',
                       (login, hashed_password, admin_id))
        conn.commit()

        flash('Les informations de connexion ont été mises à jour avec succès.', 'success')
        return redirect(url_for('profil'))

    # Récupérez les informations actuelles de l'administrateur pour les afficher dans le formulaire
    cursor.execute('SELECT login FROM administrateur WHERE id_admin = %s', (admin_id,))
    admin_login = cursor.fetchone()[0]
    cursor.close()

    admin_id = session['admin_id']
    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    return render_template('profil.html', admin_login=admin_login,filename=filename)


# ==========================Gestion des membres========================
@app.route('/admin/ajouter_membre', methods=['GET', 'POST'])
def ajouter_membre():
    utilisateur = None
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        mot_pass = request.form['password']
        telephone = request.form['tel']
        login = request.form['login']
        poste = request.form['poste']
        photo = request.files['image']  

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM utilisateur WHERE email = %s", (email,))
        utilisateur = cursor.fetchone()

        if utilisateur:
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('ajouter_membre'))

        if mot_pass != request.form['confmotpass']:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('ajouter_membre'))

        mot_pass_clair = mot_pass
        mot_pass = bcrypt.generate_password_hash(mot_pass).decode('utf-8')

        filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cursor.execute("INSERT INTO utilisateur (nom, prenom,poste,telephone, email, login, mot_pass,image,mot_pass_clair) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                       (nom, prenom, poste,telephone,email,login, mot_pass, filename,mot_pass_clair))
        conn.commit()

        cursor.execute("SELECT * FROM utilisateur WHERE email = %s", (email,))
        utilisateurs = cursor.fetchone()
        cursor.close()
        
        # flash('Nouveau membre ajouté avec succès.', 'success')
        
        return redirect('/admin/equipe/')
 
    return redirect('/admin/equipe/')

@app.route('/admin/equipe/')
def equipe():
    # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))

    admin_id = session['admin_id']

    # Récupérer les informations des utilisateurs
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM utilisateur")
    utilisateurs = cursor.fetchall()
    cursor.close()

    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    cursor.close()

    filename = infos_admin[7].decode('utf-8')

    return render_template('membres/equipe.html', utilisateurs=utilisateurs, filename=filename)


@app.route('/modifier_membre/<int:id_utilisateur>', methods=['POST', 'GET'])
def modifier_membre(id_utilisateur):
    admin_id = session['admin_id']
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM utilisateur WHERE id_utilisateur = %s", (id_utilisateur,))
    membre = cursor.fetchone()
    image_actuelle = membre[8].decode('utf-8') if membre[8] else None
    cursor.close()

    if membre is None:
        flash('Utilisateur non trouvé.', 'danger')
        return redirect(url_for('equipe'))

    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenommodif']
        poste = request.form['postemodif']
        telephone = request.form['tel']
        email = request.form['email']
        login = request.form['login']
        mot_pass = request.form['password']
        confmotpass = request.form['confmotpass']
        photo = request.files['image']

        if email != membre[5]:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM utilisateur WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Cet email est déjà utilisé.', 'danger')
                return redirect(url_for('modifier_membre', id_utilisateur=id_utilisateur))

        if mot_pass != confmotpass:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('modifier_membre', id_utilisateur=id_utilisateur))

        mot_pass_clair = mot_pass
        mot_pass = bcrypt.generate_password_hash(mot_pass).decode('utf-8')

        if photo and photo.filename != '':
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = image_actuelle

        cursor = conn.cursor()
        cursor.execute("UPDATE utilisateur SET nom = %s, prenom = %s, poste = %s, telephone = %s, email = %s, login = %s, mot_pass = %s, image = %s, mot_pass_clair = %s WHERE id_utilisateur = %s",
                       (nom, prenom, poste, telephone, email, login, mot_pass, filename,mot_pass_clair, id_utilisateur))
        conn.commit()
        cursor.close()
        flash('Informations du membre mises à jour avec succès.', 'success')
        return redirect(url_for('equipe'))

    return render_template('membres/modifier_membre.html', membre=membre, filename=filename, image_actuelle=image_actuelle, id_utilisateur=id_utilisateur)

@app.route('/userlogin', methods=['GET', 'POST'])
def userLogin():
    if request.method == 'POST':
        email = request.form.get('email')
        print ('Email: %s' % email)
        mot_pass = request.form.get('password')
        print ('Password: %s' % mot_pass)

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM utilisateur WHERE email = %s", (email,))
        utilisateur = cursor.fetchone()

        if utilisateur and bcrypt.check_password_hash(utilisateur[7], mot_pass):
            # Si les informations sont correctes, l'utilisateur est connecté
            session['logged_in'] = True
            session['utilisateur_id'] = utilisateur[0]
            session['email'] = email
            session['nom'] = utilisateur[1]
            session['poste'] = utilisateur[3]  # Poste de l'utilisateur
            return redirect(url_for('userDashboard'))

        else:
            flash('Email ou mot de passe incorrect.', 'danger')

    return render_template('connexion/userlogin.html')

@app.route('/userlogout')
def userLogout():
    session.pop('user_logged_in', None)
    session.pop('utilisateur_id', None)
    session.pop('user_email', None)
    session.pop('user_nom', None)
    session.pop('user_poste', None)
    return redirect(url_for('userLogin'))




#########Session vendeur###############################################

@app.route('/vendeur/profil/')
def profil_vendeur():
    # Vérifier si l'administrateur est connecté
    if 'utilisateur_id' not in session:
        flash('Veuillez vous connecter d\'abord.', 'danger')
        return redirect(url_for('userLogin'))

    # Récupérer l'ID de l'administrateur depuis la session
    utilisateur_id = session['utilisateur_id']

    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
    infos_membre = cursor.fetchone()
    filename = infos_membre[8].decode('utf-8')  # Convertir bytes en str
    conn.commit()
    cursor.close()
    return render_template('membres/vendeur/profil_vendeur.html',infos_membre=infos_membre,filename=filename)

@app.route('/dashboard/vendeur')
def dashboard_vendeur():
    if 'utilisateur_id' in session and session.get('poste') == 'vendeur':  # Vérifiez que l'utilisateur est un vendeur
        utilisateur_id = session['utilisateur_id']
        cursor = conn.cursor()

        # Récupérer les informations du vendeur connecté
        cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
        infos_membre = cursor.fetchone()
        filename = infos_membre[8].decode('utf-8')

        # Total des ventes
        cursor.execute('SELECT count(*) FROM vente WHERE id_utilisateur = %s', (utilisateur_id,))
        total_ventes = cursor.fetchone()[0]

        # Total des commandes
        cursor.execute("SELECT count(*) FROM commande WHERE  statut='En cours' and id_utilisateur = %s", (utilisateur_id,))
        total_commande = cursor.fetchone()[0]

        # Total des clients
        cursor.execute('SELECT count(*) FROM client')
        total_client = cursor.fetchone()[0]

        # Nombre de ventes retournées
        cursor.execute('SELECT sum(montant) FROM vente WHERE is_active =TRUE AND id_utilisateur = %s', (utilisateur_id,))
        retourne = cursor.fetchone()[0]

        # Meilleurs produits
        cursor.execute('SELECT produit.image, produit.nom_produit, SUM(vente.quantite) AS total_quantite FROM vente INNER JOIN produit ON produit.id_produit = vente.id_produit WHERE vente.id_utilisateur = %s GROUP BY produit.nom_produit ORDER BY total_quantite DESC LIMIT 20', (utilisateur_id,))
        meilleurs = cursor.fetchall()

        products = []
        for produit in meilleurs:
            image = produit[0].decode('utf-8') if isinstance(produit[0], bytes) else produit[0]
            nom_produit = produit[1]
            total_quantite = produit[2]
            products.append({'image': image, 'nom_produit': nom_produit, 'total_quantite': total_quantite})

        # Dernières ventes
        cursor.execute('SELECT date_vente, client.nom_prenoms, vente.statut, montant, id_vente FROM vente JOIN client ON vente.id_client = client.id_client WHERE vente.id_utilisateur = %s ORDER BY date_vente DESC', (utilisateur_id,))
        dash = cursor.fetchall()

        # Fermer le curseur et la connexion après avoir terminé toutes les opérations
        cursor.close()

        return render_template('membres/vendeur/dashboard_vendeur.html', total_ventes=total_ventes, total_commande=total_commande, total_client=total_client, retourne=retourne, products=products, dash=dash, filename=filename)
    else:
        flash('Veuillez vous connecter d\'abord.', 'danger')
        return redirect('/userlogin')


@app.route('/vendeur/client/', methods=["post", "get"])
def vendeur_client():
    # Vérifier si l'administrateur est connecté
    if 'utilisateur_id' not in session:
        flash('Veuillez vous connecter d\'abord.', 'danger')
        return redirect(url_for('userLogin'))
    if request.method == 'POST':
        nom = request.form['nom']
        telephone = request.form['tel']
        email = request.form['email']
        adresse = request.form['adresse']

        # Ajout automatique du préfixe +225 si nécessaire et validation du numéro
        telephone = '225' + telephone.lstrip('225')
        if len(telephone) != 13 or not telephone[3:].isdigit() or not (telephone[3:5] in ['07', '05', '01']):
            flash('Le numéro de téléphone doit être valide et contenir 14 chiffres y compris le préfixe 225.', 'danger')
            return redirect(url_for("vendeur_client"))

        # Vérifier si le numéro de téléphone est unique
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM client WHERE telephone = %s', (telephone,))
        if cursor.fetchone():
            flash('Ce numéro de téléphone est déjà utilisé.', 'danger')
            return redirect(url_for("vendeur_client"))

        # Vérification de l'unicité de l'email
        cursor.execute("SELECT * FROM client WHERE email = %s AND id_client != %s", (email, id))
        if cursor.fetchone():
            flash('Cet email est déjà utilisé par un autre client.', 'danger')
            return redirect(url_for("vendeur_client"))

        # Insérer le nouveau client
        cursor.execute('INSERT INTO client (nom_prenoms,telephone,email,adresse) VALUES (%s, %s, %s, %s)',
                       (nom, telephone, email, adresse))
        conn.commit()
        cursor.close()
        flash('Client ajouté avec succès', 'success')
        return redirect(url_for("vendeur_client"))  # Redirection vers la même page clients après ajout
    else:
        # Récupération des éléments de la table client
        curso = conn.cursor()
        curso.execute("SELECT * FROM client")
        resultat = curso.fetchall()
        curso.close()
        utilisateur_id = session['utilisateur_id']

        cursor = conn.cursor()
        # Récupérer les informations de l'administrateur en utilisant son ID
        cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
        infos_membre = cursor.fetchone()
        filename = infos_membre[8].decode('utf-8')  # Convertir bytes en str
        conn.commit()
        cursor.close()
        return render_template("membres/vendeur/vendeur_client.html", resultat=resultat,filename=filename)

@app.route('/vendeur/ventes/', methods=["POST", "GET"])
def vendeur_ventes():
    # Vérifiez si l'utilisateur est connecté et s'il est un vendeur ou un administrateur
    if ('utilisateur_id' in session and session.get('poste') == 'vendeur') or ('admin_id' in session):
        # Déterminez si l'utilisateur est un vendeur ou un administrateur
        if 'utilisateur_id' in session:
            utilisateur_id = session['utilisateur_id']
            role = 'vendeur'
        else:
            utilisateur_id = session['admin_id']
            role = 'admin'

        print(f"ID {role} récupéré : {utilisateur_id}")
        cursor = conn.cursor()

        # Récupérer les informations du vendeur connecté
        cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
        infos_membre = cursor.fetchone()
        filename = infos_membre[8].decode('utf-8')

        # Récupérer les produits et les clients
        cursor.execute("SELECT id_produit, nom_produit, categorie, prix FROM produit")
        produits = cursor.fetchall()

        cursor.execute("SELECT id_client, nom_prenoms FROM client")
        clients = cursor.fetchall()

        if request.method == 'POST':
            client_id = request.form.get("client")
            produit_id = request.form.get("produit")
            quantite = int(request.form.get("nombre"))
            prix_vente = int(request.form.get("prix_vente"))

            cursor.execute("SELECT stock FROM produit WHERE id_produit = %s", (produit_id,))
            quantite_en_stock = cursor.fetchone()[0]

            if quantite > quantite_en_stock:
                flash('Quantité demandée excède le stock disponible. Vente annulée.', 'danger')
                return redirect(url_for('vendeur_ventes'))

            if not client_id:
                nom = request.form.get("nom")
                tel = request.form.get("tel")
                email = request.form.get("email")
                adresse = request.form.get("adresse")
                cursor.execute(
                    'INSERT INTO client (nom_prenoms, telephone, email, adresse, id_utilisateur) VALUES (%s, %s, %s, %s, %s)',
                    (nom, tel, email, adresse, utilisateur_id))
                conn.commit()
                client_id = cursor.lastrowid

            if produit_id and quantite and prix_vente:
                montant = prix_vente * quantite
                date_aujourdhui = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # Vérifiez si l'utilisateur est un admin pour utiliser l'id_admin
                if role == 'admin':
                    cursor.execute(
                        'INSERT INTO vente (id_client, id_produit, quantite, montant, prix_vente, date_vente, statut, id_admin) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                        (client_id, produit_id, quantite, montant, prix_vente, date_aujourdhui, "Vendu", utilisateur_id))
                else:
                    cursor.execute(
                        'INSERT INTO vente (id_client, id_produit, quantite, montant, prix_vente, date_vente, statut, id_utilisateur) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                        (client_id, produit_id, quantite, montant, prix_vente, date_aujourdhui, "Vendu", utilisateur_id))
                conn.commit()
                flash('Vente ajoutée avec succès', 'success')
            else:
                flash('Informations de vente manquantes ou incorrectes', 'danger')

        # Récupérer les ventes du vendeur connecté
        cursor.execute(
            "SELECT id_vente, date_vente, client.nom_prenoms, produit.nom_produit, vente.statut FROM vente JOIN client ON vente.id_client = client.id_client JOIN produit ON vente.id_produit = produit.id_produit WHERE vente.id_utilisateur = %s ORDER BY date_vente DESC",
            (utilisateur_id,))
        resultat = cursor.fetchall()

        # Fermer le curseur et la connexion après avoir terminé toutes les opérations
        cursor.close()

        curso = conn.cursor()
        curso.execute(
            "select count(*) from vente where id_utilisateur = %s and is_active =TRUE", (utilisateur_id,))
        ventetotal = curso.fetchone()
        curso.close()

        date_actuelle = datetime.now().strftime('%Y-%m-%d')

        curso = conn.cursor()
        curso.execute(
            "select count(*) from vente WHERE DATE(date_vente) = %s and id_utilisateur = %s and is_active =TRUE", (date_actuelle,utilisateur_id,))
        ventejour = curso.fetchone()
        curso.close()

        curso = conn.cursor()
        curso.execute(
            "SELECT SUM(montant) FROM vente WHERE DATE(date_vente) = %s and id_utilisateur = %s and is_active =TRUE ", (date_actuelle,utilisateur_id,))
        montanttotal = curso.fetchone()
        curso.close()

        return render_template("membres/vendeur/vendeur_vente.html", produits=produits, clients=clients,
                               resultat=resultat, filename=filename,ventejour=ventejour,ventetotal=ventetotal,montanttotal=montanttotal)
    else:
        flash('Veuillez vous connecter en tant que vendeur ou administrateur.', 'danger')
        return redirect('/userlogin')


@app.route('/vendeur/commande/', methods=["POST", "GET"])
def vendeur_commande():
    # Vérifiez si l'utilisateur est connecté en tant que vendeur
    if 'utilisateur_id' not in session or session.get('poste') != 'vendeur':
        flash('Veuillez vous connecter en tant que vendeur.', 'danger')
        return redirect(url_for('userLogin'))

    utilisateur_id = session['utilisateur_id']

    # Récupérer les produits disponibles
    cursor = conn.cursor()
    cursor.execute("SELECT id_produit, nom_produit, categorie, prix FROM produit")
    produits = cursor.fetchall()
    cursor.close()

    # Récupérer les clients disponibles
    cursor = conn.cursor()
    cursor.execute("SELECT id_client, nom_prenoms FROM client")
    clients = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        produit_id = request.form["produit"]
        quantite = int(request.form["nombre"])  # Convertir en entier pour la manipulation
        id_client = request.form["client"]
        prix_vente = int(request.form["prix"])

        montant = quantite * prix_vente
        date_aujourdhui = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor = conn.cursor()
        try:
            # Enregistrement de l'achat dans la base de données avec la date d'aujourd'hui
            cursor.execute(
                'INSERT INTO commande (id_client, id_produit, Quantite, prix_vente, Montant, date_commande, statut, id_utilisateur) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (id_client, produit_id, quantite, prix_vente, montant, date_aujourdhui, "En cours", utilisateur_id)
            )
            conn.commit()
            flash('Achat ajouté avec succès', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Erreur lors de l\'ajout de l\'achat : {str(e)}', 'danger')
        finally:
            cursor.close()
        return redirect(url_for('vendeur_commande'))

    # Récupérer les commandes de ce vendeur
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id_commande, date_commande, commande.statut, client.nom_prenoms, produit.nom_produit "
        "FROM commande "
        "JOIN client ON commande.id_client = client.id_client "
        "JOIN produit ON commande.id_produit = produit.id_produit "
        "WHERE commande.id_utilisateur = %s", (utilisateur_id,)
    )
    resultat = cursor.fetchall()
    cursor.close()

    # Récupérer les informations du vendeur connecté
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
    infos_membre = cursor.fetchone()
    filename = infos_membre[8].decode('utf-8')  # Convertir bytes en str
    cursor.close()

    date_actuelle = datetime.now().strftime('%Y-%m-%d')

    curso = conn.cursor()
    curso.execute(
        "select count(*) from commande WHERE DATE(date_commande) = %s and id_utilisateur= %s ", (date_actuelle,utilisateur_id,))
    commandejour = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select count(*) from commande WHERE statut='vendu' and id_utilisateur= %s", (utilisateur_id,))
    commandelivre = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select sum(montant) from commande where statut='En cours' and id_utilisateur= %s", (utilisateur_id,))
    montantcommande = curso.fetchone()
    curso.close()

    return render_template('membres/vendeur/vendeur_commande.html', produits=produits, clients=clients, resultat=resultat, filename=filename,
                           montantcommande=montantcommande,commandelivre=commandelivre,commandejour=commandejour)

@app.route('/vendeur/modifier_profil', methods=['GET', 'POST'])
def modifier_profil_membre():
    if 'utilisateur_id' not in session:
        flash('Veuillez vous connecter d\'abord.', 'danger')
        return redirect(url_for('userLogin'))

    utilisateur_id = session['utilisateur_id']
    cursor = conn.cursor()

    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        tel = request.form['tel']
        email = request.form['email']
        image = request.files['image']

        # Sécurisez le nom du fichier
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        # Mettez à jour les informations dans la base de données
        cursor.execute('UPDATE utilisateur SET nom = %s, prenom = %s, telephone = %s, email = %s, image = %s WHERE id_utilisateur = %s',
                       (nom, prenom, tel, email, filename, utilisateur_id))
        conn.commit()

        flash('Profil mis à jour avec succès.', 'success')
        return redirect(url_for('profil_vendeur'))

    # Récupérez les informations actuelles de l'administrateur pour les afficher dans le formulaire
    cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
    membre_info = cursor.fetchone()
    cursor.close()

    return render_template('profil_vendeur.html', membre_info=membre_info)

@app.route('/vendeur/vendeur_modifier_client/<int:id>', methods=['POST', 'GET'])
def vendeur_modifier_client(id):
    utilisateur_id = session['utilisateur_id']
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
    infos_membre = cursor.fetchone()
    filename = infos_membre[8].decode('utf-8')

    cursor.execute("SELECT * from client where id_client=%s", (id,))
    client = cursor.fetchone()
    cursor.close()

    if request.method == 'POST':
        nom = request.form['nom']
        telephone = request.form['tel']
        email = request.form['email']
        adresse = request.form['adresse']

        # Ajout automatique du préfixe +225 si nécessaire et validation du numéro
        telephone = '225' + telephone.lstrip('225')
        if len(telephone) != 13 or not telephone[3:].isdigit() or not (telephone[3:5] in ['07', '05', '01']):
            flash('Le numéro de téléphone doit être valide et contenir 14 chiffres y compris le préfixe 225.', 'danger')
            return redirect(url_for('vendeur_modifier_client', id=id))

        # Vérification de l'unicité du numéro de téléphone
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM client WHERE telephone = %s AND id_client != %s", (telephone, id))
        if cursor.fetchone():
            flash('Ce numéro de téléphone est déjà utilisé par un autre client.', 'danger')
            return redirect(url_for('vendeur_modifier_client', id=id))

        # Vérification de l'unicité de l'email
        cursor.execute("SELECT * FROM client WHERE email = %s AND id_client != %s", (email, id))
        if cursor.fetchone():
            flash('Cet email est déjà utilisé par un autre client.', 'danger')
            return redirect(url_for('vendeur_modifier_client', id=id))

        # Mise à jour des informations du client
        cursor.execute("""
            UPDATE client SET nom_prenoms = %s, telephone = %s, email = %s, adresse = %s
            WHERE id_client = %s
            """, (nom, telephone, email, adresse, id))
        conn.commit()
        cursor.close()
        flash('Client mise à jour avec succès.', 'danger')
        return redirect(url_for('vendeur_client'))

    return render_template('membres/vendeur/vendeur_modifier_client.html', resultat=client, filename=filename)

#Ssession vendeur###############################################


#Session Gestionnaire###############################################

@app.route('/gestionnaire/profil/')
def profil_gestionnaire():
    # Vérifier si l'administrateur est connecté
    if 'utilisateur_id' not in session:
        flash('Veuillez vous connecter d\'abord.', 'danger')
        return redirect(url_for('userLogin'))

    # Récupérer l'ID de l'administrateur depuis la session
    utilisateur_id = session['utilisateur_id']

    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
    infos_membre = cursor.fetchone()
    filename = infos_membre[8].decode('utf-8')  # Convertir bytes en str
    conn.commit()
    cursor.close()
    return render_template('/membres/Gestionnaire/profil_gestionnaire.html',filename=filename,infos_membre=infos_membre)

@app.route('/gestionnaire/modifier_profil', methods=['GET', 'POST'])
def modifier_profil_gestion():
    if 'utilisateur_id' not in session:
        flash('Veuillez vous connecter d\'abord.', 'danger')
        return redirect(url_for('userLogin'))

    utilisateur_id = session['utilisateur_id']
    cursor = conn.cursor()

    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        tel = request.form['tel']
        email = request.form['email']
        image = request.files['image']

        # Sécurisez le nom du fichier
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        # Mettez à jour les informations dans la base de données
        cursor.execute('UPDATE utilisateur SET nom = %s, prenom = %s, telephone = %s, email = %s, image = %s WHERE id_utilisateur = %s',
                       (nom, prenom, tel, email, filename, utilisateur_id))
        conn.commit()

        flash('Profil mis à jour avec succès.', 'success')
        return redirect(url_for('profil_gestionnaire'))

    # Récupérez les informations actuelles de l'administrateur pour les afficher dans le formulaire
    cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
    membre_info = cursor.fetchone()
    cursor.close()

    return render_template('/membres/Gestionnaire/profil_vendeur.html', membre_info=membre_info)

@app.route('/dashboard/gestionnaire', methods=['GET', 'POST'])
def dashboard_gestionnaire():
    if 'utilisateur_id' in session and session.get('poste') == 'gestionnaire':  # Vérifiez que l'utilisateur est un gestionnaire
        utilisateur_id = session['utilisateur_id']
        cursor = conn.cursor()
        cursor.execute("SELECT id_produit, nom_produit, categorie, prix FROM produit")
        produits = cursor.fetchall()
        cursor.close()

        if request.method == 'POST':
            produit_id = request.form["produit"]
            quantite = int(request.form["nombre"])
            date_aujourdhui = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor = conn.cursor()
            cursor.execute('INSERT INTO stock (ID_Produit, Quantite, date, id_gestionnaire) VALUES (%s, %s, %s, %s)', (produit_id, quantite, date_aujourdhui, utilisateur_id))
            cursor.execute('UPDATE produit SET stock = stock + %s WHERE id_produit = %s', (quantite, produit_id))
            conn.commit()
            cursor.close()

            flash('Stock ajouté avec succès', 'success')
            return redirect(url_for('dashboard_gestionnaire'))
        cursor = conn.cursor()
        cursor.execute("select produit.nom_produit, produit.categorie, quantite, date, id_stock FROM stock join produit on stock.id_produit = produit.id_produit WHERE stock.id_utilisateur = %s", (utilisateur_id,))
        resultat = cursor.fetchall()
        cursor.close()

        cursor = conn.cursor()
        cursor.execute("select nom_produit, categorie, stock, stock_min FROM produit")
        resultat1 = cursor.fetchall()
        cursor.close()

        curso = conn.cursor()
        curso.execute(
            "select sum(stock) from produit")
        stocktotal = curso.fetchone()
        curso.close()

        curso = conn.cursor()
        curso.execute(
            "select count(*) from produit WHERE stock < 20")
        stockfaible = curso.fetchone()
        curso.close()

        curso = conn.cursor()
        curso.execute(
            "SELECT SUM(stock * prix) FROM produit")
        montantstock = curso.fetchone()
        curso.close()

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
        infos_membre = cursor.fetchone()
        filename = infos_membre[8].decode('utf-8')

        return render_template('membres/gestionnaire/dashboard_gestionnaire.html', produits=produits, resultat=resultat, resultat1=resultat1, filename=filename,
                               stockfaible=stockfaible,montantstock=montantstock,stocktotal=stocktotal)
    else:
        flash('Please login first', 'danger')
        return redirect('/userlogin')

@app.route('/gestionnaire/client/', methods=["post", "get"])
def gestion_client():
    if request.method == 'POST':
        nom = request.form['nom']
        telephone = request.form['tel']
        email = request.form['email']
        adresse = request.form['adresse']
        statut = request.form['statut']

        # Ajout automatique du préfixe +225 si nécessaire et validation du numéro
        telephone = '225' + telephone.lstrip('225')
        if len(telephone) != 13 or not telephone[3:].isdigit() or not (telephone[3:5] in ['07', '05', '01']):
            flash('Le numéro de téléphone doit être valide et contenir 14 chiffres y compris le préfixe 225.', 'danger')
            return redirect(url_for("gestion_client"))

        # Vérifier si le numéro de téléphone est unique
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM client WHERE telephone = %s', (telephone,))
        if cursor.fetchone():
            flash('Ce numéro de téléphone est déjà utilisé.', 'danger')
            return redirect(url_for("gestion_client"))

        # Vérification de l'unicité de l'email
        cursor.execute("SELECT * FROM client WHERE email = %s AND id_client != %s", (email, id))
        if cursor.fetchone():
            flash('Cet email est déjà utilisé par un autre client.', 'danger')
            return redirect(url_for("gestion_client"))

        # Insérer le nouveau client
        cursor.execute('INSERT INTO client (nom_prenoms,telephone,email,adresse,statut) VALUES (%s, %s, %s, %s, %s)',
                       (nom, telephone, email, adresse,statut))
        conn.commit()
        cursor.close()
        flash('Client ajouté avec succès', 'success')
        return redirect(url_for("gestion_client"))  # Redirection vers la même page clients après ajout
    else:
        # Récupération des éléments de la table client
        curso = conn.cursor()
        curso.execute("SELECT * FROM client")
        resultat = curso.fetchall()
        curso.close()
        utilisateur_id = session['utilisateur_id']

        cursor = conn.cursor()
        # Récupérer les informations de l'administrateur en utilisant son ID
        cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
        infos_membre = cursor.fetchone()
        filename = infos_membre[8].decode('utf-8')  # Convertir bytes en str
        conn.commit()
        cursor.close()
        return render_template("membres/gestionnaire/gestion_client.html", resultat=resultat,filename=filename)


@app.route('/gestionnaire/Produit/', methods=["post", "get"])
def gestion_produit():
    if request.method == 'POST':
        nom = request.form['nom']
        categorie = request.form['categorie']
        designation = request.form['description']
        prix = request.form['prix']
        image = request.files['image']
        stock_min= request.form['nombre']
        stock=request.form['stock']

        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        curso = conn.cursor()
        curso.execute('INSERT INTO produit(nom_produit,categorie,prix,stock,stock_min,designation,image) VALUES (%s, %s, %s ,%s,%s, %s, %s)',
                      (nom,categorie,prix,stock,stock_min,designation,filename))
        conn.commit()
        curso.close()
        flash('Produit ajouté avec succès', 'success')
        return redirect(url_for("gestion_produit"))  # Redirection vers la même page Produit après ajout
    else:
        # Récupération des éléments de la table produit
        curso = conn.cursor()
        curso.execute("SELECT * FROM produit")
        resultat = curso.fetchall()
        curso.close()

        utilisateur_id = session['utilisateur_id']
        cursor = conn.cursor()
        # Récupérer les informations de l'administrateur en utilisant son ID
        cursor.execute('SELECT * FROM  utilisateur WHERE id_utilisateur = %s', ( utilisateur_id,))
        infos_admin = cursor.fetchone()
        filename = infos_admin[8].decode('utf-8')

        return render_template("membres/Gestionnaire/gestion_produit.html", resultat=resultat,filename=filename)
@app.route('/gestionnaire/commande/', methods=["POST", "GET"])
def gestion_commande():
    cursor = conn.cursor()
    cursor.execute("SELECT id_produit, nom_produit, categorie, prix FROM produit")
    produits = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("SELECT id_client, nom_prenoms FROM client")
    clients = cursor.fetchall()
    cursor.close()
    if request.method == 'POST':
        produit_id = request.form["produit"]
        quantite = int(request.form["nombre"])  # Convertir en entier pour la manipulation
        id_client = request.form["client"]
        prix_vente = int(request.form["prix"])

        montant = quantite*prix_vente
        date_aujourdhui = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor = conn.cursor()
        # Enregistrement de l'achat dans la base de données avec la date d'aujourd'hui
        cursor.execute(
            'INSERT INTO commande (id_client, id_produit, Quantite, prix_vente,Montant, date_commande, statut) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (id_client, produit_id, quantite, prix_vente,montant, date_aujourdhui, "En cours"))
        conn.commit()
        cursor.close()
        flash('Achat ajouté avec succès', 'success')
        return redirect(url_for('vendeur_commande'))

    curso = conn.cursor()
    curso.execute(
        "select id_commande,date_commande,commande.statut,client.nom_prenoms,produit.nom_produit from commande,client,produit where commande.id_client = client.id_client and commande.id_produit=produit.id_produit ")
    resultat = curso.fetchall()
    curso.close()

    date_actuelle = datetime.now().strftime('%Y-%m-%d')

    curso = conn.cursor()
    curso.execute(
        "select count(*) from commande where DATE(date_commande)=%s",(date_actuelle))
    commandejour = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select count(*) from commande WHERE statut='vendu'")
    commandelivre = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select sum(montant) from commande where statut='En cours'")
    montantcommande = curso.fetchone()
    curso.close()

    utilisateur_id = session['utilisateur_id']

    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
    infos_membre = cursor.fetchone()
    filename = infos_membre[8].decode('utf-8')  # Convertir bytes en str
    conn.commit()
    cursor.close()

    return render_template('membres/gestionnaire/gestion_commande.html', produits=produits, clients=clients,resultat=resultat,filename=filename,
                           commandelivre=commandelivre,commandejour=commandejour,montantcommande=montantcommande)

@app.route('/gestionnaire/ventes/', methods=["POST", "GET"])
def gestion_ventes():
    with conn.cursor() as cursor:
        cursor.execute("SELECT id_produit, nom_produit, categorie, prix FROM produit")
        produits = cursor.fetchall()

        cursor.execute("SELECT id_client, nom_prenoms FROM client")
        clients = cursor.fetchall()

    if request.method == 'POST':
        client_id = request.form.get("client")
        produit_id = request.form.get("produit")
        quantite = request.form.get("nombre")
        prix_vente = request.form.get("prix_vente")  # Récupérer le prix de vente du formulaire

        # Vérifier la quantité en stock avant de procéder à la vente
        cursor = conn.cursor()
        cursor.execute("SELECT stock FROM produit WHERE id_produit = %s", (produit_id,))
        quantite_en_stock = cursor.fetchone()[0]

        if quantite > quantite_en_stock:
            flash('Quantité demandée excède le stock disponible. Vente annulée.', 'danger')
            return redirect(url_for('gestion_ventes'))

        if not client_id:  # Si aucun client_id n'est fourni, créez un nouveau client
            nom = request.form.get("nom")
            tel = request.form.get("tel")
            email = request.form.get("email")
            adresse = request.form.get("adresse")
            with conn.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO client (nom_prenoms, telephone, email, adresse) VALUES (%s, %s, %s, %s)',
                    (nom, tel, email, adresse))
                conn.commit()
                client_id = cursor.lastrowid

        if produit_id and quantite and prix_vente:
            quantite = int(quantite)  # Convertir en entier pour la manipulation
            prix_vente = int(prix_vente)
            montant = prix_vente * quantite
            date_aujourdhui = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with conn.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO vente (id_client, id_produit, quantite, montant, prix_vente, date_vente,statut) VALUES (%s, %s, %s, %s, %s, %s,%s)',
                    (client_id, produit_id, quantite, montant, prix_vente, date_aujourdhui, "Vendu"))
                conn.commit()
                cursor.execute(
                    'UPDATE produit SET stock = stock - %s WHERE id_produit = %s',
                    (quantite, produit_id))
                conn.commit()
                cursor.close()
                flash('Vente ajoutée avec succès', 'success')
        else:
            flash('Informations de vente manquantes ou incorrectes', 'danger')

    curso = conn.cursor()
    curso.execute(
        "select id_vente,date_vente,client.nom_prenoms,produit.nom_produit,vente.statut from vente,client,produit where vente.id_client = client.id_client and vente.id_produit=produit.id_produit ")
    resultat = curso.fetchall()
    curso.close()

    date_actuelle = datetime.now().strftime('%Y-%m-%d')

    curso = conn.cursor()
    curso.execute(
        "select count(*) from vente where is_active =TRUE")
    ventetotal = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select count(*) from vente WHERE DATE(date_vente) = %s and is_active =TRUE", (date_actuelle,))
    ventejour = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "SELECT SUM(montant) FROM vente WHERE DATE(date_vente) = %s and is_active =TRUE", (date_actuelle,))
    montanttotal = curso.fetchone()
    curso.close()

    utilisateur_id = session['utilisateur_id']

    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
    infos_membre = cursor.fetchone()
    filename = infos_membre[8].decode('utf-8')  # Convertir bytes en str
    conn.commit()
    cursor.close()

    return render_template("membres/gestionnaire/gestion_ventes.html", produits=produits, clients=clients, resultat=resultat,
                           filename=filename,ventejour=ventejour,ventetotal=ventetotal,montanttotal=montanttotal)

@app.route('/gestionnaire/stock/', methods=["POST", "GET"])
def gestion_stock():
    cursor = conn.cursor()
    cursor.execute("SELECT id_produit, nom_produit,categorie,prix FROM produit")
    produits = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        produit_id = request.form["produit"]
        quantite = int(request.form["nombre"])  # Convertir en entier pour la manipulation
        # Obtenir la date d'aujourd'hui
        date_aujourdhui = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor = conn.cursor()

        # Enregistrement de la vente dans la base de données avec la date d'aujourd'hui
        cursor.execute(
            'INSERT INTO stock (ID_Produit, Quantite, date) VALUES (%s, %s, %s)',
            (produit_id, quantite, date_aujourdhui))

        cursor.execute(
            'UPDATE produit SET stock = stock + %s WHERE id_produit = %s',
            (quantite, produit_id))
        conn.commit()
        cursor.close()

        flash('Stock ajouté avec succès', 'success')
        return redirect(url_for('gestion_stock'))

    curso = conn.cursor()
    curso.execute("select produit.nom_produit,produit.categorie,quantite,date,id_stock FROM stock join produit on stock.id_produit=produit.id_produit WHERE stock.id_produit = produit.id_produit")
    resultat = curso.fetchall()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select nom_produit,categorie,stock,stock_min FROM produit")
    resultat1 = curso.fetchall()
    curso.close()

    cursor = conn.cursor()
    cursor.execute("select nom_produit, categorie, stock, stock_min FROM produit")
    resultat1 = cursor.fetchall()
    cursor.close()

    curso = conn.cursor()
    curso.execute(
        "select sum(stock) from produit")
    stocktotal = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select count(*) from produit WHERE stock < 20")
    stockfaible = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "SELECT SUM(stock * prix) FROM produit")
    montantstock = curso.fetchone()
    curso.close()

    utilisateur_id = session['utilisateur_id']
    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM utilisateur WHERE  id_utilisateur = %s', (utilisateur_id,))
    infos_membre = cursor.fetchone()
    filename = infos_membre[8].decode('utf-8')

    return render_template("membres/Gestionnaire/gestion_stock.html", produits=produits,resultat=resultat,resultat1=resultat1,filename=filename,
                           montantstock=montantstock,stocktotal=stocktotal,stockfaible=stockfaible)

@app.route('/gestionnaire/modifier_produit/<int:id>',methods=['POST','GET'])
def gestion_modifier_produit(id):
    utilisateur_id = session['utilisateur_id']
    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[8].decode('utf-8')

    curso = conn.cursor()
    curso.execute("SELECT * from produit where id_produit=%s",(id,))
    resultat = curso.fetchone()
    image_actuel = resultat[7].decode('utf-8')
    curso.close()
    if request.method == 'POST':
        nom = request.form['nom']
        categorie = request.form['categorie']
        designation = request.form['description']
        prix = request.form['prix']
        stock_min = request.form['nombre']
        image= request.files['image']

        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        curso = conn.cursor()
        curso.execute("UPDATE produit SET   nom_produit = %s, categorie = %s, prix = %s, stock_min = %s, designation = %s, image = %s WHERE id_produit = %s",
            ( nom, categorie,prix,stock_min,designation,filename, id))
        conn.commit()
        curso.close()
        flash('produit modifié avec succès', 'success')
        return redirect(url_for('gestion_produit'))
    return render_template("membres/Gestionnaire/gestion_modifier_produit.html",resultat=resultat,filename=filename,image_actuel=image_actuel)

@app.route('/gestionnnaire/modifier_stock/<int:id_stock>', methods=['GET', 'POST'])
def gestion_modifier_stock(id_stock):
    if 'utilisateur_id' in session and session.get('poste') == 'gestionnaire':
        utilisateur_id = session['utilisateur_id']

    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM utilisateur WHERE id_utilisateur = %s', (utilisateur_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[8].decode('utf-8')

    # Récupérer les informations actuelles du stock
    cursor.execute("SELECT * FROM stock WHERE id_stock = %s", (id_stock,))
    stock_actuel = cursor.fetchone()

    # Récupérer les informations des produits pour la liste déroulante
    cursor.execute("SELECT id_produit, nom_produit FROM produit")
    produits = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        id_produit = request.form['produit']
        nouvelle_quantite = int(request.form['nombre'])

        # Vérifier si le produit existe dans la table produit
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM produit WHERE id_produit = %s", (id_produit,))
        if cursor.fetchone()[0] == 0:
            flash('Le produit sélectionné n\'existe pas.', 'danger')
            return redirect(url_for('gestion_modifier_stock', id_stock=id_stock))

# Récupérer la quantité originale du stock pour ce produit
        cursor.execute("SELECT quantite FROM stock WHERE id_stock = %s", (id_stock,))
        quantite_originale = cursor.fetchone()[0]

        # Calculer la différence de quantité pour ajuster le stock dans la table produit
        difference_quantite = nouvelle_quantite - quantite_originale

        # Mise à jour du stock dans la table stock
        cursor.execute("""
            UPDATE stock SET id_produit = %s, quantite = %s WHERE id_stock = %s
            """, (id_produit, nouvelle_quantite, id_stock))

        # Mise à jour du stock dans la table produit
        cursor.execute("""
            UPDATE produit SET stock = stock + %s WHERE id_produit = %s
            """, (difference_quantite, id_produit))

        conn.commit()
        cursor.close()

        flash(' stock modifié avec succès.', 'success')
        return redirect(url_for('gestion_stock'))

    return render_template('membres/gestionnaire/gestion_modifier_stock.html', filename=filename, produits=produits, stock=stock_actuel)

#Session Gestionnaire###############################################

@app.route('/user/dashboard')
def userDashboard():
    if 'logged_in' in session:
        if 'poste' in session:
            if session['poste'] == 'vendeur':
                return redirect(url_for('dashboard_vendeur'))
            elif session['poste'] == 'gestionnaire':
                return redirect(url_for('dashboard_gestionnaire'))
        else:
            return redirect(url_for('accueil'))  # Redirection par défaut si le poste n'est pas spécifié
    else:
        return redirect(url_for('userLogin'))

  # Redirection vers la page de connexion si l'utilisateur n'est pas connecté


# @app.route('/index')
# def index():
#     # Rendre le template index.html
#     return render_template('index.html')

@app.route('/admin/Produit/', methods=["post", "get"])
def Produit():
    # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))

    admin_id = session['admin_id']
    if request.method == 'POST':
        nom = request.form['nom']
        categorie = request.form['categorie']
        designation = request.form['description']
        prix = request.form['prix']
        image = request.files['image']
        stock_min= request.form['nombre']
        stock=request.form['stock']

        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        curso = conn.cursor()
        curso.execute('INSERT INTO produit(nom_produit,categorie,prix,stock,stock_min,designation,image) VALUES (%s, %s, %s ,%s,%s, %s, %s)',
                      (nom,categorie,prix,stock,stock_min,designation,filename))
        conn.commit()
        curso.close()
        flash('Produit ajouté avec succès', 'success')
        return redirect(url_for("Produit"))  # Redirection vers la même page Produit après ajout
    else:
        # Récupération des éléments de la table produit
        curso = conn.cursor()
        curso.execute("SELECT * FROM produit")
        resultat = curso.fetchall()
        curso.close()

        curso = conn.cursor()
        curso.execute("SELECT COUNT(*) FROM produit")
        nombreprod = curso.fetchone()
        curso.close()

        admin_id = session['admin_id']
        cursor = conn.cursor()
        # Récupérer les informations de l'administrateur en utilisant son ID
        cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
        infos_admin = cursor.fetchone()
        filename = infos_admin[7].decode('utf-8')

        return render_template("Produit.html", resultat=resultat,filename=filename,nombreprod=nombreprod)

@app.route('/admin/clients/', methods=["post", "get"])
def clients():
    # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    if request.method == 'POST':
        nom = request.form['nom']
        telephone = request.form['tel']
        email = request.form['email']
        adresse = request.form['adresse']
        statut = request.form['statut']

        # Ajout automatique du préfixe +225 si nécessaire et validation du numéro
        telephone = '225' + telephone.lstrip('225')
        if len(telephone) != 13 or not telephone[3:].isdigit() or not (telephone[3:5] in ['07', '05', '01']):
            flash('Le numéro de téléphone doit être valide et contenir 13 chiffres y compris le préfixe 225.', 'danger')
            return redirect(url_for("clients"))

        # Vérifier si le numéro de téléphone est unique
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM client WHERE telephone = %s', (telephone,))
        if cursor.fetchone():
            flash('Ce numéro de téléphone est déjà utilisé.', 'danger')
            return redirect(url_for("clients"))

        # Vérification de l'unicité de l'email
        cursor.execute("SELECT * FROM client WHERE email = %s AND id_client != %s", (email, id))
        if cursor.fetchone():
            flash('Cet email est déjà utilisé par un autre client.', 'danger')
            return redirect(url_for("clients"))

        # Insérer le nouveau client
        cursor.execute('INSERT INTO client (nom_prenoms,telephone,email,adresse,statut) VALUES (%s, %s, %s, %s, %s)',
                       (nom, telephone, email, adresse,statut))
        conn.commit()
        cursor.close()
        flash('Client ajouté avec succès', 'success')
        return redirect(url_for("clients"))  # Redirection vers la même page clients après ajout
    else:
        # Récupération des éléments de la table client
        curso = conn.cursor()
        curso.execute("SELECT * FROM client")
        resultat = curso.fetchall()
        curso.close()

        admin_id = session['admin_id']
        cursor = conn.cursor()
        # Récupérer les informations de l'administrateur en utilisant son ID
        cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
        infos_admin = cursor.fetchone()
        filename = infos_admin[7].decode('utf-8')  # Convertir bytes en str

        cursor.close()

        return render_template("clients.html", resultat=resultat,filename=filename)

@app.route('/vente_clients', methods=['POST'])
def vente_clients():
    if request.method == 'POST':
        data = request.get_json()
        nom = data['nom']
        tel = data['tel']
        email = data['email']
        adresse = data['adresse']
        statut = data['statut']

        # Ajout automatique du préfixe 225 si nécessaire et validation du numéro
        telephone = '225' + tel.lstrip('225')
        if len(telephone) != 13 or not telephone[3:].isdigit() or not (telephone[3:5] in ['07', '05', '01']):
            return jsonify({'message': 'Le numéro de téléphone doit être valide et contenir 13 chiffres y compris le préfixe 225.'}), 200

        # Vérifier si le numéro de téléphone est unique
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM client WHERE telephone = %s', (telephone,))
        if cursor.fetchone():
            return jsonify({'message': 'Ce numéro de téléphone est déjà utilisé !'}), 200

        # Vérification de l'unicité de l'email
        cursor.execute("SELECT * FROM client WHERE email = %s AND id_client != %s", (email, id))
        if cursor.fetchone():
            return jsonify({'message': 'Cet email est déjà utilisé par un autre client!'}), 200

        cursor = conn.cursor()
        cursor.execute('INSERT INTO client (nom_prenoms, telephone, email, adresse, statut) VALUES (%s, %s, %s, %s, %s)', (nom, tel, email, adresse, statut))
        conn.commit()
        cursor.close()

        return jsonify({'message': 'Client enregistré avec succès!'}), 200

    return jsonify({'error': 'Invalid request method'}), 400


@app.route('/admin/profil/')
def profil():
    # Vérifier si l'administrateur est connecté
    if 'admin_id' not in session:
        flash('Veuillez vous connecter d\'abord.', 'danger')
        return redirect(url_for('adminIndex'))

    # Récupérer l'ID de l'administrateur depuis la session
    admin_id = session['admin_id']

    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    if infos_admin:
     filename = infos_admin[7].decode('utf-8') if infos_admin[7] is not None else None
    else:
       filename = None

    cursor.close()

    return render_template('profil.html', infos_admin=infos_admin,filename=filename)

@app.route('/admin/profil_base/')
def profil_base():
    # Vérifier si l'administrateur est connecté
    if 'admin_id' not in session:
        flash('Veuillez vous connecter d\'abord.', 'danger')
        return redirect(url_for('adminIndex'))

    # Récupérer l'ID de l'administrateur depuis la session
    admin_id = session['admin_id']

    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')  # Convertir bytes en str

    cursor.close()

    return render_template('base.html', infos_admin=infos_admin,filename=filename)


@app.route('/admin/fournisseurs/', methods=["post", "get"])
def fournisseurs():
    # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    if request.method == 'POST':
        nom = request.form['nom']
        telephone = request.form['tel']
        email = request.form['email']
        adresse = request.form['adresse']

        # Ajout automatique du préfixe +225 si nécessaire et validation du numéro
        telephone = '+225' + telephone.lstrip('+225')
        if len(telephone) != 14 or not telephone[4:].isdigit() or not (telephone[4:6] in ['07', '05', '01']):
            flash('Le numéro de téléphone doit être valide et contenir 14 chiffres y compris le préfixe +225.',
                  'danger')
            return redirect(url_for("fournisseurs"))

        # Vérifier si le numéro de téléphone est unique
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM fournisseur WHERE telephone = %s', (telephone,))
        if cursor.fetchone():
            flash('Ce numéro de téléphone est déjà utilisé.', 'danger')
            return redirect(url_for("fournisseurs"))

        # Vérification de l'unicité de l'email
        cursor.execute("SELECT * FROM fournisseur WHERE email = %s AND id_fournisseur != %s", (email, id))
        if cursor.fetchone():
            flash('Cet email est déjà utilisé par un autre fournisseur.', 'danger')
            return redirect(url_for("fournisseurs"))

        curso = conn.cursor()
        curso.execute('INSERT INTO fournisseur (nom_prenoms,telephone,email,adresse) VALUES (%s, %s, %s, %s)',
                      (nom,telephone,email,adresse))
        conn.commit()
        curso.close()
        flash('Fournisseur ajouté avec succès', 'success')
        return redirect(url_for("fournisseurs"))
    else:
        # Récupération des éléments de la table fournisseur
        curso = conn.cursor()
        curso.execute("SELECT * FROM fournisseur")
        resultat = curso.fetchall()
        curso.close()

        admin_id = session['admin_id']

        cursor = conn.cursor()
        # Récupérer les informations de l'administrateur en utilisant son ID
        cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
        infos_admin = cursor.fetchone()
        filename = infos_admin[7].decode('utf-8')  # Convertir bytes en str

        cursor.close()

        return render_template("fournisseurs.html", resultat=resultat,filename=filename)


@app.route('/admin/ventes/', methods=["POST", "GET"])
def ventes():
    # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    with conn.cursor() as cursor:
        cursor.execute("SELECT id_produit, nom_produit, categorie, prix FROM produit")
        produits = cursor.fetchall()

        cursor.execute("SELECT id_client, nom_prenoms FROM client")
        clients = cursor.fetchall()

    if request.method == 'POST':
        client_id = request.form.get("client")
        produit_id = request.form.get("produit")
        quantite = request.form.get("nombre")
        prix_vente = request.form.get("prix_vente")  # Récupérer le prix de vente du formulaire

        if not client_id:  # Si aucun client_id n'est fourni, créez un nouveau client
            nom = request.form.get("nom")
            tel = request.form.get("tel")
            email = request.form.get("email")
            adresse = request.form.get("adresse")
            statut = request.form.get("statut")
            with conn.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO client (nom_prenoms, telephone, email, adresse,statut) VALUES (%s,%s,%s,%s,%s)',
                    (nom, tel, email, adresse,statut))
                conn.commit()
                client_id = cursor.lastrowid

        if produit_id and quantite and prix_vente:
            quantite = int(quantite)  # Convertir en entier pour la manipulation
            prix_vente = int(prix_vente) 
            montant = prix_vente * quantite
            date_aujourdhui = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with conn.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO vente (id_client, id_produit, quantite, montant, prix_vente, date_vente,statut) VALUES (%s, %s, %s, %s, %s, %s,%s)',
                    (client_id, produit_id, quantite, montant, prix_vente, date_aujourdhui,"Vendu"))
                conn.commit()
                cursor.execute(
                    'UPDATE produit SET stock = stock - %s WHERE id_produit = %s',
                    (quantite, produit_id))
                conn.commit()
                cursor.close()
                flash('Vente ajoutée avec succès', 'success')
        else:
            flash('Informations de vente manquantes ou incorrectes', 'danger')

    curso = conn.cursor()
    curso.execute(
        "select id_vente,date_vente,client.nom_prenoms,produit.nom_produit,vente.statut from vente,client,produit where vente.id_client = client.id_client and vente.id_produit=produit.id_produit order by date_vente desc")
    resultat = curso.fetchall()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select count(*) from vente where is_active =TRUE")
    ventetotal = curso.fetchone()
    curso.close()

    date_actuelle = datetime.now().strftime('%Y-%m-%d')

    curso = conn.cursor()
    curso.execute(
        "select count(*) from vente WHERE DATE(date_vente) = %s and is_active =TRUE", (date_actuelle,))
    ventejour = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "SELECT SUM(montant) FROM vente WHERE DATE(date_vente) = %s and is_active =TRUE", (date_actuelle,))
    montanttotal = curso.fetchone()
    curso.close()

    admin_id = session['admin_id']
    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    return render_template("ventes.html", produits=produits, clients=clients,resultat=resultat,filename=filename,
                           ventetotal=ventetotal,montanttotal=montanttotal,ventejour=ventejour)

@app.route('/get_product_infos/<int:produit_id>', methods=['GET'])
def get_product_infos(produit_id):
    with conn.cursor() as cursor:
        cursor.execute("SELECT nom_produit AS designation, stock FROM produit WHERE id_produit = %s", (produit_id,))
        product = cursor.fetchone()
        if product:
            return jsonify(designation=product[0], stock=product[1])
        else:
            return jsonify(error="Produit non trouvé"), 404


@app.route('/admin/modifier_vente/<int:id_vente>', methods=['GET', 'POST'])
def modifier_vente(id_vente):
        # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    admin_id = session['admin_id']
    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    # Récupérer les informations actuelles de la vente
    cursor.execute(
        "SELECT vente.*, produit.nom_produit, client.nom_prenoms FROM vente "
        "JOIN produit ON vente.id_produit = produit.id_produit "
        "JOIN client ON vente.id_client = client.id_client "
        "WHERE id_vente = %s", (id_vente,))
    vente = cursor.fetchone()

    # Récupérer les informations des produits et clients pour les listes déroulantes
    cursor.execute("SELECT id_produit, nom_produit FROM produit")
    produits = cursor.fetchall()
    cursor.execute("SELECT id_client, nom_prenoms FROM client")
    clients = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        # Récupération des données du formulaire
        id_produit = request.form['produit']
        id_client = request.form['client']
        nouvelle_quantite = int(request.form['nombre'])
        prix_vente = float(request.form['prix_vente'])

        # Vérifier la quantité en stock avant de procéder à la vente
        cursor = conn.cursor()
        cursor.execute("SELECT stock FROM produit WHERE id_produit = %s", (id_produit,))
        quantite_en_stock = cursor.fetchone()[0]

        if nouvelle_quantite > quantite_en_stock:
            flash('Quantité demandée excède le stock disponible. Vente annulée.', 'danger')
            return redirect(url_for('ventes'))

        # Récupérer la quantité originale et le produit de la vente avant la mise à jour
        cursor = conn.cursor()
        cursor.execute("SELECT quantite, id_produit FROM vente WHERE id_vente = %s", (id_vente,))
        quantite_originale, produit_original = cursor.fetchone()

        # Calcul du montant total
        montant = nouvelle_quantite * prix_vente

        # Mise à jour de la vente dans la base de données
        cursor.execute("""
            UPDATE vente SET id_produit = %s, id_client = %s, quantite = %s, 
            prix_vente = %s, montant = %s WHERE id_vente = %s
            """, (id_produit, id_client, nouvelle_quantite, prix_vente, montant, id_vente))
        conn.commit()

        # Mise à jour du stock dans la table produit
        # Si le produit est le même, ajuster le stock basé sur la différence de quantité
        if str(id_produit) == str(produit_original):  # Assurez-vous que les comparaisons sont de même type
            difference_quantite = quantite_originale - nouvelle_quantite
            cursor.execute("""
                UPDATE produit SET stock = stock + %s WHERE id_produit = %s
                """, (difference_quantite, id_produit))
        else:
            # Si le produit a changé, augmenter le stock de l'ancien produit et diminuer celui du nouveau
            cursor.execute("UPDATE produit SET stock = stock + %s WHERE id_produit = %s", (quantite_originale, produit_original))
            cursor.execute("UPDATE produit SET stock = stock - %s WHERE id_produit = %s", (nouvelle_quantite, id_produit))

        conn.commit()
        cursor.close()

        flash('vente modifiée avec succès.', 'success')
        return redirect(url_for('ventes'))
    return render_template('modifier_vente.html', 
                           filename=filename, produits=produits, clients=clients, vente=vente)


@app.route('/status_vente/<entry_id>', methods=['POST'])
def status_vente(entry_id):
    if request.method == 'POST':
        # Récupérer le nouveau statut envoyé depuis le formulaire
        new_status = request.form.get('status')

        cursor = conn.cursor()

        if new_status == "Retourné":
            # Marquer la vente comme inactive
            cursor.execute("UPDATE vente SET statut = %s, is_active = FALSE WHERE id_vente = %s", (new_status, entry_id))
            cursor.execute("UPDATE produit JOIN vente ON produit.id_produit = vente.id_produit SET produit.stock = produit.stock + vente.quantite where id_vente = %s",(entry_id))
        else:
            # Mettre à jour le statut dans la base de données
            cursor.execute("UPDATE vente SET statut = %s, is_active = TRUE WHERE id_vente = %s", (new_status, entry_id))
            cursor.execute(
                "UPDATE produit JOIN vente ON produit.id_produit = vente.id_produit SET produit.stock = produit.stock - vente.quantite where id_vente = %s",
                (entry_id))

        conn.commit()
        cursor.close()

        # Rediriger vers la page des ventes après la mise à jour du statut
        return redirect(url_for('ventes'))
    else:
        # Si la méthode de la requête n'est pas POST, retourner une erreur 405 (Méthode non autorisée)
        return jsonify({'error': 'Method Not Allowed'}), 405


from flask import request, jsonify, flash
from datetime import datetime
 
@app.route('/submit_vente', methods=['POST'])
def submit_vente():
    # Vérifiez si l'utilisateur est connecté en tant que vendeur ou administrateur
    if 'utilisateur_id' in session and session.get('poste') == 'vendeur':
        utilisateur_id = session['utilisateur_id']
        role = 'vendeur'
    elif 'admin_id' in session:
        utilisateur_id = session['admin_id']
        role = 'admin'
    else:
        flash('Veuillez vous connecter en tant que vendeur ou administrateur .', 'danger')
        return jsonify({'error': 'Non autorisé'}), 403

    # Récupérer les données de la vente à partir du corps de la requête
    order_data = request.get_json()

    if not order_data:
        return jsonify({'error': 'Aucune donnée reçue'}), 400

    # Traiter les données de la vente
    for item in order_data:
        product_id = item.get('produit_id')
        quantity = item.get('nombre')
        prix_vente = item.get('prix_vente')
        id_client = item.get('id_client')
        montant = item.get('montant')

        if not all([product_id, quantity, prix_vente, id_client, montant]):
            return jsonify({'error': 'Données de vente incomplètes'}), 400

        cursor = conn.cursor()
        try:
            # Insérer l'élément de vente dans la base de données
            if role == 'admin':
                cursor.execute(
                    """INSERT INTO vente (id_client, id_produit, Quantite, prix_vente, Montant, date_vente, statut, id_admin)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (id_client, product_id, quantity, prix_vente, montant, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                     'Vendu', utilisateur_id)
                )
            else:
                cursor.execute(
                    """INSERT INTO vente (id_client, id_produit, Quantite, prix_vente, Montant, date_vente, statut, id_utilisateur)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (id_client, product_id, quantity, prix_vente, montant, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                     'Vendu', utilisateur_id)
                )
            conn.commit()

            # Mettre à jour le stock du produit
            cursor.execute(
                'UPDATE produit SET stock = stock - %s WHERE id_produit = %s',
                (quantity, product_id)
            )
            conn.commit()

            flash('Vente ajoutée avec succès', 'success')
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()

    # Préparer la réponse
    response_data = {
        'message': 'Ventes ajoutées avec succès'
    }

    return jsonify(response_data), 200


@app.route('/submit_new_client_vente', methods=['POST'])
def submit_new_client_vente():
    if 'utilisateur_id' in session and session.get('poste') == 'vendeur':
        utilisateur_id = session['utilisateur_id']
        role = 'vendeur'
    elif 'admin_id' in session:
        utilisateur_id = session['admin_id']
        role = 'admin'
    else:
        flash('Veuillez vous connecter en tant que vendeur ou administrateur.', 'danger')
        return jsonify({'error': 'Non autorisé'}), 403

    order_data = request.get_json()

    print('Données reçues:', order_data)

    if not order_data:
        return jsonify({'error': 'Aucune donnée reçue'}), 400

    client_data = order_data.get('client')
    sales_data = order_data.get('order')

    if not client_data or not sales_data:
        return jsonify({'error': 'Données client ou vente manquantes'}), 400

    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO client (nom_prenoms, telephone, email, adresse, statut)
               VALUES (%s, %s, %s, %s, %s)""",
            (client_data['nom'], client_data['tel'], client_data['email'], client_data['adresse'], client_data['statut'])
        )
        conn.commit()
        cursor.execute("SELECT LAST_INSERT_ID()")
        client_id = cursor.fetchone()[0]

        print('ID Client inséré:', client_id)

        for item in sales_data:
            product_id = item.get('produit_id')
            quantity = item.get('nombre')
            prix_vente = item.get('prix_vente')
            montant = item.get('montant')

            if not all([product_id, quantity, prix_vente, client_id, montant]):
                return jsonify({'error': 'Données de vente incomplètes'}), 400

            if role == 'admin':
                cursor.execute(
                    """INSERT INTO vente (id_client, id_produit, Quantite, prix_vente, Montant, date_vente, statut, id_admin)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (client_id, product_id, quantity, prix_vente, montant, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                     'Vendu', utilisateur_id)
                )
            else:
                cursor.execute(
                    """INSERT INTO vente (id_client, id_produit, Quantite, prix_vente, Montant, date_vente, statut, id_utilisateur)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (client_id, product_id, quantity, prix_vente, montant, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                     'Vendu', utilisateur_id)
                )
            conn.commit()

            cursor.execute(
                'UPDATE produit SET stock = stock - %s WHERE id_produit = %s',
                (quantity, product_id)
            )
            conn.commit()

        flash('Vente ajoutée avec succès', 'success')
    except Exception as e:
        conn.rollback()
        print('Erreur:', e)
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()

    response_data = {
        'message': 'Ventes ajoutées avec succès',
        'client_id': client_id  # Retourner l'ID du client nouvellement créé
    }

    return jsonify(response_data), 200



@app.route('/submit_order', methods=['POST'])
def submit_order():
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant que administrateur', 'danger')
        return jsonify({'error': 'Non autorisé'}), 403

    # Récupérer les données de la commande à partir du corps de la requête
    order_data = request.get_json()

    # Valider les données de la commande (vérifier les valeurs manquantes ou invalides)

    # Traiter les données de la commande
    for item in order_data:
        product_id = item['produit_id']
        quantity = item['nombre']
        unit_price = item['prix_unitaire']
        fournisseur_id = item['fournisseur_id']
        # Insérer l'élément de commande dans la base de données
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO entree (ID_fournisseur, id_produit, Quantite, prix, date_entree, statut) VALUES (%s, %s, %s, %s, %s, %s)""",
            (fournisseur_id, product_id, quantity, unit_price,datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'En cours')  # Remplacer 1 par l'ID du fournisseur réel
        )
        conn.commit()
        cursor.close()
        flash('Commande soumise avec succès', 'success')
        # Calculer le prix total (si nécessaire)

    # Préparer la réponse
    response_data = {
        'message': 'Commande soumise avec succès'
    }

    return jsonify(response_data), 200


@app.route('/donnee_vente/<int:ligne_id>', methods=['GET'])
def donnee_vente(ligne_id):
    # Exécuter la requête SQL pour récupérer la date associée à l'ID de la ligne
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date_vente FROM vente WHERE id_vente = %s", (ligne_id,))
    date_vente = cursor.fetchone()[0]  # Récupérer la date de la première colonne

    # Ensuite, utilisez cette date pour récupérer les données associées
    cursor.execute(
        "SELECT produit.designation, vente.quantite, vente.prix_vente, vente.montant, vente.date_vente,id_vente FROM vente JOIN produit ON vente.id_produit = produit.id_produit WHERE vente.date_vente = %s", (date_vente,))
    resultat1 = cursor.fetchall()
    cursor.close()

    # Formater les données et les renvoyer en tant que réponse JSON
    data = [{'designation': row[0], 'quantite': row[1], 'prix_vente': row[2], 'montant': row[3], 'date_commande': row[5]} for row in resultat1]

    return jsonify(data)

@app.route('/admin/achats/', methods=["POST", "GET"])
def achats():
    cursor = conn.cursor()
    cursor.execute("SELECT id_produit, nom_produit, categorie, prix FROM produit")
    produits = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("SELECT id_fournisseur, nom_prenoms FROM fournisseur")
    fournisseurs = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        produit_id = request.form["produit"]
        quantite = int(request.form["nombre"])  # Convertir en entier pour la manipulation
        fournisseur_id = request.form["fournisseur"]

        montant = 0
        date_aujourdhui = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor = conn.cursor()
        # Enregistrement de l'achat dans la base de données avec la date d'aujourd'hui
        cursor.execute(
            'INSERT INTO entree (ID_fournisseur, id_produit, Quantite, prix, date_entree, statut) VALUES (%s, %s, %s, %s, %s, %s)',
            (fournisseur_id, produit_id, quantite, montant, date_aujourdhui, "En cours"))
        conn.commit()
        cursor.close()
        flash('Achat ajouté avec succès', 'success')
        return redirect(url_for('achats'))

    cursor = conn.cursor()
    cursor.execute(
        'UPDATE entree JOIN produit ON entree.id_produit = produit.id_produit SET entree.prix = produit.prix * entree.quantite')
    conn.commit()
    cursor.close()

    curso = conn.cursor()
    curso.execute(
        "select id_entree,date_entree,statut,fournisseur.nom_prenoms,produit.nom_produit from entree,fournisseur,produit where entree.id_fournisseur = fournisseur.id_fournisseur and entree.id_produit=produit.id_produit order by date_entree desc  ")
    resultat = curso.fetchall()
    curso.close()

    date_actuelle = datetime.now().strftime('%Y-%m-%d')

    curso = conn.cursor()
    curso.execute(
        "select count(*) from entree where statut='En cours' ")
    achatmensuel = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select count(*) from entree WHERE statut='livré' ")
    achatlivre = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select sum(prix) from entree WHERE statut='livré'")
    montantachat = curso.fetchone()
    curso.close()

    admin_id = session['admin_id']
    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    return render_template("achats.html", produits=produits, fournisseurs=fournisseurs,resultat=resultat,filename=filename,
                           montantachat=montantachat,achatlivre=achatlivre,achatmensuel=achatmensuel)

@app.route('/admin/modifier_achat/<int:id_entree>', methods=['GET', 'POST'])
def modifier_achat(id_entree):
    # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    admin_id = session['admin_id']
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    # Récupérer les informations actuelles de l'achat
    cursor.execute("SELECT * FROM entree WHERE id_entree = %s", (id_entree,))
    achat = cursor.fetchone()

    # Récupérer les informations des produits et fournisseurs pour les listes déroulantes
    cursor.execute("SELECT id_produit, nom_produit, prix FROM produit")
    produits = cursor.fetchall()
    cursor.execute("SELECT id_fournisseur, nom_prenoms FROM fournisseur")
    fournisseurs = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        produit_id = request.form['produit']
        fournisseur_id = request.form['fournisseur']
        nouvelle_quantite = int(request.form['nombre'])
        prix_vente = float(request.form['prix_vente'])  # Ce champ doit correspondre au prix d'achat

        # Mise à jour de l'achat dans la base de données
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE entree SET id_fournisseur = %s, id_produit = %s, quantite = %s, 
            prix = %s WHERE id_entree = %s
            """, (fournisseur_id, produit_id, nouvelle_quantite, prix_vente, id_entree))
        conn.commit()
        cursor.close()

        flash('Achat modifié avec succès', 'success')
        return redirect(url_for('achats'))

    return render_template('modifier_achats.html',
                           filename=filename, produits=produits, fournisseurs=fournisseurs, achat=achat)

@app.route('/get_row_data/<int:row_id>', methods=['GET'])
def get_row_data(row_id):
    # Exécuter la requête SQL pour récupérer la date associée à l'ID de la ligne
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date_entree FROM entree WHERE id_entree = %s", (row_id,))
    date_entree = cursor.fetchone()[0]  # Récupérer la date de la première colonne

    # Ensuite, utilisez cette date pour récupérer les données associées
    cursor.execute(
        "SELECT produit.designation, entree.quantite, produit.prix, entree.prix, entree.date_entree,id_entree FROM entree JOIN produit ON entree.id_produit = produit.id_produit WHERE entree.date_entree = %s", (date_entree,))
    resultat1 = cursor.fetchall()
    cursor.close()

    # Formater les données et les renvoyer en tant que réponse JSON
    data = [{'designation': row[5], 'quantite': row[0], 'prix_produit': row[1], 'prix_entree': row[2], 'date_entree': row[3]} for row in resultat1]

    return jsonify(data)

@app.route('/status_achat/<entry_id>', methods=['POST'])
def status_achat(entry_id):
    if request.method == 'POST':
        # Récupérer le nouveau statut envoyé depuis le formulaire
        new_status = request.form.get('status')

        # Mettre à jour le statut dans la base de données
        cursor = conn.cursor()
        cursor.execute("UPDATE entree SET statut = %s WHERE id_entree = %s", (new_status, entry_id))
        conn.commit()
        cursor.close()

        # Rediriger vers la page d'achats après la mise à jour du statut
        return redirect(url_for('achats'))
    else:
        # Si la méthode de la requête n'est pas POST, retourner une erreur 405 (Méthode non autorisée)
        return jsonify({'error': 'Method Not Allowed'}), 405

@app.route('/get_product_info/<int:produit_id>')
def get_product_info(produit_id):
    # Effectuez une requête à la base de données pour obtenir les informations du produit
    cursor = conn.cursor()
    cursor.execute("SELECT nom_produit, prix,designation FROM produit WHERE id_produit = %s", (produit_id,))
    produit_info = cursor.fetchone()
    cursor.close()

    # Vérifiez si le produit existe
    if produit_info:
        # Retournez les informations du produit sous forme de données JSON
        response = {
            'nom': produit_info[0],
            'prix': produit_info[1],
            'designation': produit_info[2]
        }
        return jsonify(response)
    else:
        # Si le produit n'est pas trouvé, retournez un message d'erreur
        return jsonify({'error': 'Produit non trouvé'}), 404

@app.route('/get_fournisseur/<int:fournisseur_id>')
def get_fournisseur(fournisseur_id):
    # Effectuez une requête à la base de données pour obtenir les informations du produit
    cursor = conn.cursor()
    cursor.execute("SELECT nom_prenoms FROM fournisseur WHERE id_fournisseur = %s", (fournisseur_id,))
    fournisseur_infos = cursor.fetchone()
    cursor.close()

    # Vérifiez si le produit existe
    if fournisseur_infos:
        # Retournez les informations du fournisseur sous forme de données JSON
        response = {
            'nom': fournisseur_infos[0],
        }
        return jsonify(response)
    else:
        # Si le produit n'est pas trouvé, retournez un message d'erreur
        return jsonify({'error': 'Fournisseur non trouvé'}), 404

@app.route('/get_client/<int:client_id>')
def get_client(client_id):
    # Effectuez une requête à la base de données pour obtenir les informations du produit
    cursor = conn.cursor()
    cursor.execute("SELECT nom_prenoms FROM client WHERE id_client = %s", (client_id,))
    client_infos = cursor.fetchone()
    cursor.close()

    # Vérifiez si le client existe
    if client_infos:
        # Retournez les informations du fournisseur sous forme de données JSON
        response = {
            'nom': client_infos[0],
        }
        return jsonify(response)
    else:
        # Si le produit n'est pas trouvé, retournez un message d'erreur
        return jsonify({'error': 'Client non trouvé'}), 404

@app.route('/admin/stock/', methods=["POST", "GET"])
def stock():
    # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    cursor = conn.cursor()
    cursor.execute("SELECT id_produit, nom_produit,categorie,prix FROM produit")
    produits = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        produit_id = request.form["produit"]
        quantite = int(request.form["nombre"])  # Convertir en entier pour la manipulation
        # Obtenir la date d'aujourd'hui
        date_aujourdhui = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor = conn.cursor()

        # Enregistrement de la vente dans la base de données avec la date d'aujourd'hui
        cursor.execute(
            'INSERT INTO stock (ID_Produit, Quantite, date) VALUES (%s, %s, %s)',
            (produit_id, quantite, date_aujourdhui))

        cursor.execute(
            'UPDATE produit SET stock = stock + %s WHERE id_produit = %s',
            (quantite, produit_id))
        conn.commit()
        cursor.close()

        flash('Stock ajouté avec succès', 'success')
        return redirect(url_for('stock'))

    curso = conn.cursor()
    curso.execute("select produit.nom_produit,produit.categorie,quantite,date,id_stock FROM stock join produit on stock.id_produit=produit.id_produit WHERE stock.id_produit = produit.id_produit order by date desc")
    resultat = curso.fetchall()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select nom_produit,categorie,stock,stock_min FROM produit")
    resultat1 = curso.fetchall()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select sum(stock) from produit")
    stocktotal = curso.fetchone()
    curso.close()

    date_actuelle = datetime.now().strftime('%Y-%m-%d')

    curso = conn.cursor()
    curso.execute(
        "select count(*) from produit WHERE stock < 10")
    stockfaible = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "SELECT SUM(stock * prix) FROM produit")
    montantstock = curso.fetchone()
    curso.close()

    admin_id = session['admin_id']
    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    return render_template("stock.html", produits=produits,resultat=resultat,resultat1=resultat1,filename=filename,
                           stockfaible=stockfaible,stocktotal=stocktotal,montantstock=montantstock)

@app.route('/admin/modifier_stock/<int:id_stock>', methods=['GET', 'POST'])
def modifier_stock(id_stock):
        # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    admin_id = session['admin_id']
    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    # Récupérer les informations actuelles du stock
    cursor.execute("SELECT * FROM stock WHERE id_stock = %s", (id_stock,))
    stock_actuel = cursor.fetchone()

    # Récupérer les informations des produits pour la liste déroulante
    cursor.execute("SELECT id_produit, nom_produit FROM produit")
    produits = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        id_produit = request.form['produit']
        nouvelle_quantite = int(request.form['nombre'])

        # Vérifier si le produit existe dans la table produit
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM produit WHERE id_produit = %s", (id_produit,))
        if cursor.fetchone()[0] == 0:
            flash('Le produit sélectionné n\'existe pas.', 'danger')
            return redirect(url_for('modifier_stock', id_stock=id_stock))

# Récupérer la quantité originale du stock pour ce produit
        cursor.execute("SELECT quantite FROM stock WHERE id_stock = %s", (id_stock,))
        quantite_originale = cursor.fetchone()[0]

        # Calculer la différence de quantité pour ajuster le stock dans la table produit
        difference_quantite = nouvelle_quantite - quantite_originale

        # Mise à jour du stock dans la table stock
        cursor.execute("""
            UPDATE stock SET id_produit = %s, quantite = %s WHERE id_stock = %s
            """, (id_produit, nouvelle_quantite, id_stock))

        # Mise à jour du stock dans la table produit
        cursor.execute("""
            UPDATE produit SET stock = stock + %s WHERE id_produit = %s
            """, (difference_quantite, id_produit))

        conn.commit()
        cursor.close()

        flash(' stock modifié avec succès.', 'success')
        return redirect(url_for('stock'))

    return render_template('modifier_stock.html', filename=filename, produits=produits, stock=stock_actuel)


@app.route('/submit_stock', methods=['POST'])
def submit_stock():
    # Récupérer les données de la commande à partir du corps de la requête
    order_data = request.get_json()

    # Valider les données de la commande (vérifier les valeurs manquantes ou invalides)

    # Traiter les données de la commande
    for item in order_data:
        produit_id = item['produit_id']
        quantite = item['nombre']
        date_aujourdhui = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor = conn.cursor()

        # Enregistrement de la vente dans la base de données avec la date d'aujourd'hui
        cursor.execute(
            'INSERT INTO stock (ID_Produit, Quantite, date) VALUES (%s, %s, %s)',
            (produit_id, quantite, date_aujourdhui))

        cursor.execute(
            'UPDATE produit SET stock = stock + %s WHERE id_produit = %s',
            (quantite, produit_id))
        conn.commit()
        cursor.close()
        flash('stock mis à jour avec succès', 'success')
    # Préparer la réponse
    response_data = {
    }

    return jsonify(response_data), 200

@app.route('/admin/commandes/', methods=["POST", "GET"])
def commandes():
    # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))

    admin_id = session['admin_id']

    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    cursor.close()

    if infos_admin is None:
        flash('Informations de l\'administrateur non trouvées.', 'danger')
        return redirect(url_for('userLogin'))

    filename = infos_admin[7].decode('utf-8')

    cursor = conn.cursor()
    cursor.execute("SELECT id_produit, nom_produit, categorie, prix FROM produit")
    produits = cursor.fetchall()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute("SELECT id_client, nom_prenoms FROM client")
    clients = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        produit_id = request.form["produit"]
        quantite = int(request.form["nombre"])  # Convertir en entier pour la manipulation
        id_client = request.form["client"]
        prix_vente = int(request.form["prix"])

        montant = quantite * prix_vente
        date_aujourdhui = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor = conn.cursor()
        try:
            # Enregistrement de l'achat dans la base de données avec la date d'aujourd'hui
            cursor.execute(
                'INSERT INTO commande (id_client, id_produit, Quantite, prix_vente, Montant, date_commande, statut, id_admin) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (id_client, produit_id, quantite, prix_vente, montant, date_aujourdhui, "En cours", admin_id)
            )
            conn.commit()
            flash('Achat ajouté avec succès', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Erreur lors de l\'ajout de l\'achat : {str(e)}', 'danger')
        finally:
            cursor.close()
        return redirect(url_for('commandes'))

    cursor = conn.cursor()
    cursor.execute(
        "SELECT id_commande, date_commande, commande.statut, client.nom_prenoms, produit.nom_produit FROM commande "
        "JOIN client ON commande.id_client = client.id_client "
        "JOIN produit ON commande.id_produit = produit.id_produit order by date_commande desc"
    )
    resultat = cursor.fetchall()
    cursor.close()

    date_actuelle = datetime.now().strftime('%Y-%m-%d')

    curso = conn.cursor()
    curso.execute(
        "select count(*) from commande WHERE DATE(date_commande) = %s", (date_actuelle,))
    commandejour = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select count(*) from commande WHERE statut='vendu' and DATE(date_commande) = %s", (date_actuelle,))
    commandelivre = curso.fetchone()
    curso.close()

    curso = conn.cursor()
    curso.execute(
        "select sum(montant) from commande where statut='En cours' ")
    montantcommande = curso.fetchone()
    curso.close()

    return render_template('commandes.html', produits=produits, clients=clients, resultat=resultat, filename=filename,
                           montantcommande=montantcommande,commandelivre=commandelivre,commandejour=commandejour)


@app.route('/admin/modifier_commande/<int:id_commande>', methods=['GET', 'POST'])
def modifier_commande(id_commande):
        # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    # Récupérer les informations actuelles de la commande
    cursor = conn.cursor()
    cursor.execute("SELECT id_commande,client.nom_prenoms,produit.nom_produit,quantite,prix_vente,commande.id_client,commande.id_produit FROM commande join produit on commande.id_produit=produit.id_produit join client on commande.id_client=client.id_client WHERE id_commande = %s", (id_commande,))
    commande_actuelle = cursor.fetchone()
    cursor.close()

    # Récupérer les informations des produits et clients pour les listes déroulantes
    cursor = conn.cursor()
    cursor.execute("SELECT id_produit, nom_produit FROM produit")
    produits = cursor.fetchall()
    cursor.execute("SELECT id_client, nom_prenoms FROM client")
    clients = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        # Récupération des données du formulaire
        id_client = request.form['client']
        id_produit = request.form['produit']
        quantite = request.form['nombre']
        prix_vente = request.form['prix_vente']

        # Calcul du montant total
        montant = int(quantite) * int(prix_vente)
        
        # Mise à jour de la commande dans la base de données
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE commande SET id_client = %s, id_produit = %s, quantite = %s, 
            prix_vente = %s, montant = %s WHERE id_commande = %s
            """, (id_client, id_produit, quantite, prix_vente, montant, id_commande))
        conn.commit()
        cursor.close()

        flash('Commande mise à jour avec succès.', 'success')
        return redirect(url_for('commandes'))

    admin_id = session['admin_id']
    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')
    # Afficher le formulaire de modification avec les informations préremplies
    return render_template('modifier_commande.html', commande=commande_actuelle, produits=produits, clients=clients, filename=filename)


@app.route('/status_commande/<entry_id>', methods=['POST'])
def status_commande(entry_id):
    if request.method == 'POST':
        # Récupérer le nouveau statut envoyé depuis le formulaire
        new_status = request.form.get('status')

        # Mettre à jour le statut dans la base de données
        cursor = conn.cursor()
        cursor.execute("UPDATE commande SET statut = %s WHERE id_commande = %s", (new_status, entry_id))
        conn.commit()
        cursor.close()

        # Rediriger vers la page d'achats après la mise à jour du statut
        return redirect(url_for('commandes'))
    else:
        # Si la méthode de la requête n'est pas POST, retourner une erreur 405 (Méthode non autorisée)
        return jsonify({'error': 'Method Not Allowed'}), 405

@app.route('/submit_commande', methods=['POST'])
def submit_commande():
    # Vérifiez si l'utilisateur est connecté en tant que vendeur ou administrateur
    if 'utilisateur_id' in session:
        utilisateur_id = session['utilisateur_id']
        role = session.get('poste')
    elif 'admin_id' in session:
        utilisateur_id = session['admin_id']
        role = 'admin'
    else:
        flash('Veuillez vous connecter en tant que vendeur ou administrateur.', 'danger')
        return jsonify({'error': 'Non autorisé'}), 403

    # Récupérer les données de la commande à partir du corps de la requête
    order_data = request.get_json()

    # Valider les données de la commande (vérifier les valeurs manquantes ou invalides)
    # Exemple de validation simple (à adapter selon vos besoins)
    if not order_data:
        return jsonify({'error': 'Aucune donnée de commande reçue'}), 400

    # Traiter les données de la commande
    for item in order_data:
        product_id = item.get('produit_id')
        quantity = item.get('nombre')
        prix_vente = item.get('prix_vente')
        id_client = item.get('id_client')
        montant = item.get('montant')

        if not all([product_id, quantity, prix_vente, id_client, montant]):
            return jsonify({'error': 'Données de commande incomplètes'}), 400

        # Insérer l'élément de commande dans la base de données
        cursor = conn.cursor()
        try:
            # Insérer l'élément de commande dans la base de données
            if role == 'admin':
                cursor.execute(
                    """INSERT INTO commande (id_client, id_produit, Quantite, prix_vente, Montant, date_commande, statut, id_admin)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (id_client, product_id, quantity, prix_vente, montant, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'En cours', utilisateur_id)
                )
            else:
                cursor.execute(
                    """INSERT INTO commande (id_client, id_produit, Quantite, prix_vente, Montant, date_commande, statut, id_utilisateur)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (id_client, product_id, quantity, prix_vente, montant, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'En cours', utilisateur_id)
                )
            conn.commit()
            
            # Mettre à jour le stock du produit
            cursor.execute(
                'UPDATE produit SET stock = stock - %s WHERE id_produit = %s',
                (quantity, product_id)
            )
            conn.commit()
            
            flash('Commande ajoutée avec succès', 'success')
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cursor.close()

    # Préparer la réponse
    response_data = {'message': 'Commande traitée avec succès'}

    return jsonify(response_data), 200


@app.route('/donnee_commande/<int:ligne_id>', methods=['GET'])
def donnee_commande(ligne_id):
    # Exécuter la requête SQL pour récupérer la date associée à l'ID de la ligne
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date_commande FROM commande WHERE id_commande = %s", (ligne_id,))
    date_commande = cursor.fetchone()[0]  # Récupérer la date de la première colonne

    # Ensuite, utilisez cette date pour récupérer les données associées
    cursor.execute(
        "SELECT produit.designation, commande.quantite, commande.prix_vente, commande.montant, commande.date_commande,id_commande FROM commande JOIN produit ON commande.id_produit = produit.id_produit WHERE commande.date_commande = %s", (date_commande,))
    resultat1 = cursor.fetchall()
    cursor.close()

    # Formater les données et les renvoyer en tant que réponse JSON
    data = [{'designation': row[0], 'quantite': row[1], 'prix_vente': row[2], 'montant': row[3], 'date_commande': row[5]} for row in resultat1]

    return jsonify(data)

@app.route('/admin/modifier_produit/<int:id>',methods=['POST','GET'])
def modifier_produit(id):
        # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    admin_id = session['admin_id']
    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    curso = conn.cursor()
    curso.execute("SELECT * from produit where id_produit=%s",(id,))
    resultat = curso.fetchone()
    image_actuel = resultat[7].decode('utf-8')
    curso.close()
    if request.method == 'POST':
        nom = request.form['nom']
        categorie = request.form['categorie']
        designation = request.form['description']
        prix = request.form['prix']
        stock_min = request.form['nombre']
        image= request.files['image']

        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        curso = conn.cursor()
        curso.execute("UPDATE produit SET   nom_produit = %s, categorie = %s, prix = %s, stock_min = %s, designation = %s, image = %s WHERE id_produit = %s",
            ( nom, categorie,prix,stock_min,designation,filename, id))
        conn.commit()
        curso.close()
        flash('produit modifié avec succès', 'success')
        return redirect(url_for('Produit'))
    return render_template("modifier_produit.html",resultat=resultat,filename=filename,image_actuel=image_actuel)

@app.route('/admin/modifier_client/<int:id>', methods=['POST', 'GET'])
def modifier_client(id):
        # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    
    admin_id = session['admin_id']
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    cursor.execute("SELECT * from client where id_client=%s", (id,))
    client_actuel = cursor.fetchone()
    cursor.close()

    if request.method == 'POST':
        nom = request.form['nom']
        telephone = request.form['tel']
        email = request.form['email']
        adresse = request.form['adresse']

        # Ajout automatique du préfixe +225 si nécessaire et validation du numéro
        telephone = '225' + telephone.lstrip('225')
        if len(telephone) != 13 or not telephone[3:].isdigit() or not (telephone[3:5] in ['07', '05', '01']):
            flash('Le numéro de téléphone doit être valide et contenir 13 chiffres y compris le préfixe 225.', 'danger')
            return redirect(url_for('modifier_client', id=id))

        # Vérification de l'unicité du numéro de téléphone
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM client WHERE telephone = %s AND id_client != %s", (telephone, id))
        if cursor.fetchone():
            flash('Ce numéro de téléphone est déjà utilisé par un autre client.', 'danger')
            return redirect(url_for('modifier_client', id=id))

        # Vérification de l'unicité de l'email
        cursor.execute("SELECT * FROM client WHERE email = %s AND id_client != %s", (email, id))
        if cursor.fetchone():
            flash('Cet email est déjà utilisé par un autre client.', 'danger')
            return redirect(url_for('modifier_client', id=id))

        # Mise à jour des informations du client
        cursor.execute("""
            UPDATE client SET nom_prenoms = %s, telephone = %s, email = %s, adresse = %s
            WHERE id_client = %s
            """, (nom, telephone, email, adresse, id))
        conn.commit()
        cursor.close()
        return redirect(url_for('clients'))

    return render_template('modifier_client.html', resultat=client_actuel, filename=filename)

@app.route('/admin/modifier_fournisseur/<int:id>',methods=['POST','GET'])
def modifier_fournisseur(id):
        # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    
    admin_id = session['admin_id']
    cursor = conn.cursor()
    # Récupérer les informations de l'administrateur en utilisant son ID
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    
    curso = conn.cursor()
    curso.execute("SELECT * from fournisseur where id_fournisseur=%s",(id,))
    resultat = curso.fetchone()
    # image_actuel = resultat[7].decode('utf-8')
    curso.close()

    if request.method == 'POST':
        nom = request.form['nom']
        telephone = request.form['tel']
        Email = request.form['email']
        adresse = request.form['adresse']

        curso = conn.cursor()
        curso.execute("UPDATE fournisseur SET   nom_prenoms = %s, telephone = %s, email = %s, adresse = %s  WHERE id_fournisseur = %s",
            ( nom, telephone,Email,adresse, id))
        conn.commit()
        curso.close()
        flash('Fournisseur modifié avec succès', 'success')
        return redirect(url_for('fournisseurs'))

    return render_template('modifier_fournisseur.html', resultat=resultat ,filename=filename )

@app.route('/admin/supprimer_stock/<int:id>', methods=['GET', 'POST'])
def supprimer_stock(id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))  # Rediriger si l'administrateur n'est pas connecté

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stock WHERE id_stock = %s", (id,))
    resultat = cursor.fetchone()
    cursor.close()

    if resultat is None:
        flash('Stock non trouvé', 'danger')
        return redirect(url_for('stock'))  # Rediriger si le stock n'est pas trouvé

    if request.method == 'POST':
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stock WHERE id_stock = %s", (id,))
        conn.commit()
        cursor.close()
        flash('Stock supprimé avec succès', 'success')
        return redirect(url_for('stock'))

    # Si vous voulez afficher une page de confirmation via une route GET, vous pouvez inclure cela :
    return render_template('stock.html', stock=resultat)


    # supprimer membre

@app.route('/admin/supprimer_membre/<int:id>', methods=['GET', 'POST'])
def supprimer_membre(id):
    if 'admin_id' not in session:
         return redirect(url_for('login'))  # Rediriger si l'administrateur n'est pas connecté
        
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM utilisateur WHERE id_utilisateur = %s", (id,))
    resultat = cursor.fetchone()
    cursor.close()

    if resultat is None:
        flash('membre non trouvé', 'danger')
        return redirect(url_for('equipe'))  # Rediriger si le stock n'est pas trouvé

    if request.method == 'POST':
        cursor = conn.cursor()
        cursor.execute("DELETE FROM utilisateur WHERE id_utilisateur = %s", (id,))
        conn.commit()
        cursor.close()
        flash('membre supprimé avec succès', 'success')
        return redirect(url_for('equipe'))

    # Si vous voulez afficher une page de confirmation via une route GET, vous pouvez inclure cela :
    return render_template('/membre/equipe.html',resultat =resultat)

# supprimer produit  

@app.route('/admin/supprimer_produit/<int:id>', methods=['GET', 'POST'])
def supprimer_produit(id):
    if 'admin_id' not in session:
         return redirect(url_for('login'))  # Rediriger si l'administrateur n'est pas connecté
        
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produit WHERE id_produit = %s", (id,))
    resultat = cursor.fetchone()
    cursor.close()

    if resultat is None:
        flash('membre non trouvé', 'danger')
        return redirect(url_for('Produit'))  # Rediriger si le stock n'est pas trouvé

    if request.method == 'POST':
        cursor = conn.cursor()
        cursor.execute("DELETE FROM produit WHERE id_produit = %s", (id,))
        conn.commit()
        cursor.close()
        flash('membre supprimé avec succès', 'success')
        return redirect(url_for('Produit'))

    # Si vous voulez afficher une page de confirmation via une route GET, vous pouvez inclure cela :
    return render_template('Produit.html',resultat =resultat)


@app.route('/status_client/<entry_id>', methods=['POST'])
def status_client(entry_id):
    if request.method == 'POST':
        # Récupérer le nouveau statut envoyé depuis le formulaire
        new_status = request.form.get('status')

        # Mettre à jour le statut dans la base de données
        cursor = conn.cursor()
        cursor.execute("UPDATE client SET statut = %s WHERE id_client = %s", (new_status, entry_id))
        conn.commit()
        cursor.close()

        # Rediriger vers la page d'achats après la mise à jour du statut
        return redirect(url_for('clients'))
    else:
        # Si la méthode de la requête n'est pas POST, retourner une erreur 405 (Méthode non autorisée)
        return jsonify({'error': 'Method Not Allowed'}), 405

@app.route('/admin/supprimer_client/<int:id>', methods=['GET', 'POST'])
def supprimer_client(id):
    # Vérifiez si l'utilisateur est connecté en tant qu'administrateur
    if 'admin_id' not in session:
        flash('Veuillez vous connecter en tant qu\'administrateur.', 'danger')
        return redirect(url_for('userLogin'))
    
    admin_id = session['admin_id']
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
    infos_admin = cursor.fetchone()
    filename = infos_admin[7].decode('utf-8')

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM client WHERE id_client = %s", (id,))
    resultat = cursor.fetchone()
    cursor.close()

    if resultat is None:
        flash('client non trouvé', 'danger')
        return redirect(url_for('clients'))  # Rediriger si le stock n'est pas trouvé

    if request.method == 'POST':
        cursor = conn.cursor()
        cursor.execute("DELETE FROM client WHERE id_client = %s", (id,))
        conn.commit()
        cursor.close()
        flash('Client  supprimé avec succès', 'success')
        return redirect(url_for('clients'))

    # Si vous voulez afficher une page de confirmation via une route GET, vous pouvez inclure cela :
    return render_template('clients.html', client=resultat, filename=filename)

@app.route('/admin/supprimer_fournisseur/<int:id>', methods=['GET', 'POST'])
def supprimer_fournisseur(id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))  # Rediriger si l'administrateur n'est pas connecté

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fournisseur WHERE id_fournisseur = %s", (id,))
    resultat = cursor.fetchone()
    cursor.close()

    if resultat is None:
        flash('fournisseur non trouvé', 'danger')
        return redirect(url_for('fournisseurs'))  # Rediriger si le stock n'est pas trouvé

    if request.method == 'POST':
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fournisseur WHERE id_fournisseur = %s", (id,))
        conn.commit()
        cursor.close()
        flash('Fournisseur  supprimé avec succès', 'success')
        return redirect(url_for('fournisseurs'))

    # Si vous voulez afficher une page de confirmation via une route GET, vous pouvez inclure cela :
    return render_template('fournisseurs.html', fournisseur=resultat)


@app.route('/admin/supprimer_vente/<int:id>', methods=['GET', 'POST'])
def supprimer_vente(id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))  # Rediriger si l'administrateur n'est pas connecté

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vente WHERE id_vente = %s", (id,))
    resultat = cursor.fetchone()
    cursor.close()

    if resultat is None:
        flash('vente non trouvé', 'danger')
        return redirect(url_for('ventes'))  # Rediriger si le stock n'est pas trouvé

    if request.method == 'POST':
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vente WHERE id_vente = %s", (id,))
        conn.commit()
        cursor.close()
        flash('vente  supprimée avec succès', 'success')
        return redirect(url_for('ventes'))

    # Si vous voulez afficher une page de confirmation via une route GET, vous pouvez inclure cela :
    return render_template('ventes.html', vente=resultat)

@app.route('/admin/supprimer_commande/<int:id>', methods=['GET', 'POST'])
def supprimer_commande(id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))  # Rediriger si l'administrateur n'est pas connecté

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM commande WHERE id_commande = %s", (id,))
    resultat = cursor.fetchone()
    cursor.close()

    if resultat is None:
        flash('commande non trouvé', 'danger')
        return redirect(url_for('commandes'))  # Rediriger si le stock n'est pas trouvé

    if request.method == 'POST':
        cursor = conn.cursor()
        cursor.execute("DELETE FROM commande WHERE id_commande = %s", (id,))
        conn.commit()
        cursor.close()
        flash('commande  supprimée avec succès', 'success')
        return redirect(url_for('commandes'))

    # Si vous voulez afficher une page de confirmation via une route GET, vous pouvez inclure cela :
    return render_template('commandes.html', commande=resultat)

@app.route('/admin/supprimer_achat/<int:id>', methods=['GET', 'POST'])
def supprimer_achat(id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))  # Rediriger si l'administrateur n'est pas connecté

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entree WHERE id_entree = %s", (id,))
    resultat = cursor.fetchone()
    cursor.close()

    if resultat is None:
        flash('achat non trouvé', 'danger')
        return redirect(url_for('achats'))  # Rediriger si le stock n'est pas trouvé

    if request.method == 'POST':
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entree WHERE id_entree = %s", (id,))
        conn.commit()
        cursor.close()
        flash('achat  supprimé avec succès', 'success')
        return redirect(url_for('achats'))

    # Si vous voulez afficher une page de confirmation via une route GET, vous pouvez inclure cela :
    return render_template('achats.html', vente=resultat)

def get_client_phones():
    cursor = conn.cursor()
    cursor.execute("SELECT telephone FROM client")
    phones = cursor.fetchall()
    cursor.close()
    return [str(phone[0]) for phone in phones]


def validate_and_format_phone(phone):
    # This is a simple validation and formatting example.
    # Modify this function based on the expected format of your phone numbers.
    phone = str(phone).strip()
    if phone.startswith("225"):
        return phone
    elif phone.startswith("0"):
        return "225" + phone[1:]
    else:
        return "225" + phone

@app.route("/admin/emailing//")
def emailing():
    if 'admin_id' in session:
        admin_id = session['admin_id']
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM administrateur WHERE id_admin = %s', (admin_id,))
        infos_admin = cursor.fetchone()
        cursor.close()
        filename = infos_admin[7].decode('utf-8')

        return render_template('emailing.html', filename=filename)
    else:
        flash('Veuillez vous connecter', 'danger')
        return redirect(url_for('adminIndex'))


@app.route('/admin/envoyer_sms', methods=['POST'])
def envoyer_sms():
    if 'admin_id' in session:
        message = request.form['message']
        sender_id = "YellikaSMS"  # Changez cette valeur pour votre nom d'expéditeur souhaité

        if not message:
            flash('Message non fourni', 'error')
            return redirect(url_for('emailing'))

        client_phones = get_client_phones()
        responses = []

        for phone in client_phones:
            formatted_phone = validate_and_format_phone(phone)
            print(f"Formatted phone: {formatted_phone}")  # Print formatted phone for debugging
            response = envoyer_sms_api(formatted_phone, sender_id, message)
            responses.append(response)

        # Print all responses for debugging
        for response in responses:
            print(response)

        if any('requestError' in response for response in responses):
            flash('Erreur lors de l\'envoi de certains SMS', 'error')
        else:
            flash('SMS envoyés avec succès', 'success')

        return redirect(url_for('emailing'))
    else:
        flash('Veuillez vous connecter', 'danger')
        return redirect(url_for('adminIndex'))


# Route pour la recherche
@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    results = search_in_database(keyword)
    return jsonify(results)


# Fonction de recherche dans la base de données
def search_in_database(mot):
    cursor = conn.cursor()
    query = "SELECT * FROM produit WHERE nom_produit LIKE ?"
    result = cursor.execute(query, ('%' + mot + '%',)).fetchall()
    conn.commit()
    cursor.close()
    conn.close()

    # Conversion des résultats en une liste de dictionnaires
    results = []
    for row in result:
        results.append(dict(row))

    return results


# Point d'entrée de l'application
if __name__ == '__main__':
    with app.app_context():
        phones = get_client_phones()
        print("Client phones:", phones)
    app.run(debug=True)





