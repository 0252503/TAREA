import os
import joblib
import numpy as np
import os

from src.contexts.api.models import PredictorRequest



class TrainModelController:
    def execute(self, request: PredictorRequest):
        print(request)
        sex=request.sex.value
        nuevo=request.nuevo
       
        lr_model_path = os.getenv("MODELO_ENTRENADO")
       
        # Cargar el modelo desde el archivo
        modelo_cargado = joblib.load(lr_model_path)

        # Crear un nuevo dato para predecir
        nuevo_dato = np.array([[nuevo]])  # X = 6

        # Hacer la predicción
        result = modelo_cargado.predict(nuevo_dato)
        print(f"Predicción para X=6: {result[0][0]}")
        
        return {"status": "OK", "result": result[0][0]}

    
