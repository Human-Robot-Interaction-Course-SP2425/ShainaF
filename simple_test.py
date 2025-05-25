from time import sleep
from utilities import *
from openai import OpenAI
from dotenv import load_dotenv

# init_robot()

# run_seq("reset")
# sleep(1)
# run_seq("yes")
# sleep(5)
# run_seq("happy")
# sleep(5)
# run_seq("sad")
# sleep(10)

load_dotenv(override=True)
print(os.environ.get("OPENAI_API_KEY"))

OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))