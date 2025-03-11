import streamlit as st
import re
import sqlite3
import hashlib
from blockchain_interface import BlockchainInterface
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
# Initialize BlockchainInterface
blockchain = BlockchainInterface(provider_url='HTTP://127.0.0.1:8545')  # Use Ganache or a testnet

st.set_page_config(layout="wide")

def apply_custom_css():
    st.markdown("""
        <style>
            /* Apply background color to the whole page */
            body {
                background-color: #FFE9EE;  /* Light pink background */
                margin: 0; /* Remove margin */
                padding: 0; /* Remove padding */
            }
            
            /* Target the Streamlit elements */
            .stApp {
                background-color: #FBFAF0; /* Light cream background for the entire app */
            }

            .stTitle {
                color: #333333; /* Darker title color for contrast */
            }

            .css-1d391kg {
                width: 100% !important;
            }

            .stColumns > div {
                width: 33.33% !important;
            }
        </style>
    """, unsafe_allow_html=True)
# Database setup
def init_db():
    conn = sqlite3.connect('freelance_platform.db')
    c = conn.cursor()

    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                user_type TEXT NOT NULL,
                wallet_address TEXT,
                private_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Create freelancer_profiles table
    c.execute('''CREATE TABLE IF NOT EXISTS freelancer_profiles
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                skills TEXT NOT NULL,
                experience INTEGER,
                hourly_rate REAL,
                bio TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id))''')

    # Create projects table
    c.execute('''CREATE TABLE IF NOT EXISTS projects
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                employer_id INTEGER,
                freelancer_id INTEGER,
                status TEXT DEFAULT 'open',
                budget REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                contract_address TEXT,
                FOREIGN KEY (employer_id) REFERENCES users(id),
                FOREIGN KEY (freelancer_id) REFERENCES users(id))''')

    conn.commit()
    conn.close()

# Initialize database
init_db()

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_username(username):
    # Check if the username is alphanumeric and does not contain spaces
    return bool(re.match("^[a-zA-Z0-9_]*$", username))

# Function to validate email
def is_valid_email(email):
    # Basic email pattern check
    email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    return bool(re.match(email_regex, email))

# Function to validate password
def is_valid_password(password):
    # Password must contain at least 8 characters, 1 uppercase, 1 lowercase, 1 digit, and 1 special character
    password_regex = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    return bool(re.match(password_regex, password))

def create_user(username, password, email, user_type):
    conn = sqlite3.connect('freelance_platform.db')
    c = conn.cursor()
    try:
        hashed_password = hash_password(password)
        wallet_info = blockchain.create_wallet()
        c.execute('''INSERT INTO users (username, password, email, user_type, wallet_address, private_key)
                    VALUES (?, ?, ?, ?, ?, ?)''', (username, hashed_password, email, user_type, wallet_info['address'], wallet_info['private_key']))
        user_id = c.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def verify_user(email, password):
    conn = sqlite3.connect('freelance_platform.db')
    c = conn.cursor()
    hashed_password = hash_password(password)
    c.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, hashed_password))
    user = c.fetchone()
    conn.close()
    return user

def create_freelancer_profile(user_id, skills, experience, hourly_rate, bio):
    conn = sqlite3.connect('freelance_platform.db')
    c = conn.cursor()
    c.execute('''INSERT INTO freelancer_profiles (user_id, skills, experience, hourly_rate, bio)
                VALUES (?, ?, ?, ?, ?)''', (user_id, skills, experience, hourly_rate, bio))
    conn.commit()
    conn.close()

def get_freelancer_profile(user_id):
    conn = sqlite3.connect('freelance_platform.db')
    c = conn.cursor()
    c.execute('SELECT * FROM freelancer_profiles WHERE user_id = ?', (user_id,))
    profile = c.fetchone()
    conn.close()
    return profile

def create_project(title, description, employer_id, budget):
    conn = sqlite3.connect('freelance_platform.db')
    c = conn.cursor()
    c.execute('''INSERT INTO projects (title, description, employer_id, budget, contract_address)
    VALUES (?, ?, ?, ?, ?)''', (title, description, employer_id, budget, None))
    project_id = c.lastrowid
    conn.commit()
    conn.close()
    return project_id

