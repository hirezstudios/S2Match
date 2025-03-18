#!/bin/bash

# Create necessary directories
mkdir -p streamlit_app/logs

# Install requirements if needed
pip install -r requirements.txt
pip install -r streamlit_app/requirements.txt

# Run the Streamlit app
streamlit run streamlit_app/Home.py 