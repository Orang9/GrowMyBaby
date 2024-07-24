from flask import Flask, request, jsonify

app = Flask(__name__)

# Array untuk menyimpan data
data_store = []

@app.route('/data', methods=['POST'])
def save_data():
    # Mendapatkan data dari request
    data = request.get_json()

    # Menyimpan data di array
    data_store.append(data)

    return jsonify({"message": "Data berhasil disimpan", "data": data}), 201

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(data_store), 200

if __name__ == '__main__':
    app.run(debug=True)