def get_projects(employer_id=None, freelancer_id=None, status='open'):
    conn = sqlite3.connect('freelance_platform.db')
    c = conn.cursor()
    
    query = "SELECT * FROM projects WHERE status = ?"
    params = [status]

    if employer_id:
        query += " AND employer_id = ?"
        params.append(employer_id)
    elif freelancer_id:
        query += " AND freelancer_id = ?"
        params.append(freelancer_id)
    
    c.execute(query, params)
    projects = c.fetchall()
    conn.close()
    return projects

def get_all_freelancers():
    conn = sqlite3.connect('freelance_platform.db')
    c = conn.cursor()
    c.execute('''SELECT users.id, users.username, users.email, freelancer_profiles.skills, 
                freelancer_profiles.experience, freelancer_profiles.hourly_rate, 
                freelancer_profiles.bio, users.wallet_address
                FROM users 
                JOIN freelancer_profiles ON users.id = freelancer_profiles.user_id
                WHERE users.user_type = 'freelancer'
                ''')
    freelancers = c.fetchall()
    conn.close()
    return freelancers

def match_freelancers(project_description, required_skills):
    freelancers = get_all_freelancers()
    if not freelancers:
        return []

    project_text = f"{project_description} {required_skills}"
    texts = [project_text]
    freelancer_data = []

    for freelancer in freelancers:
        freelancer_text = f"{freelancer[3] or ''} {freelancer[4] or ''} {freelancer[6] or ''}"
        texts.append(freelancer_text)
        freelancer_data.append({
            'id': freelancer[0],
            'username': freelancer[1],
            'email': freelancer[2],
            'skills': freelancer[3],
            'experience': freelancer[4],
            'hourly_rate': freelancer[5],
            'bio': freelancer[6],
            'wallet_address': freelancer[7]
        })

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])

    for idx, score in enumerate(cosine_similarities[0]):
        freelancer_data[idx]['match_score'] = score
    matched_freelancers = [freelancer for freelancer in freelancer_data if freelancer['match_score'] > 0]

    # Sort the freelancers by match score in descending order
    matched_freelancers = sorted(matched_freelancers, key=lambda x: x['match_score'], reverse=True)

    return matched_freelancers

# Streamlit UI


if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def sidebar_navigation():
    if st.session_state.user:
        st.sidebar.title("Navigation")
        user_type = st.session_state.user[4]

        if user_type == 'employer':
            options = ["Post Project", "My Projects", "Find Freelancers", "Wallet"]
        else:
            options = ["My Profile", "Available Projects", "My Projects", "Wallet"]

        choice = st.sidebar.selectbox("Menu", options)

        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.session_state.page = 'home'
            st.rerun()

        return choice

def home_page():
    apply_custom_css()
    st.title("Blockchain-Based Freelancing Platform")

    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.image(r"C:\Users\91812\Downloads\blockchain based freelancing\blockchain based freelancing\freelancer-img.png", use_container_width=True)

    
    with col2:
        st.header("New User?")
        user_type = st.selectbox("Select User Type", ["Employer", "Freelancer"])
        if st.button("Register"):
            st.session_state.page = 'register'
            st.session_state.registration_type = user_type.lower()
            st.rerun()

    with col3:
        st.header("Existing User?")
        if st.button("Login"):
            st.session_state.page = 'login'
            st.rerun()

