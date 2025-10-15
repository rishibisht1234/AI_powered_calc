import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import google.generativeai as genai
import io
import json # Import the JSON library

# Page config must be the first Streamlit command
st.set_page_config(page_title="AI Math Assistant", page_icon="🧮", layout="wide")

st.markdown("""
<style>
header[data-testid="stHeader"] {
    background-color: #D78FEE;
    height: 70px;
    color: #4E56C0;
    text-align: center;
    position: relative;
}
header[data-testid="stHeader"]::after {
    content: "🧮 AI-Powered Math Assistant";
    position: absolute;
    top: 30%;
    left: 50%;
    transform: translate(-50%, -25%);
    font-size: 2rem;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- CHANGE 1: CSS to reduce the header gap ---
page_bg_img = """
<style>
/* This rule reduces the vertical gap after your custom header */
h1 {
    margin-top: -130px !important; 
}
/* Main app background */
[data-testid="stAppViewContainer"] {
    background-color: #FDCFFA;  
}
/* Header background */
[data-testid="stHeader"] {
    background-color: #D78FEE; 
}
/* Sidebar background */
[data-testid="stSidebar"] {
    background-color: #9B5DE0;  
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# Titles using Markdown + HTML (removed the inline style as it's now in the CSS block)
st.markdown("<h1 style='color:#4E56C0'>Draw, upload, or chat about math problems!</h1>",unsafe_allow_html=True)


# --- CHANGE 2.1: Initialize new session state variables ---
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'chat_session' not in st.session_state:
    st.session_state.chat_session = None
if 'quiz_questions' not in st.session_state:
    st.session_state.quiz_questions = []
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = []
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
# Added states for persistent feedback
if 'solution_result' not in st.session_state: 
    st.session_state.solution_result = None
if 'feedback_given' not in st.session_state: 
    st.session_state.feedback_given = None
# ADDED: Key for clearing the canvas
if 'canvas_clear_key' not in st.session_state:
    st.session_state.canvas_clear_key = 0


# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.secrets["GOOGLE_API_KEY"]
    st.markdown("---")
    st.header("📋 Mode")
    mode = st.radio(
        "Choose input mode:",
        ["✏️ Draw", "📤 Upload Image", "💬 Chat", "🎯 Quiz"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("### 📝 Instructions")
    if mode == "✏️ Draw":
        st.markdown("1. Draw an expression\n2. Click 'Solve'\n3. Get the solution!")
    elif mode == "📤 Upload Image":
        st.markdown("1. Upload an image\n2. Click 'Solve'\n3. Get the solution!")
    elif mode == "🎯 Quiz":
        st.markdown("1. Select a topic\n2. Start the quiz\n3. Test your knowledge!")
    else: # Chat mode
        st.markdown("1. Type a question\n2. Get explanations\n3. Chat about math!")
    st.markdown("---")
    st.markdown("### 💡 Examples")
    st.markdown("- Simple: 2 + 2\n- Complex: 15 × 3 + 20\n- Equations: x + 5 = 10")

# --- Function Definitions (with corrected model name) ---
def get_gemini_model(api_key, model_name='gemini-2.0-flash-exp'):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        return model, None
    except Exception as e:
        return None, str(e)

def solve_with_gemini(image_data, api_key, is_pil=False):
    model, error = get_gemini_model(api_key)
    if error:
        return f"❌ Error initializing model: {error}"
    try:
        if is_pil:
            rgb_img = image_data.convert('RGB')
        else:
            img = Image.fromarray(image_data.astype('uint8'), 'RGBA')
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
        prompt = """Analyze this mathematical expression. Solve it step-by-step and provide a final answer in the format: **Answer:** [final answer]"""
        response = model.generate_content([prompt, rgb_img])
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_chat_session(api_key):
    try:
        if st.session_state.chat_session is None:
            model, error = get_gemini_model(api_key)
            if error:
                st.error(f"Error initializing chat: {error}")
                return None
            st.session_state.chat_session = model.start_chat(history=[])
        return st.session_state.chat_session
    except Exception as e:
        st.error(f"Error initializing chat: {str(e)}")
        return None

def generate_quiz(topic, difficulty, api_key):
    model, error = get_gemini_model(api_key)
    if error:
        st.error(f"Error initializing model for quiz: {error}")
        return None
    prompt = f"""You are a quiz generator. Create a 5-question multiple-choice quiz about {topic} at a {difficulty} level. Return the quiz as a valid JSON list. Each object must have keys: "question", "options" (a list of 4 strings), and "answer" (the correct option string). Do not include any text before or after the JSON list."""
    try:
        with st.spinner(f"Generating a {difficulty} {topic} quiz..."):
            response = model.generate_content(prompt)
            json_text = response.text.strip().replace("```json", "").replace("```", "")
            questions = json.loads(json_text)
            return questions
    except Exception as e:
        st.error(f"❌ Failed to generate or parse quiz. Error: {e}")
        return None

# --- Main App Logic ---

if mode == "🎯 Quiz":
    # This section is unchanged, as requested.
    st.subheader("🎯 Test Your Knowledge!")
    if not st.session_state.quiz_started:
        quiz_col1, quiz_col2 = st.columns(2)
        with quiz_col1:
            topic = st.selectbox("Choose a topic:", ["Algebra", "Calculus", "Geometry", "Trigonometry"])
        with quiz_col2:
            difficulty = st.selectbox("Choose difficulty:", ["Easy", "Medium", "Hard"])
        if st.button("🚀 Start Quiz", use_container_width=True):
            if not api_key: st.error("⚠️ Please enter your Gemini API key!")
            else:
                questions = generate_quiz(topic, difficulty, api_key)
                if questions:
                    st.session_state.quiz_questions = questions
                    st.session_state.current_question_index = 0
                    st.session_state.user_answers = []
                    st.session_state.quiz_started = True
                    st.rerun()
    else:
        idx = st.session_state.current_question_index
        if idx < len(st.session_state.quiz_questions):
            q = st.session_state.quiz_questions[idx]
            st.progress((idx + 1) / len(st.session_state.quiz_questions))
            st.markdown(f"### Question {idx + 1}/{len(st.session_state.quiz_questions)}")
            with st.form(key=f"question_{idx}"):
                st.markdown(f"**{q['question']}**")
                user_choice = st.radio("Choose your answer:", q['options'], index=None)
                submitted = st.form_submit_button("Submit Answer")
                if submitted:
                    if user_choice:
                        st.session_state.user_answers.append(user_choice)
                        st.session_state.current_question_index += 1
                        st.rerun()
                    else: st.warning("Please select an answer.")
        else:
            st.balloons(); st.success("🎉 Quiz Complete! 🎉")
            score = sum(1 for i, q in enumerate(st.session_state.quiz_questions) if st.session_state.user_answers[i] == q['answer'])
            st.markdown(f"### Your Final Score: **{score} out of {len(st.session_state.quiz_questions)}**")
            with st.expander("🔍 Review Your Answers"):
                for i, q in enumerate(st.session_state.quiz_questions):
                    user_ans, correct_ans = st.session_state.user_answers[i], q['answer']
                    st.markdown(f"**Question {i+1}:** {q['question']}")
                    if user_ans == correct_ans: st.markdown(f"✔️ Your answer: **{user_ans}** (Correct)")
                    else: st.markdown(f"❌ Your answer: **{user_ans}**\n➡️ Correct answer: **{correct_ans}**")
                    st.markdown("---")
            if st.button("🔄 Play Again"):
                st.session_state.quiz_started = False; st.rerun()

elif mode == "💬 Chat":
    # This section is unchanged, as requested.
    st.subheader("💬 Math Chat Assistant")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if prompt := st.chat_input("Ask me anything about math..."):
        if not api_key: st.error("⚠️ Please enter your Gemini API key!")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    chat = get_chat_session(api_key)
                    response = chat.send_message(f"You are a helpful math tutor. Help with: {prompt}")
                    response_text = response.text
                st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})

else: # Draw or Upload Mode
    # This function resets the state for a new problem
    def clear_solution_state():
        st.session_state.solution_result = None
        st.session_state.feedback_given = None

    col1, col2 = st.columns([1, 1])
    with col1:
        if mode == "✏️ Draw":
            st.subheader("📐 Draw Your Expression")

            # --- Sidebar Controls ---
            stroke_width = st.sidebar.slider("Stroke width:", 1, 50, 3)
            stroke_color_choice = st.sidebar.color_picker("Stroke color:", "#000000")
            bg_color = st.sidebar.color_picker("Background:", "#FFFFFF")
            drawing_tool_choice = st.sidebar.selectbox(
                "Drawing tool:", ("freedraw", "line", "rect", "circle", "transform")
            )
            # Add a checkbox to activate the eraser
            use_eraser = st.sidebar.checkbox("Use Eraser")

            # --- Eraser Logic ---
            # If eraser is checked, override the color and drawing tool
            if use_eraser:
                final_stroke_color = bg_color  # Eraser color is the background color
                final_drawing_tool = "freedraw"
            else:
                final_stroke_color = stroke_color_choice
                final_drawing_tool = drawing_tool_choice
            
            # --- The Canvas ---
            # Note: I fixed a syntax error in your original code where a parenthesis was misplaced.
            canvas_result = st_canvas(
                stroke_width=stroke_width,
                stroke_color=final_stroke_color,
                background_color=bg_color,
                height=400,
                width=600,
                drawing_mode=final_drawing_tool,
                display_toolbar=False,
                # UPDATED: The key is now dynamic to allow clearing
                key=f"canvas_{st.session_state.canvas_clear_key}"
            )
            realtime_update = st.sidebar.checkbox("Update in realtime", True)
            image_to_process = canvas_result.image_data if canvas_result.image_data is not None else None
            is_pil = False
        else:  # Upload Image mode
            st.subheader("📤 Upload Math Problem Image")
            uploaded_file = st.file_uploader("Choose an image", type=["png", "jpg"], on_change=clear_solution_state)
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_container_width=True)
                image_to_process = image; is_pil = True
            else:
                image_to_process = None; is_pil = False
    
    with col2:
        st.subheader("🤖 AI Solution")
        result_container = st.container(height=500, border=True)

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🎯 Solve Expression", type="primary", use_container_width=True):
            if not api_key: st.error("⚠️ Please enter your Gemini API key!")
            elif image_to_process is None: st.warning(f"⚠️ Please {'draw' if mode == '✏️ Draw' else 'upload an image'} first!")
            else:
                with st.spinner("🔍 Analyzing your image..."):
                    st.session_state.solution_result = solve_with_gemini(image_to_process, api_key, is_pil)
                    st.session_state.feedback_given = None
                st.rerun()
    with btn_col2:
        if mode == "✏️ Draw":
            # ADDED: Callback and button for clearing the canvas
            def clear_canvas():
                st.session_state.canvas_clear_key += 1 # Increment the key to force re-render

            st.button("✨ Clear Canvas", use_container_width=True, on_click=clear_canvas)
            st.button("🗑️ Clear AI Solution", use_container_width=True, on_click=clear_solution_state)

    if st.session_state.solution_result:
        with result_container:
            st.markdown(st.session_state.solution_result)
            if not st.session_state.feedback_given:
                st.info("⚠️ Please verify the solution. AI can make mistakes.", icon="🤖")
                feedback_cols = st.columns(2)
                with feedback_cols[0]:
                    if st.button("👍 Correct", use_container_width=True):
                        st.session_state.feedback_given = 'correct'
                        st.rerun()
                with feedback_cols[1]:
                    if st.button("👎 Incorrect", use_container_width=True):
                        st.session_state.feedback_given = 'incorrect'
                        st.rerun()
            elif st.session_state.feedback_given == 'correct':
                st.success("✅ Great! Analysis complete.")
                if st.button("💬 Continue this in chat mode"):
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"I just solved this problem:\n\n{st.session_state.solution_result}"
                    })
                    st.info("Added to chat history! Switch to 'Chat' mode to continue.")
            elif st.session_state.feedback_given == 'incorrect':
                st.warning("Thanks for the feedback! We'll use this to improve.")
# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Powered by Google Gemini 2.0 Flash 🤖</p>
    <p><small>Tip: Write clearly or upload high-quality images for best results!</small></p>
</div>
""", unsafe_allow_html=True)