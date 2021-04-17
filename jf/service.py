import json
import yaml
import numpy as np
import datetime
from jf.process import JFTransformation


def json_encodings(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        obj.isoformat()
    if isinstance(obj, (np.int64)):
        return int(obj)
    if isinstance(obj, (np.float)):
        return float(obj)


class RESTful(JFTransformation):
    def _fn(self, arr):
        from flask import Flask, request, Response
        from flask_cors import CORS

        base_path = ""
        if len(self.args) > 0:
            base_path = self.args[0]
        model = next(iter(arr))
        yield "Starting restful service"
        print("Model: {}".format(model))
        yield "BasePath: {}".format(base_path)

        app = Flask(__name__)

        def get_request_data():
            data = request.get_json(force=True, silent=True)
            if data is not None:
                return data
            try:
                data = yaml.load(request.data)
                if data is not None:
                    return daata
            except:
                pass
            data = []
            for line in request.data.decode().replace("}{", "}\n{").split("\n"):
                data.append(json.loads(line))
            return data

        @app.route(f"{base_path}/transform", methods=["POST", "GET"])
        def transform():
            if request.method == "POST":
                data = get_request_data()
                results = list(model.transform(data))
                return Response(json.dumps(results), 200)
                # prediction = list(model.predict(data))

        @app.route(f"{base_path}/predict", methods=["POST", "GET"])
        def predict():
            if request.method == "POST":
                data = get_request_data()
                results = model.predict(data)
                try:
                    probs = model.predict_proba(data)
                    prediction = [list(x) for x in probs]
                    return Response(json.dumps(list(zip(results, prediction))), 200)
                except:
                    pass
                return Response(json.dumps(list(results)), 200)
                # prediction = list(model.predict(data))

        CORS(app)
        app.run(port=self.kwargs.get("port", 5002))
