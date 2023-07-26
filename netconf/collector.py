import sys
import time
import logging

import wlcLib


def run():

    #subprocess.run(["echo", "NETCONF collector : Running"])
    try:
        while True:
            wlcLib.netconf_ap_data()
            wlcLib.netconf_wlc_data()
            time.sleep(1)
                
    except KeyboardInterrupt:
        #subprocess.run(["clear"])
        #subprocess.run(["echo", "NETCONF collector : Stopped"])
        sys.exit()


if __name__ == '__main__':

    logging.basicConfig(level=logging.ERROR,
                        format="%(asctime)s (%(name)s) %(levelname)s:%(message)s", 
                        datefmt="%m/%d/%Y %H:%M:%S")
    run()