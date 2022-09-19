import uuid
import io

import tornado.web
import tornado.process
import tornado.gen

from src.domain.taxi_route import TaxiRoute

@tornado.web.stream_request_body
class DataReceiverHandler(tornado.web.RequestHandler):

    def initialize(self):
        self.request_body = b''

    def data_received(self, chunk):
        self.request_body += chunk        

    @tornado.gen.coroutine
    def post(self):
        REQUEST_ID = self.request.headers.get("request-id") or str(uuid.uuid4())
        fr = io.BytesIO(self.request_body)

        result = TaxiRoute.storeroutes(REQUEST_ID, fr, tornado.process.Subprocess)

        result['result']['stats']['bytes'] = len(self.request_body)

        self.write(result)