import os

import joblib
import pandas as pd
import psycopg2
from dotenv import load_dotenv

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Las mismas columnas que expone la vista y que espera el controller.
# Si cambian aqui, hay que cambiarlas tambien en PredictorRequest.
FEATURES = ["email_type", "country", "city"]
TARGET = "genre"

QUERY = """
    SELECT email_type, country, city, genre
    FROM public.vw_cliente_genero;
"""


def normalizar(valor) -> str:
    """Normalizacion unica de las entradas categoricas.

    El modelo aprende 'usa' y no 'USA'. Si el API recibe 'USA' y no se
    normaliza igual que en el entrenamiento, el OneHotEncoder no reconoce
    la categoria y la prediccion se degrada en silencio.
    """
    return str(valor).strip().lower()


class TrainModel:

    @staticmethod
    def entrenarModelo():

        # se usaron las credenciales para ingresar de manera ocasional (Transaction pooler)
        load_dotenv("/app/.env")
        USER = os.getenv("SUPABASE_USER")
        PASSWORD = os.getenv("SUPABASE_PASSWORD")
        HOST = os.getenv("SUPABASE_HOST")
        PORT = os.getenv("SUPABASE_PORT")
        DBNAME = os.getenv("SUPABASE_DBNAME")
        MODELO_ENTRENADO = os.getenv("MODELO_ENTRENADO")

        if PORT is None:
            print("no se lee el env", flush=True)
            return
        else:
            print("si se lee el env", flush=True)

        # ------------------------------------------------------------------
        # 1. Extraccion: leer la vista creada en Supabase
        # ------------------------------------------------------------------
        try:
            with psycopg2.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DBNAME,
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(QUERY)
                    rows = cursor.fetchall()
                    print(f"Filas recuperadas: {len(rows)}", flush=True)

        except Exception as e:
            print(f"Error al conectar o recuperar datos: {e}", flush=True)
            return

        if not rows:
            print("No se recuperaron filas de la vista. Abortando entrenamiento.", flush=True)
            return

        # ------------------------------------------------------------------
        # 2. Preparacion: aqui NO se usa numpy como en el ejemplo original.
        #    Los datos son texto, no numeros, asi que se trabaja con un
        #    DataFrame y se conservan los nombres de columna: el Pipeline
        #    los necesita para mapear cada columna a su codificador.
        # ------------------------------------------------------------------
        df = pd.DataFrame(rows, columns=FEATURES + [TARGET])
        df = df.dropna(subset=FEATURES + [TARGET])

        for col in FEATURES:
            df[col] = df[col].map(normalizar)

        # El target NO se normaliza: se quiere devolver "Rock" y no "rock".
        # Tampoco se usa LabelEncoder, porque scikit-learn acepta etiquetas
        # de texto directamente y asi se evita tener que guardar un segundo
        # artefacto (el encoder) junto al modelo.
        X = df[FEATURES]
        y = df[TARGET]

        print(f"Registros utiles: {len(df)} | Generos distintos: {y.nunique()}", flush=True)
        print("Distribucion de clases:", flush=True)
        print(y.value_counts().to_string(), flush=True)

        # ------------------------------------------------------------------
        # 3. Split. El dataset es muy pequenio (59 clientes) y hay generos
        #    con un solo registro, asi que stratify solo se aplica si todas
        #    las clases tienen al menos 2 ejemplos.
        # ------------------------------------------------------------------
        estratificar = y if y.value_counts().min() >= 2 else None
        if estratificar is None:
            print("Aviso: hay generos con un solo cliente, no se estratifica el split.", flush=True)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=estratificar
        )

        # ------------------------------------------------------------------
        # 4. Modelo. Predecir un genero es CLASIFICACION multiclase, no
        #    regresion: LinearRegression no aplica porque la salida es una
        #    etiqueta y no un numero continuo.
        #
        #    Todo va dentro de un Pipeline (codificador + clasificador) y se
        #    serializa completo. Asi el API solo carga un archivo y aplica
        #    exactamente la misma transformacion que se uso al entrenar.
        #
        #    handle_unknown="ignore": si llega una ciudad que nunca se vio,
        #    el vector queda en ceros para esa columna en lugar de reventar.
        # ------------------------------------------------------------------
        preprocesador = ColumnTransformer(
            transformers=[
                ("categoricas", OneHotEncoder(handle_unknown="ignore"), FEATURES),
            ]
        )

        modelo = Pipeline(
            steps=[
                ("preprocesador", preprocesador),
                (
                    "clasificador",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",  # Rock domina el dataset
                    ),
                ),
            ]
        )

        modelo.fit(X_train, y_train)

        y_pred = modelo.predict(X_test)
        print(f"Accuracy en test: {accuracy_score(y_test, y_pred):.3f}", flush=True)
        print(classification_report(y_test, y_pred, zero_division=0), flush=True)

        # ------------------------------------------------------------------
        # 5. Reentrenar con el 100% de los datos antes de guardar.
        #    Con 59 filas, dejar fuera el 20% solo para conservarlo seria
        #    desperdiciar informacion: el split ya cumplio su unico proposito,
        #    que era medir.
        # ------------------------------------------------------------------
        modelo.fit(X, y)

        os.makedirs(os.path.dirname(MODELO_ENTRENADO), exist_ok=True)
        joblib.dump(modelo, MODELO_ENTRENADO)
        print(f"modelo entrenado y guardado en {MODELO_ENTRENADO}", flush=True)
