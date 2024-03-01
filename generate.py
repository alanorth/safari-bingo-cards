#!/usr/bin/env python3
#
# SPDX-License-Identifier: GPL-3.0-only

import argparse
import logging
import os.path
from random import sample

import pandas as pd
import pyvips
import requests
from colorama import Fore

# Create a local logger instance
logger = logging.getLogger(__name__)


def create_thumbnail(animal):
    image_filename = f"{animal['id']}.jpg"
    image_path = f"images/{image_filename}"

    thumbnail_filename = os.path.splitext(image_filename)[0] + "_thumb.vips"
    thumbnail_path = f"images/{thumbnail_filename}"
    # check if the file has been downloaded
    if not os.path.isfile(image_path):
        logger.error(
            Fore.RED + f"> Missing image for {animal['common_name']}." + Fore.RESET
        )
    # check if we already have a thumbnail
    elif os.path.isfile(thumbnail_path):
        if args.debug:
            logger.debug(
                Fore.YELLOW
                + f"> Thumbnail for {animal['common_name']} already exists."
                + Fore.RESET
            )
    else:
        vips_image = pyvips.Image.new_from_file(image_path)
        # Crop to a 600x600 square using smartcrop to focus attention
        # See: https://stackoverflow.com/questions/47852390/making-a-huge-image-mosaic-with-pyvips
        vips_thumbnail = vips_image.thumbnail_image(
            600, height=600, linear=True, crop=animal["vips_smartcrop"]
        )
        # Create a temporary image with text using Pango markup, which can use
        # some HTML. This allows us to use consistent font sizes (as opposed to
        # pyvips.Image.text's width and height parameters, which are maximums
        # in pixels). Note that we need to use RGBA here or else the text image
        # shows up as a white block when we overlay it on the thumbnail.
        #
        # See: https://docs.gtk.org/Pango/pango_markup.html
        text = pyvips.Image.text(
            f'<span foreground="white" background="#702D3E" size="48pt">{animal["common_name"]}</span>',
            rgba=True,
        )
        vips_thumbnail = vips_thumbnail.composite(
            text, "over", x=0, y=600 - text.height
        )
        # Write to VIPS format for intermediate thumbnails so we don't do JPEG
        # conversion twice.
        vips_thumbnail.vipssave(thumbnail_path, strip=True)

        logger.info(
            Fore.GREEN
            + f"> Created thumbnail for {animal['common_name']}..."
            + Fore.RESET
        )


    return


def download_image(animal):
    image_url = animal["image"]
    image_filename = f"{animal['id']}.jpg"
    image_path = f"images/{image_filename}"

    if os.path.isfile(image_path):
        if args.debug:
            logger.debug(
                Fore.YELLOW
                + f"> {animal['common_name']} already downloaded."
                + Fore.RESET
            )
    else:
        headers = {
            "User-Agent": "safari-bingo-cards-bot/0.1 (https://git.mjanja.ch/alanorth/safari-bingo-cards)"
        }
        response = requests.get(image_url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(image_path, "wb") as fd:
                for chunk in response:
                    fd.write(chunk)

            logger.info(
                Fore.GREEN + f"> Downloaded {animal['common_name']}..." + Fore.RESET
            )
        else:
            logger.error(
                Fore.RED
                + f"> Download failed (HTTP {response.status_code}), I will try again next time."
                + Fore.RESET
            )

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download images and generate thumbnails from files in a CSV."
    )
    parser.add_argument(
        "-a",
        "--across",
        help="Number of images across grid.",
        type=int,
        default=4,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Print debug messages to standard error (stderr).",
        action="store_true",
    )
    parser.add_argument(
        "-i",
        "--csv-file",
        help="Path to input file (CSV).",
        required=True,
        type=argparse.FileType("r", encoding="UTF-8"),
    )
    parser.add_argument(
        "-o",
        "--output-file",
        help="Path to output file (JPEG).",
        required=True,
    )
    args = parser.parse_args()

    # The default log level is WARNING, but we want to set it to DEBUG or INFO
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Set the global log format
    logging.basicConfig(format="[%(levelname)s] %(message)s")

    # Open the CSV
    animals_df = pd.read_csv(args.csv_file)

    # Get a random list of animal IDs. We will build a square grid using the
    # "across" parameter passed by the user.
    animal_ids = animals_df["id"].sample(args.across * args.across)
    logger.info(f"Generated random sample of {animals_df.shape[0]} animals...")

    # Slice those random animals from the dataframe
    animals_df_random = animals_df[animals_df["id"].isin(animal_ids)]

    # Apparently iterating over dataframes is bad practice so I will use apply
    # over the dataframe's columns (axis=1) instead. In pandas, apply should
    # be a bit faster than iterrows.
    animals_df_random.apply(download_image, axis=1)
    animals_df_random.apply(create_thumbnail, axis=1)

    thumbnails = []
    for animal_id in animal_ids:
        thumbnails.append(pyvips.Image.new_from_file(f"images/{animal_id}_thumb.vips"))

    # Join all thumbnails together in an array of x across with a padding of 2
    # pixels between each square.
    joined = pyvips.Image.arrayjoin(thumbnails, across=args.across, shim=2)
    logger.info(f"Generated card with a {args.across}x{args.across} grid of animals...")

    joined.jpegsave(args.output_file, optimize_coding=True, strip=True)
    logger.info(f"Wrote {args.output_file}")
