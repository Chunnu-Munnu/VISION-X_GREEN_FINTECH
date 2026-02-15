import numpy as np
from sklearn.ensemble import IsolationForest

class SolarAnomalyModel:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1)
        self.trained = False

    def train(self, data):
        self.model.fit(data)
        self.trained = True

    def predict(self, sample):
        if not self.trained:
            return 1
        return self.model.predict([sample])[0]
