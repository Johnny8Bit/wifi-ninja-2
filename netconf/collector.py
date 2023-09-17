import sys
import time
import logging
import subprocess

import wlcLib


def run():

    subprocess.run(["echo", "NETCONF collector : Running"])
    try:
        while True:
            wlcLib.netconf_loop()
            time.sleep(1)
                
    except KeyboardInterrupt:
        subprocess.run(["clear"])
        subprocess.run(["echo", "NETCONF collector : Stopped"])
        sys.exit()


if __name__ == '__main__':

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s (%(name)s) %(levelname)s:%(message)s", 
        datefmt="%m/%d/%Y %H:%M:%S"
    )
    run()