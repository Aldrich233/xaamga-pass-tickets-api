import csv

# Assurez-vous que le fichier CSV est correctement formaté
with open('home_event.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    
    # Imprimer les en-têtes pour vérifier les noms de colonnes
    id_list = [
        68, 60, 50, 59, 63, 55, 48, 62, 56, 57, 
        69, 61, 46, 47, 64, 49, 65, 58, 66, 54, 
        67, 74, 75, 76, 77, 78, 79, 53, 72, 71, 
        52, 70, 51, 73
    ]
    i=0
    
    for row in reader:
        # Imprimer les lignes pour vérifier les données
        id = id_list[i]  # Vérifiez que 'id' est bien présent
        begindatetime = row['begindatetime']
        enddatetime = row['enddatetime']
        
        sql = f"""
        UPDATE home_event
        SET begindatetime = '{begindatetime}',
            enddatetime = '{enddatetime}'
        WHERE id = {id};
        """
        print(sql)
        i+=1
