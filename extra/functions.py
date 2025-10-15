import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import google.generativeai as genai
import io
# --- Load config ---
with open('main/config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# --- Initialize authenticator ---
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

if 'show_register' not in st.session_state:
    st.session_state['show_register']=False
# flag for register and login form
if not st.session_state['authentication_status']:

    # st.session_state['show_register']=False
    with st.sidebar:
        if st.button('login'):
            st.session_state['show_register']=False
        if st.button('register'):
            st.session_state['show_register']=True
    
    
    

    if not st.session_state['show_register']:
        authenticator.login()
        
        
    if st.session_state['show_register']==True:
        email,username,name=authenticator.register_user(password_hint=False,captcha=False)
        if email and username and name:
            st.write('successfully registered',name)
            
            
            with open('app/config.yaml','w') as file:
                yaml.dump(config,file,default_flow_style=False)
            st.session_state['show_register']=False
            st.rerun()

else:
    with st.sidebar:
        st.write(f"welcome {config['credentials']['usernames'][st.session_state['username']]['first_name']}")
        authenticator.logout()
        
        
        
        

# Page config
    st.set_page_config(page_title="AI Math Assistant", page_icon="🧮", layout="wide")

    # Initialize session state for chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chat_session' not in st.session_state:
        st.session_state.chat_session = None

    # Title and description
    st.title("🧮 AI-Powered Math Assistant")
    st.markdown("Draw, upload, or chat about math problems using Google Gemini!")

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        api_key = st.secrets["GOOGLE_API_KEY"]

        st.markdown("---")
        
        # Mode selection
        st.header("📋 Mode")
        mode = st.radio(
            "Choose input mode:",
            ["✏️ Draw", "📤 Upload Image", "💬 Chat"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 📝 Instructions")
        
        if mode == "✏️ Draw":
            st.markdown("""
            1. Draw a math expression on the canvas
            2. Click 'Solve Expression'
            3. Get instant solution!
            """)
        elif mode == "📤 Upload Image":
            st.markdown("""
            1. Upload an image of a math problem
            2. Click 'Solve Expression'
            3. Get instant solution!
            """)
        else:
            st.markdown("""
            1. Type your math question
            2. Ask for explanations or solutions
            3. Have a conversation about math!
            """)
        
        st.markdown("---")
        st.markdown("### 💡 Examples")
        st.markdown("- Simple: 2 + 2")
        st.markdown("- Complex: 15 × 3 + 20")
        st.markdown("- Equations: x + 5 = 10")
        st.markdown("- Word problems")
        st.markdown("- Calculus, algebra, geometry")

    # Function to initialize Gemini model
    def get_gemini_model(api_key):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            return model, None
        except Exception as e:
            return None, str(e)

    # Function to process image with Gemini
    def solve_with_gemini(image_data, api_key, is_pil=False):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Handle different image inputs
            if is_pil:
                rgb_img = image_data.convert('RGB')
            else:
                # Convert canvas to image
                img = Image.fromarray(image_data.astype('uint8'), 'RGBA')
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
            
            # Create prompt
            prompt = """Analyze this mathematical expression or problem and:
    1. Recognize the mathematical expression/problem written
    2. Solve it step by step with clear explanations
    3. Provide the final answer

    Format your response as:
    **Expression/Problem:** [what you see]
    **Solution:** [detailed step by step solution]
    **Answer:** [final answer]

    Be thorough and educational in your explanation."""
            
            # Generate response
            response = model.generate_content([prompt, rgb_img])
            return response.text
            
        except Exception as e:
            return f"❌ Error: {str(e)}\n\n**Troubleshooting:**\n1. Make sure your API key is from https://aistudio.google.com/app/apikey\n2. Verify your API key is correct\n3. Check if you have quota remaining\n4. Ensure the image is clear and readable"

    # Function to initialize or get chat session
    def get_chat_session(api_key):
        try:
            if st.session_state.chat_session is None:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                st.session_state.chat_session = model.start_chat(history=[])
            return st.session_state.chat_session
        except Exception as e:
            st.error(f"Error initializing chat: {str(e)}")
            return None

    # Main content based on mode
    if mode == "💬 Chat":
        st.subheader("💬 Math Chat Assistant")
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me anything about math..."):
            if not api_key:
                st.error("⚠️ Please enter your Gemini API key in the sidebar!")
            else:
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Get AI response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            chat = get_chat_session(api_key)
                            if chat:
                                # Send message with math tutor context
                                full_prompt = f"You are a helpful and patient math tutor. Help the student with their question: {prompt}"
                                response = chat.send_message(full_prompt)
                                response_text = response.text
                            else:
                                response_text = "❌ Could not initialize chat session. Please check your API key."
                        except Exception as e:
                            response_text = f"❌ Error: {str(e)}"
                        
                        st.markdown(response_text)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response_text})
        
        # Clear chat button
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.chat_session = None
                st.rerun()

    else:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if mode == "✏️ Draw":
                st.subheader("📐 Draw Your Expression")
                stroke_width = st.sidebar.slider("Stroke width:", 1, 25, 3)
                stroke_color = st.sidebar.color_picker("Stroke color:")
                bg_color = st.sidebar.color_picker("Background color:", "#ffffff")
                drawing_mode = st.sidebar.selectbox(
                    "Drawing tool:", ("freedraw", "line", "rect", "circle", "transform")
                )
                realtime_update = st.sidebar.checkbox("Update in realtime", True)

                # Canvas for drawing
                canvas_result = st_canvas(
                    fill_color="rgba(255, 165, 0, 0.3)",
                    stroke_width=stroke_width,
                    stroke_color=stroke_color,
                    background_color=bg_color,
                    update_streamlit=realtime_update,
                    height=700,
                    width=1200,
                    drawing_mode=drawing_mode,
                    key="canvas",
                )
                # Drawing canvas
                # canvas_result = st_canvas(
                #     fill_color="rgba(255, 255, 255, 0)",
                #     stroke_width=5,
                #     stroke_color="#000000",
                #     background_color="#FFFFFF",
                #     height=400,
                #     width=500,
                #     drawing_mode="freedraw",
                #     key="canvas",
                # )
                
                image_to_process = canvas_result.image_data if canvas_result.image_data is not None else None
                is_pil = False
            
            else:  # Upload Image mode
                st.subheader("📤 Upload Math Problem Image")
                
                uploaded_file = st.file_uploader(
                    "Choose an image file",
                    type=["png", "jpg", "jpeg"],
                    help="Upload a clear image of your math problem"
                )
                
                if uploaded_file is not None:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Uploaded Image", use_container_width=True)
                    image_to_process = image
                    is_pil = True
                else:
                    image_to_process = None
                    is_pil = False
        
        with col2:
            st.subheader("🤖 AI Solution")
            result_container = st.container()
        
        # Buttons
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            solve_button = st.button("🎯 Solve Expression", type="primary", use_container_width=True)
        
        with col_btn2:
            if mode == "✏️ Draw":
                if st.button("🗑️ Clear Canvas", use_container_width=True):
                    st.rerun()
        
        # Process when solve button is clicked
        if solve_button:
            if not api_key:
                st.error("⚠️ Please enter your Gemini API key in the sidebar!")
            elif image_to_process is None:
                st.warning(f"⚠️ Please {'draw something on the canvas' if mode == '✏️ Draw' else 'upload an image'} first!")
            else:
                with st.spinner("🔍 Analyzing your image..."):
                    result = solve_with_gemini(image_to_process, api_key, is_pil)
                    
                    with result_container:
                        st.markdown("### 📊 Result")
                        st.markdown(result)
                        
                        if not result.startswith("❌"):
                            st.success("✅ Analysis complete!")
                            
                            # Option to continue in chat
                            if st.button("💬 Continue this in chat mode"):
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": f"I just solved this problem:\n\n{result}"
                                })
                                st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Powered by Google Gemini 2.5 pro 🤖</p>
        <p><small>Tip: Write clearly or upload high-quality images for best results!</small></p>
    </div>
    """, unsafe_allow_html=True)