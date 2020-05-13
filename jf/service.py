import json
from flask import Flask, request, Response


def RESTful(args, arr):

    params = args(arr)
    base_path = params
    model = next(iter(arr))
    yield "Starting restful service"
    print("Model: {}".format(model))
    yield "BasePath: {}".format(base_path)

    app = Flask(__name__)

    def get_request_data():
        return request.get_json(force=True, silent=True)

    @app.route(f"{base_path}", methods=["POST", "GET"])
    def predict():
        if request.method == "POST":
            data = get_request_data()
            probs = model.predict_proba(data)
            prediction = [list(x) for x in probs]
            results = model.predict(data)
            # prediction = list(model.predict(data))
            return Response(json.dumps(list(zip(results, prediction))), 200)

    app.run(port="5002")
