import tweepy
from dotenv import load_dotenv
import os
import requests
from PIL import Image
from io import BytesIO
from fpdf import FPDF
import tempfile


load_dotenv()

consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
access_token = os.environ.get("ACCESS_TOKEN")
access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")


auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


def get_images_from_last_tweet_in_thread(thread_id):
    """Get images from the last tweet in a thread.

    Args:
        thread_id (str): tweet id of last tweet in thread. id is twitter.com/{user}/status/{id}

    Returns a List of BytesIO Image objects
    """
    images = []
    tweet = api.get_status(thread_id, tweet_mode='extended')

    while tweet.in_reply_to_status_id:
        media = tweet.extended_entities.get(
            'media', []) if 'extended_entities' in tweet._json else []
        if media:
            for m in media:
                if m['type'] == 'photo':
                    response = requests.get(m['media_url'])
                    print(m["media_url"])
                    img = Image.open(BytesIO(response.content))
                    images.append(img)
        tweet = api.get_status(
            tweet.in_reply_to_status_id, tweet_mode='extended')
    return images


def convert_images_to_pdf(images, output_filename):
    """takes a list of byteio image objects and converst to a pdf

    Args:
        images (list of BytesIO Image objects): a list of images to convert to pdf
        output_filename (str): filename of the output pdf
    """
    pdf = FPDF()

    # this is used to split every image in tweet into 2 
    # comment out for general use
    images = [
        cropped_img for img in images[::-1] for cropped_img in [
            img.crop((0, 0, img.size[0] / 2, img.size[1])),
            img.crop((img.size[0] / 2, 0, img.size[0], img.size[1]))
        ]
    ]

    for img in images:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            img.save(tmp_file, 'JPEG')
            tmp_file.flush()
            tmp_file.close()
            pdf.add_page()
            pdf.image(tmp_file.name, 0, 0, pdf.w, pdf.h)
            os.unlink(tmp_file.name)

    pdf.output(output_filename, 'F')


if __name__ == '__main__':
    thread_id = input("Enter the link to the last reply of the thread: ").split(
        "/")[-1].split("?")[0]
    output_filename = input("Enter the output PDF filename: ")

    images = get_images_from_last_tweet_in_thread(thread_id)
    if images:
        convert_images_to_pdf(images, output_filename)
        print(f"Successfully converted images to {output_filename}")
    else:
        print("No images found in the thread.")
