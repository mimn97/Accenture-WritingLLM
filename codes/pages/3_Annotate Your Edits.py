import streamlit as st
import json
from collections import defaultdict
import json
import re
import boto3
import os

# Global variables
# aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
# aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

aws_access_key_id = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_access_key = st.secrets["AWS_SECRET_ACCESS_KEY"]

def split_html_into_sentences(html_text):
    html_sentences = []
    sentences = re.split(r'(?<=[.!?])', html_text)  # Split content into sentences
        
    # Filtering and cleaning the sentences
    sentences = [s.strip() for s in sentences if s]
    html_sentences.extend(sentences)
    
    return html_sentences

def upload_new_annotation_to_s3(annot_data, participant_name):

    s3 = boto3.client('s3')
    bucket_name = 'accenture-writingllm'
    file_key = '{}.jsonl'.format(participant_name)

    # Check if the file exists in S3
    try:
        s3.head_object(Bucket=bucket_name, Key=file_key)
        file_exists = True
    except:
        file_exists = False

    # Download the file if it exists
    if file_exists:
        s3.download_file(bucket_name, file_key, file_key)

    # Append new data to the file
    with open(file_key, 'a' if file_exists else 'w') as file:
        file.write(json.dumps(annot_data, ensure_ascii=False) + '\n')

    # Upload the updated file to S3
    s3.upload_file(file_key, bucket_name, file_key)

    # Optionally delete the local file
    os.remove(file_key)


class StKeys:
    QUERY_POOL = []
    CUR_QUERY_ID = -1
    ANNOTATION_TARGETS = ""

