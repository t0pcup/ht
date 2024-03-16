import io
import json
import os

# import cv2 as cv
import pandas as pd
import urllib3
from loguru import logger
from minio import Minio
from PIL import Image
from urllib3.util.retry import Retry

from config import config


class MinioLoader:
    """
    Работает на основе библиотеки minio
    https://github.com/minio/minio-py/
    """

    def __init__(self):
        """
        minio_bucket: minio buckets name from server
        """

        if config.WORK_LOCALLY:
            # Create a custom HTTP client with a timeout
            retry = Retry(total=0, backoff_factor=0, status_forcelist=None)
            custom_http_client = urllib3.PoolManager(timeout=0, retries=retry)
        else:
            retry = Retry()
            custom_http_client = urllib3.PoolManager(retries=retry)

        self.client = Minio(
            endpoint=f"{config.MINIO_HOST}:{config.MINIO_PORT}",
            access_key=config.MINIO_USERNAME,
            secret_key=config.MINIO_PASSWORD,
            http_client=custom_http_client,
            secure=False,
        )

        self.minio_bucket = config.MINIO_BUCKET
        self.minio_models_folder = config.MINIO_MODELS_FOLDER
        self.client.list_buckets()
        logger.info("Minio storage connected")
        # reach storage
        try:
            self.client.list_buckets()
            logger.info("Minio storage connected")
        except Exception as err:
            # raise error if storage not reachable
            logger.info(f"Minio storage not reachable: {err}")

    def upload_bytes_file(self, path, data, len_data, bucket_name=None):
        """
        The upload_bytes_file function uploads a file to the Minio server.
            Args:
                path (str): The path of the file on the Minio server.
                data (bytes): The bytes of data that will be uploaded to the Minio server.
                len_data (int): The length of data in bytes that will be uploaded to
                                the Minio server.

        :param path: Specify the location where the file should be stored
        :param data: Pass the data to be uploaded
        :param len_data: Specify the length of data
        :return: True
        """

        if bucket_name is None:
            bucket_name = self.minio_bucket

        path = path.replace("//", "/").replace("\\", "/")

        if isinstance(data, io.BytesIO):
            self.client.put_object(bucket_name, str(path), data, len_data)
        else:
            self.client.put_object(bucket_name, str(path), io.BytesIO(data), len_data)
        return True

    def download_models(self, local_models_folder="models"):
        """
        Download models recursively
        return: None
        """

        minio_file_list = self.client.list_objects(
            bucket_name=self.minio_bucket,
            prefix=self.minio_models_folder,
            recursive=True,
        )

        for minio_file in minio_file_list:
            minio_file_path = minio_file.object_name
            minio_file_path = minio_file_path.replace("\\", "/")
            list_minio_file_path = minio_file_path.split("/")
            local_dir_path = (
                local_models_folder + "/" + "/".join(list_minio_file_path[1:-1])
            )
            local_file_path = local_dir_path + "/" + list_minio_file_path[-1]

            if not os.path.exists(local_file_path):
                logger.info(f"Download file: {minio_file_path} to {local_file_path}")
                data = self.client.get_object(self.minio_bucket, minio_file_path)

                if not os.path.exists(local_dir_path):
                    os.makedirs(local_dir_path, exist_ok=True)

                with open(local_file_path, "wb") as file_data:
                    for data_bytes in data.stream(32 * 1024):
                        file_data.write(data_bytes)

        return True

    def create_bucket(self, bucket_name):
        """
        The create_bucket function creates a new bucket in the S3 service.

        :param bucket_name: Specify the name of the bucket that you want to create
        :return: True
        """
        found = self.client.bucket_exists(bucket_name)
        if not found:
            self.client.make_bucket(bucket_name)
            print("Created bucket", bucket_name)
        else:
            print("Bucket", bucket_name, "already exists")
        return True


