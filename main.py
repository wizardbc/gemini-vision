import streamlit as st

import requests
from io import BytesIO
from PIL import Image
import google.generativeai as genai

def _generate():
  # Generate
  model = genai.GenerativeModel(model_name=model_name,
                                generation_config=generation_config,
                                safety_settings=safety_settings)
  response = model.generate_content(st.session_state.parts, stream=True)

  text = ''
  for chunk in response:
    try:
      text += chunk.text
      placeholder.write(text + "▌")
    except:
      text = "***Error occurred*** {chunk.prompt_feedback}"
  placeholder.write(text)
  st.session_state.response = text

def _add(is_picture=False):
  if is_picture:
    st.session_state.parts.append(None)
  else:
    st.session_state.parts.append('')

def _del(idx):
  st.session_state.parts = st.session_state.parts[:idx]
  st.session_state.response = ''

def _decline():
  st.session_state.response = ''

def _accept():
  if type(st.session_state.parts[-1]) == str:
    st.session_state.parts[-1] += st.session_state.response
  else:
    st.session_state.parts.append(st.session_state.response)
  _decline()


st.title("Take pictures 🖼")
st.caption("🚀 A streamlit chatbot powered by Google Gemini")

if "api_key" not in st.session_state:
  try:
    st.session_state.api_key = st.secrets["GOOGLE_API_KEY"]
  except:
    st.session_state.api_key = ""
    st.write("Your Google API Key is not provided in `.streamlit/secrets.toml`, but you can input one in the sidebar for temporary use.")

# Initialize content
if "parts" not in st.session_state:
  st.session_state.parts = []
  st.session_state.response = ''

# Sidebar for parameters
with st.sidebar:
  # Google API Key
  if not st.session_state.api_key:
    st.header("Google API Key")
    st.session_state.api_key = st.text_input("Google API Key", type="password")
  else:
    genai.configure(api_key=st.session_state.api_key)

  # ChatCompletion parameters
  st.header("Parameters")
  model_name = st.selectbox("model_name",
      ['gemini-pro', 'gemini-pro-vision'], index=1)
  generation_config = {
    "temperature": st.slider("temperature", min_value=0.0, max_value=1.0, value=0.2),
    "max_output_tokens": st.number_input("max_tokens", min_value=1, value=4096),
    "top_k": st.slider("top_k", min_value=1, value=40),
    "top_p": st.slider("top_p", min_value=0.0, max_value=1.0, value=0.95),
  }
  safety_settings={
    'harassment':'block_none',
    'hate':'block_none',
    'sex':'block_none',
    'danger':'block_none'
  }

parts = []
for i, part in enumerate(st.session_state.parts):
  if type(part) == str:
    text = st.text_area(f"Part {i}", value=part, label_visibility='hidden')
    parts.append(text)
    continue
  if part is None:
    img = None
    img_file_buffer = st.camera_input("Take a picture")
    if img_file_buffer is not None:
      img = Image.open(img_file_buffer)
    uploaded_file = st.file_uploader("Choose a file", type=['jpg', 'png'])
    if uploaded_file is not None:
      img = Image.open(uploaded_file)
    img_url = st.text_input("URL")
    if img_url:
      response = requests.get(img_url)
      img = Image.open(BytesIO(response.content))
    parts.append(img)
  else:
    st.image(part)
    parts.append(part)

st.session_state.parts = parts

columns = st.columns([1,1,1,1,1])
with columns[0]:
  st.button("Add Text", on_click=_add, kwargs={'is_picture': False}, use_container_width=True)
with columns[1]:
  st.button("Add Picture", on_click=_add, kwargs={'is_picture': True}, use_container_width=True, disabled=('-vision' not in model_name))
with columns[2]:
  st.button("Generate", on_click=_generate, use_container_width=True, disabled=(len(st.session_state.parts)==0))
with columns[3]:
  st.button("Delete", on_click=_del, args=[-1], use_container_width=True)
with columns[4]:
  st.button("Clear", on_click=_del, args=[0], use_container_width=True)

with st.chat_message('ai'):
  placeholder = st.empty()
  if st.session_state.response:
    placeholder.write(st.session_state.response)
    columns_ai = st.columns([1,1,1,1,1])
    with columns_ai[0]:
      st.button("Accept", on_click=_accept, use_container_width=True)
    with columns_ai[1]:
      st.button("Decline", on_click=_decline, use_container_width=True)
  else:
    placeholder.write("*(Press the Generate buton to generate text.)*")