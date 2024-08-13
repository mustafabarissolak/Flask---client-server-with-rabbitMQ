from flask import Flask, render_template, request, redirect, url_for, jsonify
import threading
from rabbitmq import send_rabbitmq_message
import client
from devices import device_data, file_path
import server

app = Flask(__name__)


@app.route("/")
def index():
    """
    Ana sayfa.

    Bu rota, 'index.html' şablonunu render eder ve 'device_data' listesindeki cihazları şablona iletir.
    """
    return render_template("index.html", devices=device_data)


@app.route("/device_status")
def device_status():
    """
    Cihaz durumlarını döndürür.

    Bu rota, cihazların bağlantı durumlarını kontrol eder ve JSON formatında döndürür.
    Her cihazın adı ve bağlantı durumu ('connected' veya 'disconnected') içeren bir liste döner.
    """
    status_list = []
    for device in device_data:
        status = "connected" if client.check_connection(device) else "disconnected"
        status_list.append({"deviceName": device["deviceName"], "status": status})
    return jsonify(status_list)


@app.route("/add_device", methods=["GET", "POST"])
def add_device():
    """
    Yeni cihaz ekle.

    Bu rota, cihaz eklemek için kullanılan bir formu gösterir. Form gönderildiğinde, yeni cihaz bilgilerini alır,
    cihazı 'device_data' listesine ekler ve RabbitMQ aracılığıyla mesaj gönderir. Ayrıca cihazın bağlantısını test etmek için
    bir iş parçacığı başlatır. Ardından ana sayfaya yönlendirir.
    """
    if request.method == "POST":
        device_name = request.form["deviceName"]
        ip_host = request.form["IPHost"]
        port = int(request.form["port"])
        commands = request.form["commands"].split(",")
        new_device = {
            "deviceName": device_name,
            "IPHost": ip_host,
            "port": port,
            "commands": [cmd.strip() for cmd in commands],
        }
        device_data.append(new_device)
        client.save_config(file_path, device_data)
        send_rabbitmq_message("add", new_device)
        threading.Thread(target=client.send_ping, args=(new_device,)).start()
        return redirect(url_for("index"))
    return render_template("add_device.html")


@app.route("/edit_device/<device_id>", methods=["GET", "POST"])
def edit_device(device_id):
    """
    Cihaz düzenle.

    Bu rota, belirli bir cihazı düzenlemek için kullanılan bir formu gösterir. Form gönderildiğinde, cihaz bilgilerini günceller
    ve değişiklikleri RabbitMQ aracılığıyla gönderir. Ardından ana sayfaya yönlendirir.
    """
    device = next((d for d in device_data if d["deviceName"] == device_id), None)
    if request.method == "POST":
        device["deviceName"] = request.form["deviceName"]
        device["IPHost"] = request.form["IPHost"]
        device["port"] = int(request.form["port"])
        device["commands"] = [
            cmd.strip() for cmd in request.form["commands"].split(",")
        ]
        client.save_config(file_path, device_data)
        send_rabbitmq_message("edit", device)
        return redirect(url_for("index"))
    return render_template("edit_device.html", device=device)


@app.route("/edit_device_inline/<device_id>", methods=["POST"])
def edit_device_inline(device_id):
    """
    Cihaz bilgilerini JSON formatında düzenle.

    Bu rota, cihaz bilgilerini JSON formatında alır ve günceller. Değişiklikleri RabbitMQ aracılığıyla gönderir ve başarılı
    olduğunda 200 durum kodu döner. Eğer cihaz bulunamazsa 404 durum kodu döner.
    """
    data = request.json
    device = next((d for d in device_data if d["deviceName"] == device_id), None)
    if device:
        device["deviceName"] = data["deviceName"]
        device["IPHost"] = data["IPHost"]
        device["port"] = int(data["port"])
        device["commands"] = [cmd.strip() for cmd in data["commands"].split(",")]
        client.save_config(file_path, device_data)
        send_rabbitmq_message("edit", device)
        return "", 200
    return "", 404


@app.route("/delete_device/<device_id>", methods=["DELETE"])
def delete_device(device_id):
    """
    Cihaz sil.

    Bu rota, belirli bir cihazı 'device_data' listesinden kaldırır ve RabbitMQ aracılığıyla bir silme mesajı gönderir.
    Başarıyla silindiğinde 204 durum kodu döner. Eğer cihaz bulunamazsa 404 durum kodu döner.
    """
    device_delete = next((d for d in device_data if d["deviceName"] == device_id), None)
    if device_delete:
        device_data.remove(device_delete)
        client.save_config(file_path, device_data)
        send_rabbitmq_message("delete", device_delete)
        return "", 204
    return "", 404


if __name__ == "__main__":
    """
    Flask uygulamasını başlatır, sunucuyu dinlemeye başlar ve mevcut cihazlar için bağlantıyı test eden iş parçacıkları
    başlatır. Flask uygulamasının debug modunda çalışmasını sağlar.
    """
    server.start_listenindg()
    for device in device_data:
        threading.Thread(target=client.send_ping, args=(device,)).start()
    app.run(debug=True)
