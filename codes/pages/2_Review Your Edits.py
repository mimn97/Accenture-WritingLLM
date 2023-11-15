import streamlit as st
import json


def visualize_edits(string_json_data):

    json_data = json.loads(string_json_data)
    added_tokens = json_data['added']
    removed_tokens = json_data['removed']
    unchanged_tokens = json_data['unchanged']
    
    all_tokens = []
    for token in unchanged_tokens:
        all_tokens.append((token['token'], token['position'], 'unchanged'))
    
    for token in removed_tokens:
        all_tokens.append((token['token'], token['position'], 'removed'))
        
    for token in added_tokens:
        all_tokens.append((token['token'], token['position'], 'added'))
        
    all_tokens.sort(key=lambda x: x[1])
    
    html_text = ""
    for token in all_tokens:
        if token[2] == 'removed':
            html_text += f'<s>{token[0]}</s> '
        elif token[2] == 'added':
            html_text += f'<span style="color:red;">{token[0]}</span> '
        else:
            html_text += f'{token[0]} '            
    return html_text


def main():

    st.set_page_config(page_title="Compare with Edits")
    st.sidebar.header("Visualizing the edited texts")

    visual_edit = visualize_edits(st.session_state.differences_json)
    st.markdown("""
                <h2> Comparing the Original Text and Your Revision </h2> 
                """, unsafe_allow_html=True)
    st.markdown(visual_edit, unsafe_allow_html=True)
    st.markdown("""
                <br><br>
                <p> If you do not see your revision, then please go back to Revision page on the left side bar, and click 'Finish Annotation' button at the bottom. </p>
                <br><br>
                """, unsafe_allow_html=True)
    if 'visual_edit' not in st.session_state:
        st.session_state.visual_edit = visual_edit

if __name__ == '__main__':
    main()


























