#!/usr/bin/env python3.12
# scratch.py
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from random import randint

from ping3 import ping
import requests
from bs4 import BeautifulSoup
from rich.console import Console

num = lambda: randint(1, 5)
response_list = []
max_threads = 10
queues = [Queue() for _queue in range(max_threads)]
futures = []
url = "https://kamapuaa.it"
host = "kamapuaa.it"
c = Console()


def purl(target_host):
    return ping(target_host)


with ThreadPoolExecutor(max_workers=max_threads) as executor:
    for i, icmp_req in enumerate(range(max_threads)):
        c.print(f"Sending Request n {i}")
        future = executor.submit(purl, host)
        futures.append(future)
        c.print(f"Request n {i} sent.")
c.print(*[future.result() for future in futures])


# def assert_url(n):
#     try:
#         response = requests.get(url)
#     except requests.RequestException as e:
#         c.print(f"Request Error: {e}")
#     else:
#         c.print(f"Response {n}: {BeautifulSoup(response.content, features='html.parser').get_text()}")
#
#
# with ThreadPoolExecutor(max_workers=max_threads) as executor:
#     for n, request in enumerate(range(max_threads)):
#         future = executor.submit(assert_url, n)
#         c.print(f"Future {n} submitted. \r")
#         futures.append(future)



# def append_stuff(numb):
#     response_list.append(numb)
#     time.sleep(num())
#     print(f"[+] Item {numb} appended.")
#
#
# for i, queue in enumerate(queues):
#     thread_id = i % max_threads
#     number = num()
#     queues[thread_id].put(number)
#
# with ThreadPoolExecutor(max_workers=max_threads) as executor:
#     for queue in queues:
#         while not queue.empty():
#             numb = queue.get()
#             future = executor.submit(append_stuff, numb)
#             futures.append(future)
#     print(response_list)

# def append_stuff(numb: int) -> None:
#     response_list.append(numb)
#     time.sleep(1)
#
#
#
# for i, queue in enumerate(queues):
#     thread_id = i % max_threads
#     queues[thread_id].put(num())
#     print(queue.queue)
#
# with ThreadPoolExecutor(max_workers=max_threads) as executor:
#     for queue in queues:
#         while not queue.empty():
#             number = queue.get()
#             future = (append_stuff, number)
#             futures.append(future)

# import random
# import time
# from concurrent.futures import ThreadPoolExecutor
# from queue import Queue
#
# max_threads = 10
# queues = [Queue() for _queue in range(max_threads)]
# # print(queues)
# resp_list = []
# num = random.random()
#
#
# def append_stuff(numb):
#     resp_list.append(numb)
#     print(numb)
#     time.sleep(1)
#
#
# for i, queue in enumerate(queues):
#     thread_id = i % max_threads
#     queues[thread_id].put(num)
# # print(queues)
#
# with ThreadPoolExecutor(max_workers=max_threads) as executor:
#     for thread_id, queue in enumerate(queues):
#         while not queue.empty():
#             number = queue.get()
#             future = executor.submit(
#                 append_stuff,
#                 number
#             )
#             # future.result()
#
# # for thread in range(max_threads):
# #     append_stuff(num)
# #     time.sleep(0.5)
# #
# print(resp_list)
