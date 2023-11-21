import streamlit as st

from collections import defaultdict
import json
import os
import time 
import nltk 
nltk.download('punkt')
from nltk.tokenize import word_tokenize, regexp_tokenize
from copy import deepcopy

import difflib 

import openai
# openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = st.secrets["OPENAI_API_KEY"]

class GenerateTemplate():
    def __init__(self) -> None:

        """
        Input: participant, role, writing task, writing content (prompt)
        -> Generate GPT-4 original text, and participants will revise the text
        -> Store them as a json (original, revision, change)
        """

        self.revision_done = False
        self.writing_content = ""
        self.writing_task = ""
        self.original = ""
        self.revision = ""

        if 'gpt4_done' not in st.session_state:
            st.session_state.gpt4_done = False

        ### Instruction on the top page
        st.markdown("Thank you for participating in our research. Please read the instruction carefully, and follow them accordingly. Please contact at Minhwa Lee (lee03533@umn.edu) if you face any problem or seek help.")
        instruction_text = """ 
        <h2> Instruction </h2>
        <br>
        <p> In this page, you will provide inputs to GPT-4 that will then generate a proxy writing template. Please follow each of the steps carefully. </p>
        <ol>
            <li> Fill out the four blank forms in the section 'Generate Writing Template'.
            <li> After filling out all blanks, click 'Generate by GPT-4'. 
            <li> You will be given a passage that is generated by GPT-4 based on your input. Please revise the text as you would normally do. 
            <li> After finishing your revision, click the 'Finish Revision' button in the bottom of this page. 
        </ol>
        <br>
        <p> <b style="color:red">Warning: </b> If you want to restart it, please <b>refresh</b> the page! </p>
        <hr>
        """
        st.markdown(instruction_text, unsafe_allow_html=True)

        ### Input from Participant's last name (identifier)
        st.markdown("<h2> Generate Writing Template </h2>", unsafe_allow_html=True)
        
        ### Running functions

        self._get_people_name()
        self._get_people_job()
        self._get_writing_task()
        self._get_writing_content()

        self._generate_gpt4_writing()
        self.show_revision()
        # self._store_revision_json()

    def _get_people_name(self):

        Lname = None
        if 'participant' in st.session_state:
            Lname = st.session_state.participant

        self.participant = st.text_input("What is your last name?", 
                                         value=Lname)
        
        if 'participant' not in st.session_state:
            st.session_state.participant = self.participant
        
        if st.session_state.participant != self.participant:
            st.session_state.participant = self.participant

    def _get_people_job(self):
        job_list = ['IT', 'Operation', 'Marketing/Sales', 'Customer Support', 'Human Resources (HR)', 
                    'Product & Brand Management', 'Research & Development', 'Legal', 'Student', 'Teacher/Faculty', 'Documentation/Communication']
        
        # Check if 'job' is in session_state and if its value is in job_list
        job_index = None
        if 'job' in st.session_state and st.session_state.job in job_list:
            job_index = job_list.index(st.session_state.job)

        self.job = st.selectbox('What best describes your function or work group?', 
                                job_list, 
                                index=job_index,
                                placeholder='Select Your Role..')

        # Add 'job' to session_state
        if 'job' not in st.session_state:
            st.session_state.job = self.job

        # Update 'job' 
        if st.session_state.job != self.job:
            st.session_state.job = self.job

    
    def _get_writing_task(self):
        task_list = ['Manual', 'Project Reports', 'Meeting Minutes', 'Emails', 'Project Proposal', 
                     'Newsletters', 'Press releases', 'Short Copy (e.g., ads, headlines)', 'Project Updates', 'Blog Posts', 'White Papers', 
                     'Social Media Posts', 'Product Descriptions', 'Technical documentation', 'Job Posting and description', 'Policy', 
                     'Academic Essay', 'Academic Report']
        
        task_index = None 
        if 'writing_task' in st.session_state and st.session_state.writing_task in task_list:
            task_index = task_list.index(st.session_state.writing_task)

        self.writing_task = st.selectbox('What kind of writing task would you like to work on? ',
                                        task_list, 
                                        index=task_index,
                                        placeholder='Select Your Task..')
        # Add to session_state
        if 'writing_task' not in st.session_state:
            st.session_state.writing_task = self.writing_task
        # Update 'job'
        if st.session_state.writing_task != self.writing_task:
            st.session_state.writing_task = self.writing_task
        
    
    def _get_writing_content(self):
        self.writing_content = st.text_area("What will be the content of the writing you selected above?", 
                                            value = st.session_state.writing_content if 'writing_content' in st.session_state else None,
                                            height=150, 
                                            max_chars=700, 
                                            placeholder="e.g., some announcements about developing AI writing assistants and related software details.")
        
        # Add to session_state
        if 'writing_content' not in st.session_state:
            st.session_state.writing_content = self.writing_content
        # Update
        if st.session_state.writing_content != self.writing_content:
            st.session_state.writing_content = self.writing_content
    
    def _generate_gpt4_writing(self):

        click_gpt4 = st.button("Generate Writing Example")

        if click_gpt4:
            if (st.session_state.job != None) and (st.session_state.writing_task != None) and (st.session_state.writing_content != None):
                with st.status("Generating Writing with GPT-4..", expanded=True) as openai_status:
                    st.write("Generating contents...")         
                    system_prompt = f"Your work group is {st.session_state.job}."
                    prompt = f"### Instruction: Write a passage of {st.session_state.writing_task} about the following situation: {st.session_state.writing_content}."
                    if st.session_state.job not in ['Student', 'Teacher/Faculty']:
                        prompt += " For tone and style, use plain language, write professional but less formal."
                    prompt_creation = openai.ChatCompletion.create(model="gpt-4", 
                                                       messages = [{"role": "system", "content":system_prompt},
                                                                   {"role":"user", "content":prompt}], 
                                                       temperature = 0.8)
                    gpt4_response = prompt_creation.choices[0]['message']['content']
                    time.sleep(2)
                    openai_status.update(label="Generation Completed!", state='complete', expanded=False)
                self.original = gpt4_response
                # Add to session_state
                if 'original' not in st.session_state:
                    st.session_state.original = self.original
                # Update gpt4_done status to True
                st.session_state.gpt4_done = True
            else:
                st.warning("Please fill out all of the inputs above and re-click the button.")

    def show_revision(self):
        def update_revision(text):
            st.session_state.revision = text
        
        # Add a boolean flag to signal finished revision later
        if 'finish_revision' not in st.session_state:
            st.session_state.finish_revision = False
        
        # Show a editor panel and revision by each step are stored
        if st.session_state.gpt4_done:
            st.markdown("<hr><h2> Revise the GPT-4 Generated Text </h2>", unsafe_allow_html=True)
            st.write("Given a short passage generated by GPT-4, please **revise it to better communicate within your team.**")
            st.markdown("<p> If you want to re-generate template, please refresh the page first. </p>", unsafe_allow_html=True)
            
            if 'revision' not in st.session_state:
                st.session_state.revision = st.session_state.original 

            # Initialize or update the revision state with the original text if it hasn't been modified
            # revision_default = st.session_state.get('revision', "")
            revision_current = st.text_area("Revise Text Here 👇", 
                                            value=st.session_state.revision,  # Set the value to the current state
                                            key = 'revised_text_area',
                                            height=1000, 
                                            on_change=update_revision, 
                                            args=(st.session_state.revision,))
            
            # Update the revision state whenever there is a change in the text area
            if revision_current != st.session_state.revision:
                st.session_state.revision = revision_current
            
            st.markdown(""" 
                        <p> If you finish your revision, please click Finish Revision. Otherwise, your data will be lost. </p> 
                        <br><br>
                        """, unsafe_allow_html=True)
            

            click_finish_revision = st.button("Finish Revision!")
            if click_finish_revision:
                st.session_state.finish_revision = True

                with st.status("Finalizing Your Revision...", expanded=True) as revision_store_status:
                    st.write("Storing Your Revision...")
                    time.sleep(1)
                    st.write("Analyzing Your Revision...")
                    self._store_revision_json()
                    time.sleep(2)
                    revision_store_status.update(label="Storing Completed...!", state='complete', expanded=True)
                    st.success('All of your edits have been succesfully stored. Please navigate to Review Your Edits on the left side bar.')

    def _store_revision_json(self):

        double_newline_placeholder = "_DOUBLE_NEWLINE_"

        def tokenize(text):
            return word_tokenize(text)

        def diff_paragraphs(original, revised):

            d = difflib.Differ()
            return list(d.compare(tokenize(original), tokenize(revised)))

        # def tokenize_with_newline(text):
            # new_list = []
            # for s in tokenized_sentence:
            #     if "_NEWLINE_" in s:
            #         parts = s.split("_NEWLINE_")
            #         for part in parts[:-1]:
            #             new_list.append("\n")
            #         new_list.append(parts[-1])
            #     else:
            #         new_list.append(s)

            # return new_list
            # return [token if token != '\n' else '_NEWLINE_' for token in word_tokenize(tokenized_sentence)]
        
                # Tokenizing the text while preserving newline characters
            # tokens = []
            # for token in word_tokenize(tokenized_sentence):
            #     if token == '\n':
            #         tokens.append('_NEWLINE_')
            #     else:
            #         tokens.extend(token.split('\n'))
            #         tokens.append('_NEWLINE_')
            # return tokens[:-1]  # Remove the last '_NEWLINE_' added by the loop
            
            # text = text.replace('\n\n', double_newline_placeholder)
            # tokens = word_tokenize(text)
            # # Restore \n\n in the token list
            # return [token.replace(double_newline_placeholder, '\n\n') for token in tokens]


        
        if st.session_state.finish_revision:
            # original_text_new = st.session_state.original.replace('\n', '_NEWLINE_')
            # revised_text_new = st.session_state.revision.replace('\n', '_NEWLINE_')

            # tokens_orig = word_tokenize(original_text_new)
            # tokens_revised = word_tokenize(revised_text_new)

            # tokens_orig = tokenize_with_newline(tokens_orig)
            # tokens_revised = tokenize_with_newline(tokens_revised)

            # tokens_orig = tokenize_with_newline(st.session_state.original)
            # tokens_revised = tokenize_with_newline(st.session_state.revision)
            
            # d = difflib.Differ()
            # diff = list(d.compare(tokens_orig, tokens_revised))

            # diffs = process_paragraphs(st.session_state.original, st.session_state.revision)

            original_paragraphs = st.session_state.original.split('\n\n')
            revised_paragraphs = st.session_state.revision.split('\n\n')

            all_diffs = []
            for orig_para, rev_para in zip(original_paragraphs, revised_paragraphs):
                diffs = diff_paragraphs(orig_para, rev_para)
                all_diffs.extend(diffs + ['\n\n'])

            # Creating a JSON object to store the differences
            differences = {
                "lastN": st.session_state.participant,
                "job": st.session_state.job,
                "task": st.session_state.writing_task,
                "content": st.session_state.writing_content,
                "original_text": st.session_state.original, 
                "revised_text": st.session_state.revision,
                "added": [],
                "removed": [],
                "unchanged": [],
                "diffs": all_diffs
            }

            # token_position = 0
            # for token in diffs:
            #     if token == '\n\n':
            #         token_position += 1
            #         continue 

            #     position_info = {
            #             'token': token[2:],
            #             'position': token_position
            #         }
            #     if token.startswith('+ '):
            #         differences['added'].append(position_info)
            #         token_position += 1
            #     elif token.startswith('- '):
            #         differences['removed'].append(position_info)
            #         token_position += 1
            #     elif token.startswith('  '):  # Unchanged tokens
            #         differences['unchanged'].append(position_info)
            #         token_position += 1
            
            # Converting the differences to a JSON string
            differences_json = json.dumps(differences, indent=4)
            
            if 'differences_json' not in st.session_state:
                st.session_state.differences_json = None 
            
            st.session_state.differences_json = differences_json
            # st.success('All of your edits have been succesfully stored. Please navigate to Review Your Edits on the left side bar.')
        

def main():
    st.set_page_config(page_title="Make Your Revision on GPT-4 Generated Writing Template!", 
                       page_icon="📝")
    GenerateTemplate()

if __name__ == '__main__':
    main() 