import numpy as np
import joblib
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv


from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

class TrainModel:

    def entrenarModelo():

        #se usaron las credeciales para ingresar de manera ocacional (Transaction pooler)
        load_dotenv("/app/.env")
        USER = os.getenv("SUPABASE_USER")
        PASSWORD = os.getenv("SUPABASE_PASSWORD")
        HOST = os.getenv("SUPABASE_HOST")
        PORT = os.getenv("SUPABASE_PORT")
        DBNAME = os.getenv("SUPABASE_DBNAME")
        

        if(PORT== None):
            print("no se lee el env")
            return
        else:
            print("si se lee en env")


        try:
            with psycopg2.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DBNAME
            ) as connection:
                with connection.cursor() as cursor:
                    # Consulta SQL
                    cursor.execute('SELECT x, y FROM "Dataset";')
                    rows = cursor.fetchall()  # devuelve una lista de tuplas [(x1,y1),(x2,y2),...]
                    
                    print(f"Filas recuperadas: {len(rows)}")

        except Exception as e:
            print(f"Error al conectar o recuperar datos: {e}")
            return
        
        if not rows:
            print("No se recuperaron filas de la base de datos. Abortando entrenamiento.")
            return
        else:
            print(rows[:2])
            

        # Convertir la lista de tuplas a un array de NumPy
        data_array = np.array(rows)  # shape (num_filas, 2)

        # Separar columnas
        x = data_array[:, 0].reshape(-1, 1)  # 100 x 1
        y = data_array[:, 1].reshape(-1, 1)  # 100 x 1

        #dividir en entranamiento y prueba
        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)
        
        #entrenar el modelo
        
        model = LinearRegression()
        model.fit(x_train, y_train)
        joblib.dump(model, str(os.getenv("MODELO_ENTRENADO")))
        print("modelo entrenado")
        
