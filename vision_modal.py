import io
import os
import json
from enum import Enum
from typing import List, Dict, Optional
from datetime import date
import instructor
import time
from openai import OpenAI
from pdf2image import convert_from_bytes
import requests
import gc
import torch
from PIL import Image
import sys
from transformers import AutoTokenizer, AutoModel
#from lmdeploy import pipeline, TurbomindEngineConfig
from PIL import Image
import torchvision.transforms as T
from torchvision.transforms.functional import InterpolationMode

path='OpenGVLab/InternVL2_5-4B-MPO'
def ai_analysis(image_pixels,prompt):
    try:
       with torch.no_grad():
                response, history = model.chat(tokenizer, image_pixels, prompt, generation_config,
                               history=None, return_history=True)
       if response:
           try:
               response=json.loads(response.replace('```','').replace('json',''))
               response['extraction_confidence']=calculate_extraction_confidence(response)
           except:
               pass
       return response
    except Exception as ex:
        print(str(ex))
        return None

generation_config = dict(max_new_tokens=1024, do_sample=True)

path="OpenGVLab/InternVL2_5-4B-MPO"
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
# Load the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
model = AutoModel.from_pretrained(
    path,
    torch_dtype=torch.bfloat16,  # Or use torch.float16
    load_in_8bit=True,

    use_flash_attn=True,
    trust_remote_code=True
).eval()
def build_transform(input_size):
    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose([
        T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=MEAN, std=STD)
    ])
    return transform
def load_image(image_file, input_size=448, max_num=12):
    image = Image.open(image_file).convert('RGB')
    transform = build_transform(input_size=input_size)
    images = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
    pixel_values = [transform(image) for image in images]
    pixel_values = torch.stack(pixel_values)
    return pixel_values