def register_page():
    apply_custom_css()
    st.title("Registration")
    user_type = st.session_state.registration_type

    with st.form(f"{user_type}_registration"):
        st.subheader(f"{user_type.capitalize()} Registration")

        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if user_type == 'freelancer':
            skills = st.text_input("Skills (comma-separated)")
            experience = st.number_input("Years of Experience", min_value=0)
            hourly_rate = st.number_input("Hourly Rate ($)", min_value=0)
            bio = st.text_area("Bio")

        if st.form_submit_button("Register"):
            # Validate user inputs
            if not username:
                st.error("Username cannot be empty!")
                return
            if not is_valid_username(username):
                st.error("Username must be alphanumeric and cannot contain spaces!")
                return

            if not is_valid_email(email):
                st.error("Please enter a valid email address!")
                return

            if not is_valid_password(password):
                st.error("Password must be at least 8 characters long, include 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character!")
                return

            if password != confirm_password:
                st.error("Passwords don't match!")
                return

            # Proceed with registration
            user_id = create_user(username, password, email, user_type)

            if user_id:
                if user_type == 'freelancer':
                    create_freelancer_profile(user_id, skills, experience, hourly_rate, bio)
                st.success("Registration successful! Please login.")
                st.session_state.page = 'login'
                st.rerun()
            else:
                st.error("Username or email already exists!")
                
