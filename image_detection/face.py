#!/usr/bin/env python

from googleapiclient import discovery
import httplib2
from oauth2client.client import GoogleCredentials
import argparse
import sys

import base64

from PIL import Image
from PIL import ImageDraw

import pprint

DISCOVERY_URL='https://{api}.googleapis.com/$discovery/rest?version={apiVersion}'


def get_vision_service():
    credentials = GoogleCredentials.get_application_default()
    try:
        vision_service =  discovery.build('vision', 'v1', credentials=credentials,
                           discoveryServiceUrl=DISCOVERY_URL)
    except:
        print "Unexpected error when trying to creating vision service!", sys.exc_info()[0]
    else:
        return vision_service

def detect_face(face_file, max_results=4):
    """Uses the Vision API to detect faces in the given file.

    Args:
        face_file: A file-like object containing an image with faces.

    Returns:
        An array of dicts with information about the faces in the picture.
    """
    image_content = face_file.read()
    batch_request = [{
        'image': {
            'content': base64.b64encode(image_content).decode('UTF-8')
            },
        'features': [{
            'type': 'FACE_DETECTION',
            'maxResults': max_results,
            }]
        }]
    
    print "trying to get vision service!"
    try: 
        service = get_vision_service()
    except:
        print "Unexpected error when trying to get vision service!", sys.exc_info()[0]


    try:
        request = service.images().annotate(body={
            'requests': batch_request,
            })
    except:
        print "Unexpected error when trying to send image to service!", sys.exc_info()[0]

    response = request.execute()
    pprint(response)
    return response['responses'][0]['faceAnnotations']


def highlight_faces(image, faces, output_filename):
    """Draws a polygon around the faces, then saves to output_filename.

    Args:
      image: a file containing the image with the faces.
      faces: a list of faces found in the file. This should be in the format
          returned by the Vision API.
      output_filename: the name of the image file to be created, where the faces
          have polygons drawn around them.
    """
    im = Image.open(image)
    draw = ImageDraw.Draw(im)

    for face in faces:
        box = [(v.get('x', 0.0), v.get('y', 0.0)) for v in face['fdBoundingPoly']['vertices']]
        draw.line(box + [box[0]], width=5, fill='#00ff00')

    del draw
    im.save(output_filename)


def main(input_filename, output_filename, max_results):
    print "Starting..."
    with open(input_filename, 'rb') as image:
        print "Processing file: ", input_filename
        faces = detect_face(image, max_results)
        print('Found %s face%s' % (len(faces), '' if len(faces) == 1 else 's'))

        print('Writing to file %s' % output_filename)
        # Reset the file pointer, so we can read the file again
        image.seek(0)
        highlight_faces(image, faces, output_filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Detects faces in the images')
    parser.add_argument(
        'input_filename',
        help='the image you want to detect face in.')
    parser.add_argument(
        'output_filename',
        help='the image you want to output image.')
    parser.add_argument(
        'max_results',
        help='the max results limitation.')
    args = parser.parse_args()

    main(args.input_filename, args.output_filename, args.max_results)
