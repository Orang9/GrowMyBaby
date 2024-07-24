from flask import Flask, request, jsonify
import os
from pymongo import MongoClient

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise ValueError("MONGO_URI environment variable not set")

client = MongoClient(mongo_uri)
db = client["sic5_belajar"]
data_store = []

@app.route('/data', methods=['POST'])
def save_data():
    data = request.get_json()
    data_store.append(data)
    return jsonify({"message": "Data berhasil disimpan", "data": data}), 201

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(data_store), 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
