import sqlite3
from datetime import datetime

# Connexion à la base de données
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Récupérer toutes les lignes de la table home_event
cursor.execute("SELECT id, begindatetime, enddatetime FROM home_event")
rows = cursor.fetchall()

for row in rows:
    event_id = row[0]
    begindatetime = row[1]
    enddatetime = row[2]

    # Si la date n'est pas NULL, vérifier si elle est déjà au bon format
    if begindatetime:
        try:
            # Tenter de parser avec le format attendu
            new_begindatetime = datetime.strptime(begindatetime, '%d/%m/%Y %H:%M').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Si échec, conserver la date telle quelle
            new_begindatetime = begindatetime

    if enddatetime:
        try:
            # Tenter de parser avec le format attendu
            new_enddatetime = datetime.strptime(enddatetime, '%d/%m/%Y %H:%M').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            # Si échec, conserver la date telle quelle
            new_enddatetime = enddatetime

    # Mise à jour des valeurs dans la table
    cursor.execute("""
        UPDATE home_event 
        SET begindatetime = ?, enddatetime = ? 
        WHERE id = ?
    """, (new_begindatetime, new_enddatetime, event_id))

# Confirmer les changements
conn.commit()
conn.close()
