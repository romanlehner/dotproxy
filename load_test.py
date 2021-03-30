import logging
import threading
import pytest
import e2e_client_test

logging.basicConfig(level=logging.INFO)

CONCURRENT_QUERIES = 200 # on my machine the test gets stuck for more than about 280 threads

# Todo: Try thread pools with concurrent.features ThreadPoolExecutor
def test_rapid_fire():
    
    logging.info(f'Generating {CONCURRENT_QUERIES} queries...')
    queries = []
    for num in range(CONCURRENT_QUERIES):
        thread = threading.Thread(target=e2e_client_test.test_when_google_dns_is_queried_then_the_response_should_contain_google, args=(num + 1,))
        thread.start()
        logging.info(f'Fired Query {thread}')
        queries.append(thread)

    logging.info(f'Concurrent Queries Active: {threading.active_count() - 1}')

    for thread in queries:
        thread.join()
        logging.info(f'Queries left: {threading.active_count() - 1}')

    logging.info(f'Processed {len(queries)} queries... Done!')
    
