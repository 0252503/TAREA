import os

import joblib
import pandas as pd

from src.contexts.api.models import PredictorRequest

FEATURES = ["email_type", "country", "city"]


class TrainModelController:
    def execute(self, request: PredictorRequest):
        modelo_path = os.getenv("MODELO_ENTRENADO")

        if not modelo_path or not os.path.exists(modelo_path):
            # Si el cron todavia no corrio, el .pkl no existe. Mejor un
            # error explicito que un stacktrace 500 sin explicacion.
            return {
                "status": "ERROR",
                "message": "El modelo aun no ha sido entrenado. Espera a que corra el cron TrainModel.",
            }

        modelo = joblib.load(modelo_path)

        # Se construye un DataFrame con los MISMOS nombres de columna que se
        # usaron al entrenar. El ColumnTransformer selecciona por nombre: si
        # se le pasa un array de numpy suelto, falla o codifica mal.
        nuevo_dato = pd.DataFrame(
            [
                {
                    "email_type": request.email_type,
                    "country": request.country,
                    "city": request.city,
                }
            ],
            columns=FEATURES,
        )

        # El pipeline aplica el OneHotEncoder guardado y luego clasifica,
        # asi que aqui no hay que replicar ninguna transformacion.
        genero = str(modelo.predict(nuevo_dato)[0])

        # predict_proba da el detalle de que tan seguro esta el modelo.
        # Con este dataset casi siempre gana Rock, y el top 3 lo evidencia.
        probabilidades = modelo.predict_proba(nuevo_dato)[0]
        ranking = sorted(
            zip(modelo.classes_, probabilidades),
            key=lambda par: par[1],
            reverse=True,
        )[:3]

        return {
            "status": "OK",
            "input": nuevo_dato.iloc[0].to_dict(),
            "genero_predicho": genero,
            "confianza": round(float(max(probabilidades)), 4),
            "top_3": [
                {"genero": str(clase), "probabilidad": round(float(p), 4)}
                for clase, p in ranking
            ],
        }
