import joblib
import os
import argparse
import re
from pathlib import Path
from pwn import remote

# Import the solver registry and lookup function from our new module
from src.core.solvers import get_solver

# --- AGENT CONFIGURATION ---

# Get the project root directory
PROJECT_ROOT = Path(os.getcwd())
MODELS_PATH = PROJECT_ROOT / 'models'

# --- MAIN AGENT LOGIC ---

def run_agent(host: str, port: int):
    """
    Orchestrates the end-to-end process of solving a challenge by connecting to a live server.
    """
    print("--- [STARTING AI AGENT] ---")
    conn = None
    
    try:
        # 1. Establish Connection and get Challenge Description
        print(f"\n[1. CONNECTING to {host}:{port}...")
        conn = remote(host, port)
        # Receive the initial banner/description from the server.
        # We receive until a common prompt character or timeout.
        initial_text = conn.recvuntil(b'> ', timeout=5).decode()
        print(f"[+] Received initial text:\n---\n{initial_text}\n---")
        challenge_description = initial_text

        # 2. Load the trained model ("The Brain")
        print("\n[2. LOADING MODELS]")
        try:
            classifier_pipeline = joblib.load(MODELS_PATH / 'challenge_classifier.joblib')
            label_binarizer = joblib.load(MODELS_PATH / 'label_binarizer.joblib')
            print("[+] Models loaded successfully.")
        except FileNotFoundError:
            print("[X] ERROR: Model files not found. Please run train_classifier.py first.")
            return

        # 3. Predict the crypto technique from the description
        print("\n[3. ANALYZING CHALLENGE]")
        predicted_binarized = classifier_pipeline.predict([challenge_description])
        predicted_labels = label_binarizer.inverse_transform(predicted_binarized)
        
        if not predicted_labels or not predicted_labels[0]:
            print("[X] ERROR: The classifier could not identify a crypto technique.")
            # Fallback: attempt to read more from the server if possible
            conn.interactive()
            return
            
        labels = list(predicted_labels[0])
        print(f"[+] Classifier prediction: {labels}")

        # 4. Find and Execute the appropriate solver ("The Hands")
        print("\n[4. SELECTING & EXECUTING SOLVER]")
        solver_function = get_solver(labels)

        if not solver_function:
            print("[X] ERROR: No solver found for the predicted techniques.")
            print("Switching to interactive mode.")
            conn.interactive()
            return
        
        # Pass the existing connection to the solver
        solver_success = solver_function(conn)

        # 5. Report the result
        print("\n[5. FINAL RESULT]")
        if solver_success:
            print("[*] Solver reported success. Searching for flag...")
            # After solver runs, get the rest of the output to find the flag
            final_output = conn.recvall(timeout=2).decode()
            print(f"[i] Final server output:\n---\n{final_output}\n---")
            flag_match = re.search(r'(flag|ctf|sekai)\{[^}]+\}', final_output, re.IGNORECASE)
            if flag_match:
                flag = flag_match.group(1)
                print(f"[*] AGENT MISSION SUCCESSFUL. Flag: {flag}")
            else:
                print("[*] AGENT MISSION COMPLETED, but no flag found in final output.")
        else:
            print("[*] AGENT MISSION FAILED. Solver reported an error.")
            
        print("--- [AI AGENT FINISHED] ---")

    except Exception as e:
        print(f"\n[X] A critical error occurred in the agent: {e}")
    finally:
        if conn:
            conn.close()
            print("\n[*] Connection closed.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Autonomous Crypto CTF Solving Agent')
    parser.add_argument('host', type=str, help='The hostname or IP address of the challenge server.')
    parser.add_argument('port', type=int, help='The port number of the challenge server.')
    
    args = parser.parse_args()
    
    run_agent(args.host, args.port)