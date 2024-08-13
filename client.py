import json
import time
import socket
from pythonping import ping


def send_ping(device):
    """
    Belirli aralıklarla cihazın IP adresine ping gönderir.

    Bu fonksiyon, verilen cihazın IP adresine 5 saniyelik aralıklarla ping gönderir. Ping işlemi sırasında bir hata oluşursa,
    hata mesajını yazdırır.

    :param device: Ping gönderilecek cihazın bilgilerini içeren sözlük. Sözlük 'IPHost' anahtarını içermelidir.
    """
    while True:
        time.sleep(5)  # Her 5 saniyede bir ping gönderir.
        try:
            ping(device["IPHost"], verbose=False)  # Cihazın IP adresine ping gönderir.
        except Exception as e:
            print(
                f"ERROR: {device['deviceName']} - Ping failed: {e}"
            )  # Ping işlemi sırasında hata oluşursa hata mesajı yazdırır.


def check_connection(device):
    """
    Cihazın belirli bir port üzerinden bağlantısının olup olmadığını kontrol eder.

    Bu fonksiyon, verilen cihazın IP adresi ve port numarasına bir bağlantı oluşturmaya çalışır. Bağlantı başarılı olursa
    True döner; aksi takdirde False döner.

    :param device: Bağlantı kontrol edilecek cihazın bilgilerini içeren sözlük. Sözlük 'IPHost' ve 'port' anahtarlarını içermelidir.
    :return: Bağlantı başarılıysa True, aksi takdirde False.
    """
    try:
        sock = socket.create_connection(
            (device["IPHost"], device["port"]), timeout=1
        )  # Belirtilen IP ve port üzerinden bağlantı oluşturur.
        sock.close()  # Bağlantıyı kapatır.
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False  # Bağlantı oluşturulamazsa False döner.


def save_config(file_name, data):
    """
    Cihaz verilerini bir JSON dosyasına kaydeder.

    Bu fonksiyon, verilen verileri (data) belirtilen dosya adına (file_name) JSON formatında kaydeder.

    :param file_name: Verilerin kaydedileceği dosya adı.
    :param data: JSON formatında kaydedilecek veriler.
    """
    with open(file_name, "w") as file:
        json.dump(data, file, indent=4)  # Verileri JSON formatında dosyaya kaydeder.
