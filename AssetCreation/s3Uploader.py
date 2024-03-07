import logging
import boto3
from botocore.exceptions import ClientError
import os
from keys import s3AccessKey
from keys import s3SecretKey

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        #object_name = os.path.basename(file_name)
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3', aws_access_key_id=s3AccessKey, aws_secret_access_key=s3SecretKey)
    try:
        response = s3_client.upload_file(file_name, 
                                         bucket, 
                                         object_name,
                                         ExtraArgs={'ContentType': 'image/png'})
    except ClientError as e:
        logging.error(e)
        return False
    except Exception as e:
        logging.error(e)
        return False
    return True