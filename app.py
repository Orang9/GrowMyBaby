from flask import Flask, request, jsonify
app = Flask(__name__)

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
    app.run(debug=True, use_reloader=False)
