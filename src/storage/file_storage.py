import csv

from datetime import date

class TaxiRouteFile():

    def store(uniqueid, fieldnames, rows, subprocess):
        BASE_FILE_NAME = f"csv/nyc_taxi-{date.today()}"
        DAILY_FILE_NAME = f"{BASE_FILE_NAME}.csv"
        TEMPORAL_FILE_NAME = f"{BASE_FILE_NAME}-{uniqueid}.csv"

        with open(f"{TEMPORAL_FILE_NAME}", 'a') as fw:
            writer = csv.DictWriter(fw, fieldnames, extrasaction='ignore')
            writer.writerows(rows)
    
        mergecmd = f"cat {TEMPORAL_FILE_NAME} > {DAILY_FILE_NAME}"
        deletecmd = f"rm {TEMPORAL_FILE_NAME}"

        process = subprocess(
            mergecmd, stdin=subprocess.STREAM, stdout=subprocess.STREAM, stderr=subprocess.STREAM, shell=True
        )
        
        process.set_exit_callback(
            lambda retcode: subprocess(deletecmd, stdin=subprocess.STREAM, stdout=subprocess.STREAM, stderr=subprocess.STREAM, shell=True)
        )
