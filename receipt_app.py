import streamlit as st

import google.generativeai as genai
import pandas as pd
import json

import requests
from io import BytesIO
from PIL import Image

from datetime import datetime
import pytz


st.title("🧾 Receipt NARA")
st.caption("🚀 A Recipt collect service powered by Google Gemini")

def img_json(s:pd.Series) -> (Image, str):
  d = {k:"" if pd.isna(v) else v for k,v in s.to_dict().items()}
  f = d['file_name']
  del d['file_name']
  return Image.open(f), "JSON:\n"+json.dumps(d, ensure_ascii=False, indent=4)

def set_submit_trigger():
  st.session_state.submit_trigger = True

def submit(result:dict, img:Image):
  df = pd.DataFrame([result])
  submit_datetime = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
  today = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%Y%m%d")
  df.loc[0, 'submit_datetime'] = submit_datetime
  try:
    receipt_df = pd.read_csv('./data/receipt.csv', index_col=0)
    file_name = f"{today}_{len(receipt_df):04d}.jpg"
    df.loc[0, 'file_name'] = file_name
    final_df = pd.concat([receipt_df, df]).reset_index(drop=True)
  except:
    file_name = f"{today}_{0:04d}.jpg"
    df.loc[0, 'file_name'] = file_name
    final_df = df
  img.save(f"./data/imgs/{file_name}")
  final_df.to_csv('./data/receipt.csv')
  st.session_state['finished']=df.set_index('file_name', drop=True).T

if 'img' not in st.session_state:
  with st.container():
    img = None

    with st.expander('Take a picture'):
      img_file_buffer = st.camera_input("Take a picture")
      if img_file_buffer is not None:
        img = Image.open(img_file_buffer)

    with st.expander('Upload file', True):
      uploaded_file = st.file_uploader("Choose a file", type=['jpg', 'png'])
      if uploaded_file is not None:
        img = Image.open(uploaded_file)

      img_url = st.text_input("URL")
      if img_url:
        response = requests.get(img_url)
        img = Image.open(BytesIO(response.content))

  if img:
    st.session_state['img'] = img

    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)

    generation_config = {
      "temperature": 0.2,
      "max_output_tokens": 4096,
      "top_k": 40,
      "top_p": 0.95,
    }

    model = genai.GenerativeModel(
      model_name='gemini-pro-vision',
      generation_config=generation_config,
      safety_settings={
        'harassment':'block_none',
        'hate':'block_none',
        'sex':'block_none',
        'danger':'block_none'
      }
    )

    parts = ["""Transform the following recipt (or slip) in a JSON format in Korean(한국어).
Keys are ['receipt_datatime', 'business_name(상호명,가맹점명)', 'business_no(사업자번호)', 'address', 'tel', 'fax', 'e-mail', 'item_summary', 'currency unit', 'total'].
Do NOT translate the keys and addresses.
'business_no' is place near the 'business_name' and it is of the form "xxx-xx-xxxxx".
Categories are ['식사', '음료', '식료품', '주류', '사무용품', '의약품', ...].
If there is no receipt in the picture, make all the values empty strings.
"""]

    example_df = pd.read_csv('./example/receipt.csv', index_col=0)
    for i, s in example_df.iterrows():
      parts += img_json(s)

    prompt = [img, "JSON:\n"]
    with st.spinner('Processing receipt...'):
      response = model.generate_content(parts + prompt)
      st.session_state['content'] = json.loads(response.text)
    st.success('Done!')
    st.rerun()
else:
  if not 'finished' in st.session_state:
    with st.expander("Recipt", False):
      st.image(st.session_state.img)
    
    with st.expander("Submit", True):
      with st.form('res'):
        result = {
          k: st.text_input(k, value=v)
          for k, v in st.session_state.content.items()
        }
        st.form_submit_button(on_click=set_submit_trigger)
      if 'submit_trigger' in st.session_state:
        submit(result, st.session_state.img)
  else:
    with st.expander("Recipt", False):
      st.image(st.session_state.img)
    st.write(st.session_state.finished)