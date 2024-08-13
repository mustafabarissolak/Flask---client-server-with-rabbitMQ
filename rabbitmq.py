import pika
import json


def create_rabbitmq_connection():
    """
    RabbitMQ sunucusuna bir bağlantı oluşturur.

    Bu fonksiyon, RabbitMQ sunucusuna bağlantı kurmak için 'localhost' adresini kullanarak bir bağlantı nesnesi döner.
    """
    return pika.BlockingConnection(pika.ConnectionParameters("localhost"))


def send_rabbitmq_message(event_type, device):
    """
    RabbitMQ kuyruğuna mesaj gönderir.

    Bu fonksiyon, verilen 'event_type' ve 'device' bilgilerini içeren bir mesaj oluşturur ve bu mesajı RabbitMQ'nun
    "device_updates" kuyruğuna gönderir.

    event_type: Mesajın türü (örneğin, "add", "edit", "delete").
    device: Mesajın içeriği olarak gönderilecek cihaz bilgileri.
    """
    connection = create_rabbitmq_connection()  # Bağlantı oluşturur.
    channel = connection.channel()  # Kanal açar.

    channel.queue_declare(
        queue="device_updates"
    )  # "device_updates" kuyruğunu oluşturur.

    message = {"event": event_type, "device": device}  # Gönderilecek mesajı hazırlar.
    channel.basic_publish(
        exchange="", routing_key="device_updates", body=json.dumps(message)
    )  # Mesajı kuyruğa gönderir.

    connection.close()


def start_rabbitmq_consumer(callback):
    """
    RabbitMQ kuyruğundan mesajları tüketir ve verilen callback fonksiyonunu çağırır.

    Bu fonksiyon, RabbitMQ'nun "device_updates" kuyruğundan mesajları alır ve bu mesajları işlemek için verilen
    'callback' fonksiyonunu çağırır.

    :param callback: Kuyruktan gelen mesajları işlemek için kullanılan callback fonksiyonu.
    """
    connection = create_rabbitmq_connection()  # Bağlantı oluşturur.
    channel = connection.channel()  # Kanal açar.

    channel.queue_declare(
        queue="device_updates"
    )  # "device_updates" kuyruğunu oluşturur.

    channel.basic_consume(
        queue="device_updates", on_message_callback=callback, auto_ack=True
    )  # Kuyruktan gelen mesajları callback fonksiyonu ile işler.
    channel.start_consuming()
