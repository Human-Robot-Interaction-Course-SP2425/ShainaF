from time import sleep
from utils import *

init_robot()

run_seq("reset")
sleep(1)
run_seq("yes")
sleep(5)
run_seq("happy")
sleep(5)
run_seq("sad")
sleep(10)
