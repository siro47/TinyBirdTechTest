import io
import json

from datetime import date

from src.storage.file_storage import TaxiRouteFile

class TaxiRoute():
    def storeroutes(uniqueid, inputfile, subprocess):
        # Subprocess is still tied to the tornado web server for quick binding stdin, stdout...
        # The ideal solution will be to use the os subprocess directly to get rid of every web server framework dependency

        BATCH_SIZE = 1000

        records_valid = 0
        records_invalid = 0
        
        fieldnames = [
            'vendorid',
            'tpep_pickup_datetime',
            'trip_distance',
            'total_amount',
        ]
                    
        rows = []
        counter = 0

        for record in inputfile.readlines():
            try:
                rows.append(json.loads(record))
                records_valid += 1
            except Exception:
                records_invalid +=1

        TaxiRouteFile.store(uniqueid, fieldnames, rows, subprocess)
            
        result = {
            'result': {
                'status': 'ok',
                'stats': {
                    'records': {
                        'valid': records_valid,
                        'invalid': records_invalid,
                        'total': records_valid + records_invalid,
                    },
                }
            }
        }

        return result