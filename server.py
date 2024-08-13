import socket
import threading
import json
from devices import device_data, file_path
from rabbitmq import start_rabbitmq_consumer
import client
import random

port_listeners = {}


def port_dinle(device):
    """
    Bir cihazın belirtilen IP ve portu üzerinde dinleme yapar.
    Bağlantı geldiğinde, istemciyle ilgili işlemleri yapacak bir iş parçacığı başlatır.

    :param device: Dinleme yapılacak cihazın bilgilerini içeren sözlük. Sözlük 'IPHost', 'port', ve 'commands' anahtarlarını içermelidir.
    """
    ip = device["IPHost"]
    port = device["port"]
    commands = device["commands"]
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((ip, port))
    server_socket.listen(len(device_data))
    port_listeners[port] = server_socket
    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(
            target=client_handler, args=(client_socket, commands, device["deviceName"])
        ).start()


def stop_port_listening(port):
    """
    Belirli bir port üzerinde dinlemeyi durdurur ve portu kapatır.

    :param port: Dinlemenin durdurulacağı port numarası.
    """
    if port in port_listeners:
        server_socket = port_listeners.pop(port)
        server_socket.close()
        print(f"Port kapatıldı: {port}")


def client_handler(client_socket, commands, device_name):
    """
    İstemciden gelen verileri işler ve uygun yanıtı gönderir.
    Verilen komutlardan biri mevcutsa 1 ile 100 arasında rastgele bir sayı, aksi takdirde 0 gönderir.

    :param client_socket: İstemci ile olan bağlantı soketi.
    :param commands: Geçerli komutların listesi.
    :param device_name: Cihazın adı.
    """
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            received_command = data.decode("utf-8")
            response = (
                str(random.randint(1, 100)) if received_command in commands else "0"
            )
            client_socket.sendall(response.encode("utf-8"))
        except ConnectionResetError:
            break
    client_socket.close()


def start_listenindg():
    """
    Tüm cihazların portlarını dinlemeye başlar ve RabbitMQ tüketicisini başlatır.
    """
    for device in device_data:
        threading.Thread(target=port_dinle, args=(device,)).start()
    threading.Thread(target=start_rabbitmq_consumer, args=(callback,)).start()


def callback(ch, method, properties, body):
    """
    RabbitMQ'dan gelen mesajlara göre cihaz ekler, günceller veya siler.
    Güncellenmiş cihaz verilerini kaydeder.

    :param ch: RabbitMQ kanal nesnesi.
    :param method: Mesajın yöntem bilgileri.
    :param properties: Mesajın özellikleri.
    :param body: Mesajın gövdesi, JSON formatında cihaz bilgilerini içerir.
    """
    data = json.loads(body)
    event_type = data.get("event")  # Mesajın olay türünü alır (add, edit, delete).
    device = data.get("device")  # Mesajın içindeki cihaz bilgilerini alır.

    if event_type == "add":
        # Yeni bir cihaz eklenmişse, cihazı `device_data` listesine ekler.
        device_data.append(device)
        threading.Thread(target=port_dinle, args=(device,)).start()
        print(
            f"Yeni cihaz eklendi: Adı: {device['deviceName']}, Port: {device['port']}, Komutlar: {device['commands']}"
        )
    elif event_type == "edit":
        # Cihaz güncellenmişse, `device_data` listesindeki eski cihazı yenisiyle değiştirir.
        for i, d in enumerate(device_data):
            if d["deviceName"] == device["deviceName"]:
                device_data[i] = device
                break
        # Cihazın bağlantılarını yeniden başlatır.
        restart_device_connections(device)
        print(
            f"Cihaz güncellendi: Adı: {device['deviceName']}, Port: {device['port']}, Komutlar: {device['commands']}"
        )
    elif event_type == "delete":
        # Cihaz silinmişse, `device_data` listesinden cihazı çıkarır.
        device_data[:] = [
            d for d in device_data if d["deviceName"] != device["deviceName"]
        ]
        # Cihazın port dinlemeyi durdurur.
        stop_port_listening(device["port"])
        print(f"Cihaz silindi: Adı: {device['deviceName']}, Port: {device['port']}")

    client.save_config(file_path, device_data)


def restart_device_connections(updated_device):
    """
    Güncellenmiş cihazın bağlantılarını yeniden başlatır ve gerekli port dinleme iş parçacığını oluşturur.

    :param updated_device: Güncellenmiş cihazın bilgilerini içeren sözlük.
    """
    for thread in threading.enumerate():
        if thread.name.startswith(updated_device["deviceName"]):
            thread.join()
    threading.Thread(
        target=port_dinle, args=(updated_device,), name=updated_device["deviceName"]
    ).start()


if __name__ == "__main__":
    start_listenindg()