def login_page():
    apply_custom_css()
    st.title("Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.form_submit_button("Login"):
            user = verify_user(email, password)
            if user:
                st.session_state.user = user
                st.session_state.page = 'dashboard'
                st.rerun()
            else:
                st.error("Invalid credentials!")

def post_project():
    apply_custom_css()
    st.subheader("Post New Project")

    with st.form("project_form"):
        title = st.text_input("Project Title")
        description = st.text_area("Project Description")
        budget = st.number_input("Budget ($)", min_value=0.0)

        # Validation to check if all fields are filled
        if st.form_submit_button("Post Project"):
            # Check if any field is empty or budget is zero
            if not title or not description or budget <= 0.0:
                st.error("Please fill in all fields and set a valid budget greater than 0.")
            else:
                # Assuming create_project() returns a project ID
                project_id = create_project(title, description, st.session_state.user[0], budget)
                if project_id:
                    st.success("Project posted successfully!")
                else:
                    st.error("Failed to post the project. Please try again.")

def delete_project(project_id, employer_id):
    conn = sqlite3.connect('freelance_platform.db')
    c = conn.cursor()
    c.execute('DELETE FROM projects WHERE id = ? AND employer_id = ?', (project_id, employer_id))
    conn.commit()
    conn.close()

def view_projects(employer_id=None, freelancer_id=None, available=False):
    apply_custom_css()
    conn = sqlite3.connect('freelance_platform.db')
    c = conn.cursor()

    if employer_id:
        # Show projects posted by this employer
        c.execute('SELECT * FROM projects WHERE employer_id = ?', (employer_id,))
    elif freelancer_id and not available:
        # Show only assigned projects for this freelancer
        c.execute('SELECT * FROM projects WHERE status = "assigned" AND freelancer_id = ?', (freelancer_id,))
    elif available:
        # Show only open projects (not assigned)
        c.execute('SELECT * FROM projects WHERE status = "open" AND freelancer_id IS NULL')
    else:
        # Default: Show open projects
        c.execute('SELECT * FROM projects WHERE status = "open"')

    projects = c.fetchall()
    conn.close()

    if not projects:
        st.write("No projects found.")
        return

    for project in projects:
        with st.expander(f"Project: {project[1]}"):
            st.write(f"Description: {project[2]}")
            st.write(f"Budget: ${project[6]}")
            st.write(f"Status: {project[5]}")

            # Freelancer can apply for open projects
            if st.session_state.user[4] == 'freelancer' and project[5] == 'open':
                if st.button("Apply", key=f"apply_{project[0]}"):
                    conn = sqlite3.connect('freelance_platform.db')
                    c = conn.cursor()
                    c.execute('UPDATE projects SET freelancer_id = ?, status = ? WHERE id = ?',
                    (st.session_state.user[0], 'assigned', project[0]))
                    conn.commit()
                    conn.close()
                    st.success("Applied successfully!")
                    st.rerun()  # Refresh the page

            # Freelancer can mark assigned projects as completed
            if st.session_state.user[4] == 'freelancer' and project[5] == 'assigned' and project[3] == st.session_state.user[0]:
                if st.button("Mark as Completed", key=f"complete_{project[0]}"):
                    try:
                        blockchain.complete_work(project[7], st.session_state.user[6])  # Freelancer's private key
                        conn = sqlite3.connect('freelance_platform.db')
                        c = conn.cursor()
                        c.execute('UPDATE projects SET status = ? WHERE id = ?', ('completed', project[0]))
                        conn.commit()
                        conn.close()
                        st.success("Job marked as completed! Waiting for employer approval.")
                        st.rerun()  # Refresh the page
                    except Exception as e:
                        st.error(f"Failed to complete job: {str(e)}")

            # Employer can release payment for completed projects
            if st.session_state.user[4] == 'employer' and project[5] == 'completed' and project[2] == st.session_state.user[0]:
                if st.button("Release Payment", key=f"release_{project[0]}"):
                    try:
                        blockchain.release_payment(project[7], st.session_state.user[6])  # Employer's private key
                        conn = sqlite3.connect('freelance_platform.db')
                        c = conn.cursor()
                        c.execute('UPDATE projects SET status = ? WHERE id = ?', ('paid', project[0]))
                        conn.commit()
                        conn.close()
                        st.success("Payment released successfully!")
                        st.rerun()  # Refresh the page
                    except Exception as e:
                        st.error(f"Failed to release payment: {str(e)}")

            # Employer can delete an open project
            if st.session_state.user[4] == 'employer' and project[5] == 'open' and project[2] == st.session_state.user[0]:
                if st.button("Delete Project", key=f"delete_{project[0]}"):
                    conn = sqlite3.connect('freelance_platform.db')
                    c = conn.cursor()
                    c.execute('DELETE FROM projects WHERE id = ?', (project[0],))
                    conn.commit()
                    conn.close()
                    st.success("Project deleted successfully!")
                    st.rerun()  # Refresh the page
                    
            if st.session_state.user[4] == 'employer' and project[5] == 'open':  # Ensure only employers see the delete option
                if st.button("Delete Project", key=f"delete_{project[0]}"):
                    delete_project(project[0], employer_id)
                    st.success("Project deleted successfully!")
                    st.rerun()
# Add at the top with other session state initializations
if 'refresh_projects' not in st.session_state:
    st.session_state.refresh_projects = False
def find_freelancers_page():
    apply_custom_css()
    st.subheader("Find Freelancers")

    # Preserve search parameters across reruns
    if 'search_params' not in st.session_state:
        st.session_state.search_params = {
            'project_id': None,
            'description': '',
            'skills': ''
        }

    # Project selection
    projects = get_projects(employer_id=st.session_state.user[0], status='open')
    if not projects:
        st.warning("You have no open projects. Please post a project first.")
        return

    project_options = {p[0]: p[1] for p in projects}
    selected_project_id = st.selectbox(
        "Select a Project to Hire For",
        options=list(project_options.keys()),
        format_func=lambda x: project_options[x],
        key='project_select'
    )

    # Update session state when project changes
    if st.session_state.search_params['project_id'] != selected_project_id:
        st.session_state.search_params = {
            'project_id': selected_project_id,
            'description': next(p[2] for p in projects if p[0] == selected_project_id),
            'skills': ''
        }

    # Editable search fields
    project_description = st.text_area(
        "Project Description",
        value=st.session_state.search_params['description'],
        key='project_desc'
    )
    required_skills = st.text_input(
        "Required Skills",
        value=st.session_state.search_params['skills'],
        key='project_skills'
    )

    # Update session state on search
    if st.button("Find Matches"):
        st.session_state.search_params.update({
            'description': project_description,
            'skills': required_skills
        })
        st.session_state.refresh_projects = True

    # Display results
    if st.session_state.refresh_projects:
        show_freelancer_matches(selected_project_id, project_description, required_skills)

def show_freelancer_matches(project_id, description, skills):
    matched_freelancers = match_freelancers(description, skills)
    
    if not matched_freelancers:
        st.info("No freelancers found matching your requirements.")
        return

    st.write("### Matched Freelancers")
    
    for freelancer in matched_freelancers:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"**{freelancer['username']}**  \n"
                            f"Skills: {freelancer['skills']}  \n"
                            f"Experience: {freelancer['experience']} yrs  \n" 
                            f"Rate: ${freelancer['hourly_rate']}/hr")
            
            with col2:
                st.markdown(f"Match Score: {freelancer['match_score']*100:.1f}%  \n"
                            f"Wallet: `{freelancer['wallet_address']}`")
            
            with col3:
                if st.button(
                    "Hire",
                    key=f"hire_{freelancer['id']}_{project_id}",
                    use_container_width=True
                ):
                    handle_hire_action(project_id, freelancer)

