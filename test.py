import os

import gradio as gr
from openai import OpenAI
import numpy as np
import cv2

# def reverse_text(text):
#     return text[::-1]

def image_to_sketch(image):
    gray_image = image.convert("L")
    inverted_image = 255 - np.array(gray_image)
    blurred = cv2.GaussianBlur(inverted_image, (21, 21), 0)
    inverted_blurred = 255 - blurred
    pencil_sketch = cv2.divide(np.array(gray_image), inverted_blurred, scale=256.0)
    return pencil_sketch

demo = gr.Interface(
    fn = image_to_sketch,
    inputs = [gr.Image(label="上传图片",type="pil")],
    outputs = [gr.Image(label="素描图")],
    title="图像转铅笔画",
    description="上传一张图片，将转换为铅笔画效果"
)

demo.launch()
