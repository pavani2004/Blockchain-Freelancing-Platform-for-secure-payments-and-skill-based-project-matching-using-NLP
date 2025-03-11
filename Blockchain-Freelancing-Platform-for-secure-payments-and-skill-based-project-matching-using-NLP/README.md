# 🚀 Blockchain Freelancing Platform for Secure Payments and Skill-Based Project Matching Using NLP

This project is a **blockchain-based freelancing platform** that ensures **secure and automated transactions** between clients and freelancers using **smart contracts**. It leverages **NLP-based algorithms** to match freelancers with projects based on their **skills, experience, and client requirements**. The platform features a ranking system to ensure the right freelancer is chosen for the right job and allows seamless contract creation, management, and validation without third-party intervention.

---

## 📂 Project Files
```
├── app.py                    # Streamlit app for user interaction
├── blockchain_interface.py    # Handles blockchain interactions
├── compile_contract.py        # Compiles the Solidity contract
├── FreelanceContract.sol      # Solidity smart contract
├── FreelanceContract.json     # Compiled contract ABI
```

---

## 🌟 Overview
**Key features include:**  
✅ Automatic, Secure & Low-Fee Payments.  
✅ Skill-Based Project Matching Using NLP.  
✅ Comprehensive Freelancer Profiles. 
✅ Trustworthy Ranking System.  

---

## 🛠️ Dependencies
Make sure you have the following libraries installed:
```
pip install streamlit web3 eth-account scikit-learn numpy solcx
```

**Python Libraries:**  
- `streamlit` – For building the frontend  
- `web3` – For Ethereum blockchain interaction  
- `eth-account` – For managing Ethereum accounts  
- `solcx` – For compiling Solidity contracts  
- `scikit-learn` – For text similarity analysis  
- `numpy` – For numerical operations  
- `sqlite3` – For local contract data storage  
- `hashlib` – For hashing contract data  

---

## 🔧 Setup
### 1. **Clone the repository**
```
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. **Set up a virtual environment** (optional but recommended)
```
python -m venv venv
source venv/bin/activate # On Windows: .\venv\Scripts\activate
```

### 3. **Install dependencies**
```
pip install -r requirements.txt
```

### 4. **Set up the Solidity compiler**  
Ensure `solc` is installed:  
```
solcx.install_solc('0.8.0')
```

---

## 🏃‍♂️ Running the Project
### 1. **Start the Blockchain (Ganache)**
Open a terminal and run:  
```
ganache --port 8545
```
Wait until you see:  
```
RPC Listening on 127.0.0.1:8545
```

### 2. **Run the Streamlit App**
Open another terminal and run:
```
streamlit run app.py
```
This will open the homepage in your browser at **localhost**.

---

## 🚨 Troubleshooting
- If `web3` connection fails, ensure the Ethereum node is running on **port 8545**.  
- If `solcx` installation fails, try updating pip:
```
pip install --upgrade pip
```

---

## 📝 Notes
- The contract ABI and address will be stored in **FreelanceContract.json** after compilation.  
- All contract interactions are handled through **blockchain_interface.py**.  

---
