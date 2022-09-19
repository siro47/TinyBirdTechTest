import sys
import tornado.ioloop
import tornado.web

from src.api.taxi_route_service import DataReceiverHandler

def run():
    handlers = [
        (r"/", DataReceiverHandler),
    ]
    debug = bool(sys.flags.debug)
    settings = {
        'debug': False
    }
    port = 8888
    address = '0.0.0.0'
    application = tornado.web.Application(handlers, **settings)
    server = tornado.httpserver.HTTPServer(application, max_buffer_size=1024*1024*201)
    server.bind(port)
    server.start(0)

    print(f"server listening at {address}:{port} debug={debug}")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    run()
