# Write a python code to call the /download/{company_id} from test_server.py 
# Use aiohttp to make the request and print the response status code and content.
import aiohttp
import asyncio
from src.logging.logging import configure_logging, get_logger
configure_logging(level="INFO", service_name="test-client")
logger = get_logger("test_client")
async def fetch_company_data(company_id):
    url = f"http://localhost:8002/file/download/{company_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status in [200, 201]:
                logger.info(f"✓ Download successful for company_id {company_id}")
                return True
            else:
                error_text = await response.text()
                logger.error(f"✗ Download failed for company_id {company_id} with status {response.status}: {error_text}")
                return None

async def parse(admin_id=None, path=None):  # Add the required admin_id
   
    url= f"http://localhost:8000/parser?path={path}&admin_id={admin_id}"
    async with aiohttp.ClientSession() as session:
        async with session.post(
                    url
                ) as response:
            if response.status in [200, 201]:
                logger.info(f"✓ Parsing successful")
                return True
            else:
                error_text = await response.text()
                logger.error(f"✗ Parsing failed with status {response.status}: {error_text}")
                return False

async def chunk(namespace="dotlines", admin_id=None):
    url= f"http://localhost:8000/chunk?namespace={namespace}&admin_id={admin_id}"
    async with aiohttp.ClientSession() as session:
        async with session.post(
                    url
                ) as response:
            if response.status in [200, 201]:
                logger.info(f"✓ Chunking successful")
                return True
            else:
                error_text = await response.text()
                logger.error(f"✗ Chunking failed with status {response.status}: {error_text}")
                return False
            
            
async def vectorizing(namespace="dotlines", admin_id=None):
    url= f"http://localhost:8000/vectorizing?namespace={namespace}&admin_id={admin_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(
                    url
                ) as response:
            if response.status in [200, 201]:
                logger.info(f"✓ vectorizing successful")
                return True
            else:
                error_text = await response.text()
                logger.error(f"✗ vectorizing failed with status {response.status}: {error_text}")
                return False
            
async def store(admin_id=None):
    url= f"http://localhost:8000/store?admin_id={admin_id}"
    async with aiohttp.ClientSession() as session:
        async with session.post(
                    url
                ) as response:
            if response.status in [200, 201]:
                result = await response.json()
                logger.info(f"✓ Storing successful")
                return True
            else:
                error_text = await response.text()
                logger.error(f"✗ Storing failed with status {response.status}: {error_text}")
                return False


# Example usage
company_id = "4347461f-b706-44be-a3a8-b97db4f86944"  # Replace with the actual company ID
namespace = "dotlines"
asyncio.run(fetch_company_data(company_id))
asyncio.run(parse(admin_id="some_admin_id", path="download_dir"))
asyncio.run(chunk(namespace=namespace, admin_id="some_admin_id"))
asyncio.run(vectorizing(namespace=namespace, admin_id="some_admin_id"))
asyncio.run(store(admin_id="some_admin_id"))