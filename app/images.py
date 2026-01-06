import os

from dotenv import load_dotenv
from imagekitio import ImageKit

load_dotenv()

imagekit = ImageKit(
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
)

imagekit_url_endpoint = os.environ.get("IMAGEKIT_URL")
