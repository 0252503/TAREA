
from src.contexts.train_model.TrainModel import TrainModel



class CronTrainModelApp:
    def start(self, *, hour):
        ########################
        print(f"start train model cron in hour: {hour}", flush=True)
        TrainModel.entrenarModelo()
