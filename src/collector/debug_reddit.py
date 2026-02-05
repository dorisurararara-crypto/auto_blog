import praw
import os
from dotenv import load_dotenv
from prawcore.exceptions import ResponseException

load_dotenv()

def test_reddit(client_id, client_secret):
    user_agent = "python:GTB_Blog:v1.0 (by /u/Training-Run7703)"
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        list(reddit.subreddit("test").hot(limit=1))
        return True
    except ResponseException as e:
        if e.response.status_code == 401:
            return "401 (Unauthorized)"
        if e.response.status_code == 403:
            return "403 (Forbidden)"
        return f"Error: {e.response.status_code}"
    except Exception as e:
        return str(e)

id_base = "d_6QWE1pZuPPPmg81_Pfmw"
id_alt = "d_6QWE1pZUPPPmg81_Pfmw"
secret_base = "lOzoCmc4ArqjV5WxKotBC7Lw8lj9oA"
secret_alt = "IOzoCmc4ArqjV5WxKotBC7Lw8lj9oA"

combinations = [
    (id_base, secret_base, "small u + small l"),
    (id_base, secret_alt, "small u + capital I"),
    (id_alt, secret_base, "capital U + small l"),
    (id_alt, secret_alt, "capital U + capital I"),
]

print("Starting Reddit API Key Test...")

for cid, sec, desc in combinations:
    print(f"Testing: {desc}")
    result = test_reddit(cid, sec)
    if result is True:
        print(f"!!! SUCCESS !!!: {desc}")
        with open("correct_keys.txt", "w") as f:
            f.write(f"ID={cid}\nSECRET={sec}")
        break
    else:
        print(f"X Failed: {result}")