def dynamic_preprocess(image, min_num=1, max_num=12, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images


def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff = float('inf')
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio


def calculate_extraction_confidence(response_dict):
    """Calculate the extraction confidence after parsing."""
    print(f'response_dict: {response_dict}')

    # Identifying all confidence keys and summing their values
    confidence_values = [v for k, v in response_dict.items() if k.endswith("_confidence")]
    total_confidences = sum(confidence_values)
    num_confidences = len(confidence_values)

    # Avoid division by zero if no confidence values are present
    extraction_confidence = total_confidences / num_confidences if num_confidences > 0 else 0.0
    return round(extraction_confidence,2)


def extract_text_from_pdf(pdf_path, start_page=1, prompt=None):
    pixel_values = None
    try:
        ocr_time = 0
        model_processing_time = 0
        ocr_start_time = time.time()
        responses = []  # Initialize an empty list to store responses

        # Convert PDF to images
        try:
            temp_images = convert_from_bytes(pdf_path.getvalue())
            if len(temp_images) != 1:
                images = temp_images[start_page - 1:]
            else:
                images = temp_images
        except:
            image_file = Image.open(pdf_path)
            images = [image_file]

        final_page_text = ""
        pixels_array = []

        # Process each page
        for idx, image in enumerate(images):
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            img_pixel_values = load_image(io.BytesIO(img_byte_arr)).to(torch.bfloat16).cuda()
            pixels_array.append(img_pixel_values)
            if idx == 2:
                break

        pixel_values = torch.cat(pixels_array, dim=0)
        model_processing_start_time = time.time()

        system_prompt = f"""
            You are an expert at extracting structured data and information from documents including invoices, receipts, forms, tables, and other business documents.
            You will be provided images of documents that may contain text, forms, tables, or structured data.

            DO NOT make up any information that is not in the given images.
            If you cannot find the data, respond with null or "unknown" as applicable.

            Extract ALL data from the document with high precision and accuracy:

            For documents with tables or item lists (invoices, receipts, purchase orders):
            - Extract each row as a complete object
            - Preserve all numeric values (prices, quantities, amounts, rates, percentages)
            - Include all columns/fields exactly as shown
            - Return as a JSON array of objects

            For form documents:
            - Extract all filled fields and their corresponding values
            - Preserve field names and values exactly
            - Return as a single JSON object

            For text documents:
            - Extract key information and structure logically
            - Identify and preserve numeric data
            - Maintain field names and values

            Pay special attention to:
            - Numeric values (prices, quantities, totals, percentages, tax amounts)
            - Names and identifiers (e.g., patient names, provider names, product names)
            - Dates and amounts (e.g., MM-DD-YYYY format for dates)
            - Table headers and row data
            - Currency symbols and units (extract numeric values only)

            Important guidelines:
            - All numeric values must be numbers (not strings with text)
            - Preserve original field names exactly as they appear
            - Do not trim or modify extracted text
            - Include decimal places for prices and percentages
            - Handle currency symbols by extracting just the numeric value
            - Ensure all extracted data is accurate and complete

            Return valid JSON format that matches the document structure.
            If the document contains a table or list of items, return a JSON array.
            If it's a form or single record, return a JSON object.

            Example JSON formats:

            For a table or list of items:
            [
                {
                    "name": "product name",
                    "price": numeric value,
                    "quantity": numeric value,
                    "vat": numeric value,
                    "vatRate": numeric value
                },
                ...
            ]

            For form data:
            {
                "field_name": "value",
                "field_name2": "value2",
                ...
            }

            For text documents:
            {
                "key_information": "value",
                "additional_details": "value",
                ...
            }

            Ensure the JSON output is well-structured, accurate, and complete.
        """

        if prompt is not None:
            system_prompt = prompt

        resp = ai_analysis(pixel_values, system_prompt)
        model_processing_end_time = time.time()
        model_processing_time += model_processing_end_time - model_processing_start_time

        if resp:
            return {
                "file_name": pdf_path,
                "responses": "",
                "highest_confidence_response": resp,
                "execution_time": ocr_time + model_processing_time,
                "final_page_text": final_page_text,
                "status": "success"
            }, ocr_time, model_processing_time
        else:
            return {
                "file_name": pdf_path,
                "responses": [],
                "highest_confidence_response": None,
                "execution_time": 0,
                "final_page_text": "",
                "status": "no_response"
            }, None, model_processing_time

    except Exception as e:
        return {
            "file_name": pdf_path,
            "responses": [],
            "highest_confidence_response": None,
            "execution_time": 0,
            "final_page_text": "",
            "status": str(e)
        }, None, model_processing_time

    finally:
        del pixel_values
        torch.cuda.empty_cache()
        gc.collect()


def summarize_the_pdf(pdf_path, start_page=1):
    pixel_values=None
    try:
        ocr_time=0
        model_processing_time=0
        ocr_start_time = time.time()
        #print(f"start_time:{start_time}")
        responses = []  # Initialize an empty list to store responses
        # Convert PDF to images
        try:
            temp_images = convert_from_bytes(pdf_path.getvalue())
            images = temp_images[start_page - 1:] if len(temp_images) > 1 else temp_images
        except:
            image_file=Image.open(pdf_path)
            images=[image_file]


        final_page_text = ""
        pixels_array=[]
        # Process each page

        for idx, image in enumerate(images):
            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            img_pixel_values = load_image(io.BytesIO(img_byte_arr)).to(torch.bfloat16).cuda()
            pixels_array.append(img_pixel_values)
            if idx==2:
                break
        pixel_values=torch.cat(pixels_array,dim=0)
        model_processing_start_time=time.time()
        system_prompt = f"""
            summarize the given images
            """

        resp = doc_analysis(pixel_values,system_prompt)
        return resp
    except Exception as ex:
        return str(ex)
    finally:
       del pixel_values
       torch.cuda.empty_cache()
       gc.collect()


def doc_analysis(image_pixels,prompt):
    try:
       with torch.no_grad():
                response, history = model.chat(tokenizer, image_pixels, prompt, generation_config,
                               history=None, return_history=True)
       return response
    except Exception as ex:
        print(str(ex))
        return None