class RevisionAnnotation():
    def __init__(self) -> None:

        if 'is_annotation' not in st.session_state:
            st.session_state.is_annotation = False

        # Create annotation key to st.session_state
        if 'sent_annotation' not in st.session_state:
            st.session_state.sent_annotation = json.loads(st.session_state.differences_json)
        
        self.is_done = False
        self._get_sentences() 
        self._select_annotation_targets()
        self.show_annotation_targets()

    @property
    def cur_query_id(self):
        if StKeys.CUR_QUERY_ID not in st.session_state:
            st.session_state[StKeys.CUR_QUERY_ID] = 0
        return st.session_state[StKeys.CUR_QUERY_ID]
    
    @cur_query_id.setter
    def cur_query_id(self, id):
        st.session_state[StKeys.CUR_QUERY_ID] = id

    @property
    def annotation_targets(self):
        if StKeys.ANNOTATION_TARGETS not in st.session_state:
            st.session_state[StKeys.ANNOTATION_TARGETS] = []
        return st.session_state[StKeys.ANNOTATION_TARGETS]    

    @annotation_targets.setter
    def annotation_targets(self, targets):
        st.session_state[StKeys.ANNOTATION_TARGETS] = targets

    @property
    def query_pool(self):
        if StKeys.QUERY_POOL not in st.session_state:
            st.session_state[StKeys.QUERY_POOL] = []

        return st.session_state[StKeys.QUERY_POOL]

    @query_pool.setter
    def query_pool(self, queries):
        st.session_state[StKeys.QUERY_POOL] = queries

    def _get_sentences(self):
        self.query_pool = split_html_into_sentences(st.session_state.visual_edit)

    def _select_annotation_targets(self):
        if self.cur_query_id >= len(self.query_pool):
            self.is_done = True 
        else:
            cur_query = self.query_pool[self.cur_query_id]
            self.annotation_targets = cur_query 

    def show_annotation_targets(self):
        if not self.is_done:
            if len(self.annotation_targets) == 0:
                self._select_annotation_targets()
                self.cur_query_id += 1 
            
            # st.session_state.is_annotation = st.button("Start Your Annotation")

            # if st.session_state.is_annotation:

                # Sentence & Intention Input
            st.markdown(f"<h3> Sentence </h3>", unsafe_allow_html=True)
            st.markdown(f"<div style='border: 2px solid blue; padding: 10px;'>{self.annotation_targets}</div>", unsafe_allow_html=True)
            st.markdown(f"""
                        <mark>Note: The removed span of texts in the original text were <u>crossed out</u>, while newly added edits from you are colored in <b style="color:red">red</b>. </mark>
                        """, unsafe_allow_html=True)
            # Intention text box
            edit_intention = st.text_area("Give Your Reasons Behind those Edits. (If you don't see any edits, then write N/A .)", 
                                                height=100, max_chars=700, 
                                                placeholder="e.g., Make the sentence sound more catchy to customer, etc.")
                
            # if 'edit_intention'

            label_annotations = defaultdict(bool)

            form = st.form("checkboxes", clear_on_submit=True)
            with form:                    
                # Intention checkbox
                fluency = st.checkbox("**Fluency** (e.g., Fix grammatical errors)")
                coherency = st.checkbox("**Coherency** (e.g., Improve logical linking and consistency as a whole)")
                clarity = st.checkbox("**Clarity** (e.g., Make texts formal, concise, readable, and understandable)")
                style = st.checkbox("**Style Change** (e.g., Convey your own preferences, such as voice, tone, emotions, etc.)")
                meaning = st.checkbox("**Meaning Change** (e.g., Update or add new information)")
                domain = st.checkbox("**Domain-specific Knowledge** (e.g., Include more knowledge of your domain background)")
                other = st.checkbox("**Others** (If you click this, please give a detailed explanation to the above textbox.)")
                na = st.checkbox("**N/A** (Check only if you did not edit any span of the sentence.)")

                label_annotations['fluency'] = fluency
                label_annotations['coherency'] = coherency
                label_annotations['clarity'] = clarity 
                label_annotations['style'] = style 
                label_annotations['meaning'] = meaning
                label_annotations['domain'] = domain
                label_annotations['other'] = other
                label_annotations['na'] = na

            st.markdown("------")

            save_btn_submit = form.form_submit_button("Next")

            if save_btn_submit:
                if edit_intention == "":
                    st.error("Fill out the Reasons Behind Those Edits in the above text box.")
                    return 
        
                annotated_intent = list(dict(filter(lambda e:e[1]==True, label_annotations.items())).keys())
                if len(annotated_intent) < 1:
                    st.error("Any of the checkboxes is not selected. Please choose all checkboxes that apply.")
                    return

                annot_data = {
                    "revision_info": st.session_state.sent_annotation, 
                    "sent_idx": self.cur_query_id,
                    "edit_sentence": self.annotation_targets, 
                    "edit_intent": edit_intention,
                    "label": annotated_intent
                }

                # with open('../data/{}.jsonl'.format(st.session_state.participant), 'a') as out_file:
                #     l = json.dumps(annot_data, ensure_ascii=False)
                #     out_file.write(f"{l}\n")

                upload_new_annotation_to_s3(annot_data, st.session_state.participant)

                # st.markdown(f" Stored Data: {st.session_state.sent_annotation}", unsafe_allow_html=True)

                self.cur_query_id += 1
                self._select_annotation_targets()
                st.experimental_rerun()

        else:
            st.success("Congratulation. You have finished your tasks. ", icon="👍") 

# def main():

#     st.set_page_config(page_title="Annotate Your Edits")
#     demo = RevisionAnnotation()

def main():

    st.set_page_config(page_title="Annotate Your Edits")
    
    # Brief Explanation
    st.markdown("<h2> Annotate Your Edits </h2>", unsafe_allow_html=True)
    st.markdown("""
            <br> Now, it's time to give your opinions and reasons about the edits that you have made on the original GPT-4 text.
            We would like to take a deeper look at your intention behind those edits. 
            <br>
            Here are the detailed instructions:
            <ol>
                <li> First, you will see each sentence with your revision. At the below textbox, give your reason why you have changed like that." </li>
                <li> Then, select checkboxes that apply to your intentions. </li>
                <li> After clicking all checkboxes in a sentence, then go to the next button to see the next sentence. </li>
            </ol>
            <br>
            <p> <span style="color:red"> WARNING: </span> There is no 'back' button to change your response in the previsou sentences. Please make sure to review your responses and then go to the next sentence. </p>
            <hr>
            """, unsafe_allow_html=True)

    # Create two columns
    col1, col2 = st.columns(2)

    # In the left column, show st.session_state.visual_edit
    with col1:
        st.markdown("<h2>Visual Edit</h2>", unsafe_allow_html=True)
        st.markdown(st.session_state.visual_edit, unsafe_allow_html=True)

    # In the right column, show the rest of the interface
    with col2:
        demo = RevisionAnnotation()

if __name__ == '__main__':
    main()




