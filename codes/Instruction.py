import streamlit as st
from collections import defaultdict
import json
from urllib import parse
import os
import time 
import nltk 
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from copy import deepcopy

import difflib 

import openai
# openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = st.secrets["OPENAI_API_KEY"]

def start_instruction():

    """
    Input: participant, role, writing task, writing content (prompt)
    -> Generate GPT-4 original text, and participants will revise the text
    -> Store them as a json (original, revision, change)
    """

    if 'gpt4_done' not in st.session_state:
        st.session_state.gpt4_done = False

    ### Instruction on the top page
    st.markdown("Thank you for participating in our research. Please read the instruction carefully, and follow them accordingly. Please contact at Minhwa Lee (lee03533@umn.edu) if you face any problem or seek help.")
    instruction_text = """ 
    <h2> Welcome! </h2>
    <br>
    The objective of this study is to examine the writing behaviors and strategy for different groups of people on several topics. 
    Here are the detailed instructions:
    <ol>
        <li> Go to <b>Revise GPT-4 Texts</b>, where you will revise a GPT-4 generated writing template. Please follow the instruction there. 
        <li> Navigate to the page <b> Review Your Edits </b> on the left sidebar. You will see a visualization of edits with the original text. 
        <li> Then, go to <b> Annotate Your Edits </b> to annotate your edits. Please read and follow the instruction carefully.
    </ol>
    <br>
    <p> <span style="color:red"> WARNING : </span> Please follow each of steps in the instructions responsibly. Your response will be manually reviewed for the approval. 
    <br><br>
    <h5> If you are ready, please first navigate to the page 'Revise GPT-4 Texts.'</h5>
    """
    st.markdown(instruction_text, unsafe_allow_html=True)
        
def main():
    st.set_page_config(page_title="Make Your Revision on GPT-4 Generated Writing Template!", 
                       page_icon="📝")
    
    start_instruction()

if __name__ == '__main__':
    main() 