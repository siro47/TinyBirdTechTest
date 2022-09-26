import csv
import io
import json
import sys
import tornado.ioloop
import tornado.web
from tornado.process import Subprocess

from datetime import date
import uuid


@tornado.web.stream_request_body
class DataReceiverHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.request_body = b''
        self.uniqueid = self.request.headers.get("request-id") or str(uuid.uuid4())

    def data_received(self, chunk):
        self.request_body += chunk

    def post(self):
        BATCH_SIZE = 1000
        
        BASE_FILE_NAME = f"csv/nyc_taxi-{date.today()}"
        DAILY_FILE_NAME = f"{BASE_FILE_NAME}.csv"
        TEMPORAL_FILE_NAME = f"{BASE_FILE_NAME}-{self.uniqueid}.csv"

        records_valid = 0
        records_invalid = 0
        
        with open(TEMPORAL_FILE_NAME, 'a') as fw:
            fieldnames = [
                'vendorid',
                'tpep_pickup_datetime',
                'trip_distance',
                'total_amount',
            ]
            writer = csv.DictWriter(fw, fieldnames, extrasaction='ignore')
            fr = io.BytesIO(self.request_body)
            
            rows = []
            counter = 0

            def reset_batch():
                rows.clear()
                counter = 0

            for record in fr.readlines():
                try:
                    rows.append(json.loads(record))
                    counter +=1
                    if (counter >= BATCH_SIZE):
                        writer.writerows(rows)
                        records_valid += len(rows)
                        reset_batch()
                except Exception:
                    records_invalid +=1
            
            # Store last batch
            writer.writerows(rows)
            records_valid += len(rows)

        mergecmd = f"cat {TEMPORAL_FILE_NAME} > {DAILY_FILE_NAME}"
        deletecmd = f"rm {TEMPORAL_FILE_NAME}"

        STREAM = Subprocess.STREAM

        process = Subprocess(
            mergecmd, stdin=STREAM, stdout=STREAM, stderr=STREAM, shell=True
        )
        
        process.set_exit_callback(
            lambda retcode: Subprocess(deletecmd, stdin=STREAM, stdout=STREAM, stderr=STREAM, shell=True)
        )     
        
        result = {
            'result': {
                'status': 'ok',
                'stats': {
                    'bytes': len(self.request_body),
                    'records': {
                        'valid': records_valid,
                        'invalid': records_invalid,
                        'total': records_valid + records_invalid,
                    },
                }
            }
        }
        self.write(result)

def run():
    handlers = [
        (r"/", DataReceiverHandler),
    ]
    debug = bool(sys.flags.debug)
    settings = {
        'debug': debug
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