def save_xlsx_to_minio(df_to_excel, save_filepath, bucket_name=None):
    """
    The save_xlsx_to_minio function saves a dictionary of DataFrames
    to an Excel file in Minio.

    :param df_to_excel: dataframe
    :param save_filepath: Specify the filepath in minio where
    the file will be saved
    :return: True
    """
    minio_loader = MinioLoader()
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_to_excel.to_excel(writer, "0", header=False, index=False)
    buffer.seek(0)
    minio_loader.upload_bytes_file(
        save_filepath, buffer, buffer.getbuffer().nbytes, bucket_name
    )

    return True


def save_json_to_minio(input_dict, save_filepath, bucket_name=None):
    """
    The save_json_to_minio function takes a dictionary
    and saves them to Minio as JSON.

    :param df_dict: Pass in a dictionary
    :param save_filepath: Specify the filepath to save the dataframe to
    :return: True
    """
    minio_loader = MinioLoader()

    json_binary = json.dumps(
        input_dict, ensure_ascii=False, indent=4, cls=JSONEncoder
    ).encode("UTF-8")
    minio_loader.upload_bytes_file(
        save_filepath, json_binary, len(json_binary), bucket_name
    )

    return True


# def save_file_to_minio(input_dict, save_filepath, bucket_name=None):
#     minio_loader = MinioLoader()

#     file_binary = json.dumps(
#         input_dict, ensure_ascii=False, indent=4, cls=JSONEncoder
#     ).encode("UTF-8")
#     minio_loader.upload_bytes_file(
#         save_filepath, file_binary, len(json_binary), bucket_name
#     )

#     return True


def save_txt_to_minio(text_string, save_filepath, bucket_name=None):
    """
    The save_txt_to_minio function takes a text string and saves it to the Minio server.

    :param text_string: Store the text that is to be uploaded
    :param save_filepath: Define the filepath where the text_string will be saved
    :return: True
    """
    minio_loader = MinioLoader()
    text_string = text_string.encode("UTF-8")
    minio_loader.upload_bytes_file(
        save_filepath, text_string, len(text_string), bucket_name
    )
    return True


def save_upload_file_to_minio(upload_file, save_filepath, bucket_name=None):
    """
    The save_txt_to_minio function takes a text string and saves it to the Minio server.

    :param text_string: Store the text that is to be uploaded
    :param save_filepath: Define the filepath where the text_string will be saved
    :return: True
    """
    minio_loader = MinioLoader()
    upload_file = upload_file.file.read()
    minio_loader.upload_bytes_file(
        save_filepath, upload_file, len(upload_file), bucket_name
    )
    return True


def save_docx_to_minio(document, save_filepath, bucket_name=None):
    """
    The save_docx_to_minio function saves a python-docx file to the Minio server.

    :param document: Document object that is created by python-docx
    :param save_filepath: Specify the name of the file that will be saved to minio
    :param bucket_name: Specify the bucket in which to save the file
    :return: True
    """
    minio_loader = MinioLoader()
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    minio_loader.upload_bytes_file(
        save_filepath, buffer, buffer.getbuffer().nbytes, bucket_name
    )

    return True


def save_file_from_disk_to_minio(file_path, save_filepath, bucket_name=None):
    """
    Load file from disk to minio
    """
    minio_loader = MinioLoader()

    minio_loader.client.fput_object(bucket_name, save_filepath, file_path)
    return True


def load_image_from_minio(filepath, bucket_name=None):
    """
    Load single image (png, jpg, jpeg) from minio
    """
    minio_loader = MinioLoader()
    image_data = minio_loader.client.get_object(bucket_name, filepath)

    image_bytes = io.BytesIO(image_data.read())
    image = Image.open(image_bytes)

    return image


def load_file_from_minio(filepath, bucket_name=None):
    minio_loader = MinioLoader()
    data = minio_loader.client.get_object(bucket_name, filepath)

    bytes = io.BytesIO(data.read())
    image = Image.open(bytes)

    return image


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "to_dict"):
            return o.to_dict(orient="index")
        return json.JSONEncoder.default(self, o)
