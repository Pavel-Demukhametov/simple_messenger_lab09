import tornado.ioloop
import tornado.web
import tornado.websocket
import redis
import threading
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger()

try:
    redis_connection = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_connection.ping()
    log.info("Подключение к Redis прошло успешно.")
except redis.ConnectionError as e:
    log.error(f"Ошибка подключения к Redis: {e}")
    exit(1)

CHANNEL = "chat_channel"
connected_clients = set()

io_loop = tornado.ioloop.IOLoop.current()

def redis_listener():
    pubsub = redis_connection.pubsub()
    pubsub.subscribe(CHANNEL)
    for message in pubsub.listen():
        if message['type'] == 'message':
            log.info(f"Получено новое сообщение: {message['data']}")
            io_loop.add_callback(forward_message_to_clients, message['data'])

def forward_message_to_clients(msg):
    if not connected_clients:
        log.warning("Нет подключенных клиентов для доставки сообщения.")
        return

    log.info(f"Доставка сообщения {msg} {len(connected_clients)} клиентам.")
    message_data = {"type": "message", "content": msg}
    serialized_data = json.dumps(message_data)
    for client in connected_clients:
        try:
            client.write_message(serialized_data)
            log.info(f"Сообщение отправлено клиенту {id(client)}: {serialized_data}")
        except Exception as e:
            log.error(f"Ошибка отправки сообщения клиенту {id(client)}: {e}")

def update_client_list():
    client_names = [f"User-{id(client)}" for client in connected_clients]
    client_update_message = {"type": "clients", "clients": client_names}
    serialized_list = json.dumps(client_update_message)
    for client in connected_clients:
        try:
            client.write_message(serialized_list)
            log.info(f"Обновление списка клиентов отправлено клиенту {id(client)}")
        except Exception as e:
            log.error(f"Ошибка отправки обновления списка клиенту {id(client)}: {e}")

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        self.user_id = str(id(self))
        log.info(f"Клиент {self.user_id} подключен.")
        connected_clients.add(self)
        self.send_user_id()
        update_client_list()

    def send_user_id(self):
        user_message = {"type": "client_id", "client_id": self.user_id}
        self.write_message(json.dumps(user_message))
    
    def on_message(self, message):
        log.info(f"Получено сообщение от клиента {self.user_id}: {message}")
        try:
            redis_connection.publish(CHANNEL, message)
            log.info(f"Сообщение опубликовано в Redis: {message}")
        except Exception as e:
            log.error(f"Ошибка отправки сообщения в Redis: {e}")

    def on_close(self):
        log.info(f"Клиент {self.user_id} отключен.")
        connected_clients.remove(self)
        update_client_list()

    def check_origin(self, origin):
        return True

class IndexPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

def create_web_application():
    return tornado.web.Application([
        (r"/", IndexPageHandler),
        (r"/ws", WebSocketHandler),
    ], static_path="static", template_path="templates")

redis_thread = threading.Thread(target=redis_listener)
redis_thread.daemon = True
redis_thread.start()

application = create_web_application()
application.listen(8888)
log.info("Сервер работает на http://localhost:8888")
tornado.ioloop.IOLoop.current().start()