def handle_hire_action(project_id, freelancer):
    try:
        # Get project details
        conn = sqlite3.connect('freelance_platform.db')
        c = conn.cursor()
        c.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        project = c.fetchone()
        
        if not project:
            st.error("Project not found!")
            return

        # Deploy smart contract
        contract_address = blockchain.deploy_contract(
            employer_private_key=st.session_state.user[6],
            freelancer_address=freelancer['wallet_address'],
            job_description=project[2],  # project description
            amount=project[6]  # project budget
        )

        # Update project in database
        c.execute('''UPDATE projects 
                    SET freelancer_id = ?, 
                        status = ?, 
                        contract_address = ? 
                    WHERE id = ?''',
                (freelancer['id'], 'assigned', contract_address, project_id))
        conn.commit()
        
        # Update session state
        st.session_state.refresh_projects = False
        st.success(f"Hired {freelancer['username']}! Contract: {contract_address}")
        
        # Force refresh the UI
        st.rerun()
    
    except sqlite3.Error as e:
        st.error(f"Database error: {str(e)}")
    except Exception as e:
        st.error(f"Contract deployment failed: {str(e)}")
    finally:
        conn.close()

def wallet_page():
    apply_custom_css()
    st.subheader("Wallet")

    wallet_address = st.session_state.user[5]
    private_key = st.session_state.user[6]

    if wallet_address:
        # Convert the address to checksum format
        checksum_address = blockchain.w3.to_checksum_address(wallet_address)
        
        st.write("### Your Wallet Details")
        st.code(f"Address: {checksum_address}")
        st.code(f"Private Key: {private_key}")

        # Get balance using the checksum address
        balance = blockchain.w3.eth.get_balance(checksum_address)
        st.write(f"Balance: {blockchain.w3.from_wei(balance, 'ether')} ETH")

def main():
    if st.session_state.page == 'home':
        home_page()
    elif st.session_state.page == 'register':
        register_page()
    elif st.session_state.page == 'login':
        login_page()
    elif st.session_state.page == 'dashboard':
        choice = sidebar_navigation()
        wallet_address = st.session_state.user[5]  # Employer's wallet address
        balance_wei = blockchain.w3.eth.get_balance(wallet_address)
        balance_eth = blockchain.w3.from_wei(balance_wei, 'ether')
        # st.write(f"Employer Wallet Balance: {wallet_address} ETH")

        #st.write(f"Employer Wallet Balance: {balance_eth} ETH")

        # if balance_eth < 0.01:  # Set a minimum balance threshold
        #     st.error("⚠️ Insufficient funds! Add ETH to your wallet before proceeding.")
        #     st.stop()

        if not choice:
            return

        if choice == "Post Project":
            post_project()
        elif choice in ["My Projects", "Available Projects"]:
            if st.session_state.user[4] == 'employer':
                view_projects(employer_id=st.session_state.user[0])
            else:
                if choice == "My Projects":
                    view_projects(freelancer_id=st.session_state.user[0])
                else:  # choice == "Available Projects"
                    view_projects(available=True)

        elif choice == "Find Freelancers":
            find_freelancers_page()
        elif choice == "Wallet":
            wallet_page()
        elif choice == "My Profile":
            st.subheader("My Profile")
            profile = get_freelancer_profile(st.session_state.user[0])
            if profile:
                st.write(f"Skills: {profile[2]}")
                st.write(f"Experience: {profile[3]} years")
                st.write(f"Hourly Rate: ${profile[4]}/hour")
                st.write(f"Bio: {profile[5]}")

if __name__ == "__main__":
    main()