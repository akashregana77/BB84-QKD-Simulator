import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
import random
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# Load environment variables
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ----------- GEMINI AI CONFIGURATION -----------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

GEMINI_PRIMARY_MODEL = "gemini-2.5-flash"
GEMINI_FALLBACK_MODELS = ["gemini-2.5-flash-lite", "gemini-flash-latest"]

def get_gemini_model(system_instruction=None):
    if not GOOGLE_API_KEY:
        return None
    for model_name in [GEMINI_PRIMARY_MODEL] + GEMINI_FALLBACK_MODELS:
        try:
            if system_instruction:
                return genai.GenerativeModel(model_name, system_instruction=system_instruction)
            return genai.GenerativeModel(model_name)
        except Exception:
            continue
    return None

# ----------- BB84 FUNCTIONS -----------
def generate_bases(n):
    return [random.choice(['Z', 'X']) for _ in range(n)]

def generate_bits(n):
    return [random.randint(0, 1) for _ in range(n)]

def encode_qubits(bits, bases):
    circuits = []
    for bit, base in zip(bits, bases):
        qc = QuantumCircuit(1, 1)
        if bit == 1:
            qc.x(0)
        if base == 'X':
            qc.h(0)
        circuits.append(qc)
    return circuits

def measure_qubits(circuits, bases):
    backend = AerSimulator()
    results = []
    for qc, base in zip(circuits, bases):
        qc_copy = qc.copy()
        if base == 'X':
            qc_copy.h(0)
        qc_copy.measure(0, 0)
        compiled = transpile(qc_copy, backend)
        job = backend.run(compiled, shots=1)
        counts = job.result().get_counts()
        bit = int(list(counts.keys())[0])
        results.append(bit)
    return results

def sift_key(a_bits, a_bases, b_bits, b_bases):
    sifted_a, sifted_b = [], []
    for a_bit, a_base, b_bit, b_base in zip(a_bits, a_bases, b_bits, b_bases):
        if a_base == b_base:
            sifted_a.append(a_bit)
            sifted_b.append(b_bit)
    return sifted_a, sifted_b

def qber(a_key, b_key):
    if len(a_key) == 0:
        return 0
    errors = sum(ai != bi for ai, bi in zip(a_key, b_key))
    return errors / len(a_key)

# ----------- ENCRYPTION HELPERS (OTP) -----------
def str_to_bits(s):
    bits = []
    for c in s:
        bits.extend([int(b) for b in format(ord(c), '08b')])
    return bits

def bits_to_str(bits):
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]
        if len(byte) < 8:
            break
        chars.append(chr(int("".join(str(b) for b in byte), 2)))
    return "".join(chars)

def xor_encrypt_decrypt(message_bits, key_bits):
    return [mb ^ kb for mb, kb in zip(message_bits, key_bits)]

# ----------- ROUTES -----------

@app.route("/bb84", methods=["POST"])
def run_bb84():
    data = request.get_json()
    with_eve = data.get("eve", False)
    n = data.get("n", 100)

    alice_bits = generate_bits(n)
    alice_bases = generate_bases(n)
    qubits = encode_qubits(alice_bits, alice_bases)

    eve_results, eve_bases = None, None
    if with_eve:
        eve_bases = generate_bases(n)
        eve_results = measure_qubits(qubits, eve_bases)
        qubits = encode_qubits(eve_results, eve_bases)

    bob_bases = generate_bases(n)
    bob_results = measure_qubits(qubits, bob_bases)
    alice_key, bob_key = sift_key(alice_bits, alice_bases, bob_results, bob_bases)
    current_qber = qber(alice_key, bob_key)
    aborted = with_eve and current_qber > 0.15

    return jsonify({
        "alice_bits": alice_bits,
        "alice_bases": alice_bases,
        "bob_bases": bob_bases,
        "bob_results": bob_results,
        "alice_key": alice_key,
        "bob_key": bob_key,
        "qber": current_qber,
        "aborted": aborted,
        "eve_results": eve_results,
        "eve_bases": eve_bases
    })

@app.route("/encrypt", methods=["POST"])
def encrypt_message():
    data = request.get_json()
    message = data.get("message", "")
    key_bits = data.get("key", [])

    if not key_bits:
        return jsonify({"error": "No key provided"}), 400

    message_bits = str_to_bits(message)
    if len(key_bits) < len(message_bits):
        message_bits = message_bits[:len(key_bits)]

    encrypted_bits = xor_encrypt_decrypt(message_bits, key_bits[:len(message_bits)])
    encrypted_message = bits_to_str(encrypted_bits)

    return jsonify({
        "encrypted_bits": encrypted_bits,
        "encrypted_message": encrypted_message
    })

@app.route("/decrypt", methods=["POST"])
def decrypt_message():
    data = request.get_json()
    encrypted_bits = data.get("encrypted_bits", [])
    key_bits = data.get("key", [])

    if not key_bits:
        return jsonify({"error": "No key provided"}), 400

    decrypted_bits = xor_encrypt_decrypt(encrypted_bits, key_bits[:len(encrypted_bits)])
    decrypted_message = bits_to_str(decrypted_bits)

    return jsonify({
        "decrypted_bits": decrypted_bits,
        "decrypted_message": decrypted_message
    })

# ----------- AI QUANTUM ASSISTANT & ANALYZER ROUTES -----------

@app.route("/api/chat", methods=["POST"])
def quantum_chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    system_instruction = (
        "You are an expert Quantum Computing and Quantum Cryptography AI assistant for the BB84 QKD Simulator. "
        "Your role is to provide clear, technically accurate, intuitive, and engaging explanations about Quantum Computing, "
        "Quantum Key Distribution (QKD), BB84 protocol stages, quantum states (|0>, |1>, |+>, |->), photon polarization, "
        "the No-Cloning theorem, Heisenberg's uncertainty principle, basis reconciliation, quantum bit error rate (QBER), "
        "and One-Time Pad encryption. Format your response cleanly using Markdown."
    )

    try:
        model = get_gemini_model(system_instruction=system_instruction)
        if not model:
            return jsonify({
                "reply": "AI service is currently unavailable. Please verify the Gemini API key configuration."
            }), 503

        # Convert history format for google.generativeai
        formatted_history = []
        for item in history:
            role = "model" if item.get("role") in ["model", "assistant"] else "user"
            content = item.get("content") or (item.get("parts", [""])[0] if item.get("parts") else "")
            if content:
                formatted_history.append({"role": role, "parts": [content]})

        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(user_message)
        return jsonify({"reply": response.text.strip()})
    except Exception as e:
        print(f"Error in quantum_chat: {e}")
        return jsonify({
            "reply": f"I encountered an error processing your quantum query: {str(e)}"
        }), 500


# Approved target identifiers and their corresponding stable DOM selectors
VALID_TARGET_SELECTORS = {
    "alice": "[data-qkd-stage='alice']",
    "bob": "[data-qkd-stage='bob']",
    "channel": "[data-qkd-stage='channel']",
    "eve": "[data-qkd-stage='eve']",
    "sifting": "[data-qkd-stage='sifting']",
    "qber": "[data-qkd-stage='qber']",
    "final_key": "[data-qkd-stage='final_key']",
    "encryption": "[data-qkd-stage='encryption']",
    "controls": "[data-qkd-stage='controls']",
}

TARGET_ALIASES = {
    "alice": "alice",
    "alice-panel": "alice",
    "alice_panel": "alice",
    "bob": "bob",
    "bob-panel": "bob",
    "bob_panel": "bob",
    "channel": "channel",
    "quantum-channel": "channel",
    "quantum_channel": "channel",
    "eve": "eve",
    "eve-toggle": "eve",
    "eve_toggle": "eve",
    "sifting": "sifting",
    "sifted-bits": "sifting",
    "sifted_bits": "sifting",
    "basis_reconciliation": "sifting",
    "qber": "qber",
    "qber-section": "qber",
    "qber_section": "qber",
    "final_key": "final_key",
    "final-key": "final_key",
    "key": "final_key",
    "encryption": "encryption",
    "encryption-section": "encryption",
    "encryption_section": "encryption",
    "controls": "controls",
}

@app.route("/api/analyze-state", methods=["POST"])
def analyze_state():
    data = request.get_json() or {}
    stage = data.get("stage", "idle")
    num_bits = data.get("numBits", 20)
    eve_enabled = data.get("eveEnabled", False)
    alice_bits = data.get("aliceBits", [])
    alice_bases = data.get("aliceBases", [])
    bob_bits = data.get("bobBits", [])
    bob_bases = data.get("bobBases", [])
    sifted_bits = data.get("siftedBits", [])
    final_key = data.get("finalKey", [])
    qber_val = data.get("qber")
    key_accepted = data.get("keyAccepted")
    msg = data.get("message", "")
    encrypted_msg = data.get("encryptedMessage", "")
    decrypted_msg = data.get("decryptedMessage", "")
    is_generating = data.get("isGenerating", False)

    # Calculate mismatch count if sifted bits available
    mismatch_count = 0
    if sifted_bits:
        mismatch_count = sum(1 for b in sifted_bits if isinstance(b, dict) and b.get("alice") != b.get("bob"))

    state_summary = {
        "current_stage": stage,
        "is_generating": is_generating,
        "num_bits": num_bits,
        "eve_intercepting": eve_enabled,
        "alice_bits_generated": len(alice_bits),
        "alice_sample_bits": alice_bits[:8] if alice_bits else [],
        "alice_sample_bases": alice_bases[:8] if alice_bases else [],
        "bob_bits_measured": len(bob_bits),
        "bob_sample_bits": bob_bits[:8] if bob_bits else [],
        "bob_sample_bases": bob_bases[:8] if bob_bases else [],
        "sifted_bits_count": len(sifted_bits),
        "sifted_mismatches": mismatch_count,
        "qber": f"{qber_val:.2f}%" if qber_val is not None else None,
        "key_accepted": key_accepted,
        "final_key_length": len(final_key),
        "has_plaintext_message": bool(msg),
        "has_encrypted_message": bool(encrypted_msg),
        "has_decrypted_message": bool(decrypted_msg),
    }

    system_instruction = (
        "You are an interactive Quantum Key Distribution (BB84) process analyzer. "
        "Analyze the exact live simulation state provided. "
        "Return a strictly valid JSON object conforming to this schema without any backticks, markdown markers, or surrounding text:\n"
        "{\n"
        '  "status": "success",\n'
        '  "current_stage": "<e.g. idle | alice_preparation | bob_measurement | basis_reconciliation | qber_evaluation | final_key | message_encryption | aborted>",\n'
        '  "summary": "<2-3 clear sentences summarizing what is occurring in this actual simulation state>",\n'
        '  "explanations": [\n'
        '    {\n'
        '      "target": "<one of: alice | bob | channel | eve | sifting | qber | final_key | encryption | controls>",\n'
        '      "title": "<short descriptive title for this UI section>",\n'
        '      "description": "<technical explanation referencing actual data/state for this region>",\n'
        '      "selector": "<will be mapped from target>"\n'
        '    }\n'
        '  ],\n'
        '  "next_stage": "<short description of the logical next operation in BB84>",\n'
        '  "metrics_insight": "<commentary on current numbers: bit counts, match rate, or QBER>",\n'
        '  "suggested_questions": ["<relevant question 1>", "<relevant question 2>", "<relevant question 3>"]\n'
        "}\n"
        "Allowed targets: alice, bob, channel, eve, sifting, qber, final_key, encryption, controls. Do not invent any other target."
    )

    prompt = (
        f"Analyze this live BB84 simulation state:\n{json.dumps(state_summary, indent=2)}\n\n"
        "Output ONLY the JSON object."
    )

    try:
        model = get_gemini_model(system_instruction=system_instruction)
        if not model:
            raise Exception("Gemini model not initialized")

        response = model.generate_content(prompt)
        raw_text = response.text.strip()

        # Clean potential markdown wrapping
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()

        data_json = json.loads(raw_text)

        # Validate and sanitize response structure
        data_json["status"] = "success"
        if "current_stage" not in data_json:
            data_json["current_stage"] = stage
        if "summary" not in data_json:
            data_json["summary"] = data_json.get("overview", "QKD process analyzed.")

        raw_explanations = data_json.get("explanations") or data_json.get("steps") or []
        sanitized_explanations = []

        for exp in raw_explanations:
            raw_target = exp.get("target") or exp.get("targetId") or "controls"
            clean_target = TARGET_ALIASES.get(str(raw_target).lower().strip(), "controls")
            sanitized_explanations.append({
                "target": clean_target,
                "title": exp.get("title", f"Stage: {clean_target.title()}"),
                "description": exp.get("description") or exp.get("content", ""),
                "selector": VALID_TARGET_SELECTORS.get(clean_target, "[data-qkd-stage='controls']"),
            })

        if not sanitized_explanations:
            sanitized_explanations = generate_state_fallback(state_summary)["explanations"]

        data_json["explanations"] = sanitized_explanations
        if "next_stage" not in data_json:
            data_json["next_stage"] = "Continue simulation workflow"
        if "metrics_insight" not in data_json:
            data_json["metrics_insight"] = data_json.get("metricsInsight", "")
        if "suggested_questions" not in data_json:
            data_json["suggested_questions"] = data_json.get("suggestedQuestions", [
                "Why is this stage happening?",
                "What does this measurement mean?",
                "What happens next?"
            ])

        return jsonify(data_json)
    except Exception as e:
        print(f"Error in analyze_state or fallback triggered: {e}")
        fallback = generate_state_fallback(state_summary)
        return jsonify(fallback)


def generate_state_fallback(state):
    stage = state.get("current_stage", "idle")
    eve = state.get("eve_intercepting", False)
    qber = state.get("qber")
    sifted_count = state.get("sifted_bits_count", 0)
    alice_count = state.get("alice_bits_generated", 0)
    bob_count = state.get("bob_bits_measured", 0)
    key_accepted = state.get("key_accepted")
    final_len = state.get("final_key_length", 0)

    if stage in ["alice_preparation", "alice_generated"]:
        return {
            "status": "success",
            "current_stage": "alice_preparation",
            "summary": f"Alice has generated {alice_count} random bits and encoded each bit into a quantum state using randomly selected rectilinear (+) and diagonal (×) bases.",
            "explanations": [
                {
                    "target": "alice",
                    "title": "Alice's State Preparation",
                    "description": f"Alice prepared {alice_count} qubits (|0⟩, |1⟩ in Z-basis and |+⟩, |−⟩ in X-basis). Each qubit represents one classical bit encoded into photon polarization.",
                    "selector": VALID_TARGET_SELECTORS["alice"]
                },
                {
                    "target": "channel",
                    "title": "Quantum Optical Channel",
                    "description": f"The prepared photons are queued for transmission along the quantum optical channel. {'Eve is currently enabled to intercept!' if eve else 'No eavesdropping is detected.'}",
                    "selector": VALID_TARGET_SELECTORS["channel"]
                }
            ],
            "next_stage": "Bob's Measurement",
            "metrics_insight": f"{alice_count} quantum states prepared. Next, Bob will measure them using his randomly chosen bases.",
            "suggested_questions": [
                "Why must Alice use two different non-orthogonal bases?",
                "What does clicking on a qubit to view the Bloch sphere represent?",
                "What happens when photons enter the quantum channel?"
            ]
        }
    elif stage in ["bob_measurement", "bob_measured"]:
        return {
            "status": "success",
            "current_stage": "bob_measurement",
            "summary": f"Bob received the transmitted qubits and independently measured each in a randomly selected basis (+ or ×).{' Eve intercepted the transmission.' if eve else ''}",
            "explanations": [
                {
                    "target": "bob",
                    "title": "Bob's Independent Measurement",
                    "description": f"Bob measured {bob_count} qubits. By quantum mechanics, measuring a quantum state projects it into the chosen basis, collapsing any superpositions.",
                    "selector": VALID_TARGET_SELECTORS["bob"]
                },
                {
                    "target": "channel",
                    "title": "Quantum Channel Transmission",
                    "description": "Photons have completed transmission across the quantum channel. Any measurement by Eve along the way caused state disturbance.",
                    "selector": VALID_TARGET_SELECTORS["channel"]
                }
            ],
            "next_stage": "Basis Reconciliation (Key Sifting)",
            "metrics_insight": f"Bob measured {bob_count} bits. The next step is comparing bases over the classical public channel to sift matching bases.",
            "suggested_questions": [
                "Why can't Bob measure in both bases at the same time?",
                "What happens when Bob's basis differs from Alice's basis?",
                "Did Eve alter the states during transmission?"
            ]
        }
    elif stage in ["basis_reconciliation", "sifted"]:
        return {
            "status": "success",
            "current_stage": "basis_reconciliation",
            "summary": f"Alice and Bob publicly compared their measurement bases. Discarded mismatched bases and retained {sifted_count} matching bases to form the raw sifted key.",
            "explanations": [
                {
                    "target": "sifting",
                    "title": "Sifted Key Generation",
                    "description": f"From the initial transmission, Alice and Bob agreed on bases for {sifted_count} bits (~50% statistical match rate). These bits form the shared sifted key.",
                    "selector": VALID_TARGET_SELECTORS["sifting"]
                },
                {
                    "target": "alice",
                    "title": "Alice's Matching Bases",
                    "description": "Alice marks bits where her chosen basis agreed with Bob's. Mismatched bases are discarded.",
                    "selector": VALID_TARGET_SELECTORS["alice"]
                },
                {
                    "target": "bob",
                    "title": "Bob's Matching Bases",
                    "description": "Bob retains only bits where his detector basis coincided with Alice's preparation basis.",
                    "selector": VALID_TARGET_SELECTORS["bob"]
                }
            ],
            "next_stage": "Quantum Bit Error Rate (QBER) Calculation",
            "metrics_insight": f"{sifted_count} sifted bits retained out of {state.get('num_bits', 20)} (~50% efficiency). QBER check is needed next to verify security.",
            "suggested_questions": [
                "Why were about half of the bits discarded during sifting?",
                "Does revealing bases publicly over a classical channel compromise security?",
                "Why must we calculate QBER next?"
            ]
        }
    elif stage in ["qber_evaluation", "qber_calculated", "aborted"]:
        is_aborted = (key_accepted is False) or (eve and qber and float(str(qber).replace('%','')) > 15.0)
        return {
            "status": "success",
            "current_stage": "aborted" if is_aborted else "qber_evaluation",
            "summary": f"Alice and Bob tested a sample of their sifted key for transmission errors. Measured QBER is {qber or 'calculated'}. Security threshold is ≤ 15%. Transmission is {'ABORTED due to eavesdropping detection' if is_aborted else 'ACCEPTED (channel is secure)'}.",
            "explanations": [
                {
                    "target": "qber",
                    "title": "QBER Security Evaluation",
                    "description": f"Observed QBER is {qber}. {'Because QBER exceeds 15%, Alice and Bob know an eavesdropper was active and abort the protocol.' if is_aborted else 'Since QBER ≤ 15%, the channel is within tolerable noise limits and secure.'}",
                    "selector": VALID_TARGET_SELECTORS["qber"]
                },
                {
                    "target": "eve",
                    "title": "Eavesdropping Impact",
                    "description": f"Eve toggle is {'ON (Eavesdropping simulated)' if eve else 'OFF'}. Any intercept-resend attack induces ~25% theoretical error due to the No-Cloning theorem.",
                    "selector": VALID_TARGET_SELECTORS["eve"]
                }
            ],
            "next_stage": "Abort & Restart" if is_aborted else "Final Shared Key Generation",
            "metrics_insight": f"QBER: {qber}. Key status: {'REJECTED (Eavesdropping Detected)' if is_aborted else 'ACCEPTED'}.",
            "suggested_questions": [
                "Why does eavesdropping inevitably introduce errors in BB84?",
                "What is the mathematical significance of the 15% QBER threshold?",
                "Can Alice and Bob extract a secure key if QBER is too high?"
            ]
        }
    elif stage in ["final_key", "message_encryption", "encrypted"]:
        return {
            "status": "success",
            "current_stage": "final_key",
            "summary": f"A secure shared key of {final_len or sifted_count} bits has been distilled. Alice and Bob can now use this key for One-Time Pad encryption.",
            "explanations": [
                {
                    "target": "final_key",
                    "title": "Distilled Shared Secret Key",
                    "description": f"This {final_len or sifted_count}-bit secret key is identical for Alice and Bob and mathematically guaranteed to be secret from any third party.",
                    "selector": VALID_TARGET_SELECTORS["final_key"]
                },
                {
                    "target": "encryption",
                    "title": "One-Time Pad Encryption",
                    "description": "The shared key can now encrypt plaintext messages via bitwise XOR, providing information-theoretic (Shannon) security.",
                    "selector": VALID_TARGET_SELECTORS["encryption"]
                }
            ],
            "next_stage": "Secure Classical Communication (One-Time Pad)",
            "metrics_insight": f"Final key length: {final_len or sifted_count} bits. Unbreakable One-Time Pad encryption is active.",
            "suggested_questions": [
                "Why is One-Time Pad encryption unbreakable when paired with QKD?",
                "Why must each secret key bit be used only once?",
                "What happens if the message is longer than the shared key?"
            ]
        }
    else:
        return {
            "status": "success",
            "current_stage": "idle",
            "summary": f"The QKD simulator is initialized and idle. Configure the number of bits ({state.get('num_bits', 20)}) and decide whether to enable Eve before generating qubits.",
            "explanations": [
                {
                    "target": "controls",
                    "title": "Protocol Configuration",
                    "description": f"Set the number of bits (currently {state.get('num_bits', 20)}) and click 'Generate Alice' to prepare the quantum state stream.",
                    "selector": VALID_TARGET_SELECTORS["controls"]
                },
                {
                    "target": "eve",
                    "title": "Eve Interception Toggle",
                    "description": f"Eve is currently {'ENABLED (will intercept channel)' if eve else 'DISABLED (secure channel)'}. Toggle Eve to test eavesdropping detection.",
                    "selector": VALID_TARGET_SELECTORS["eve"]
                }
            ],
            "next_stage": "Alice State Generation",
            "metrics_insight": f"Ready to generate {state.get('num_bits', 20)} qubits. Eve is {'ON' if eve else 'OFF'}.",
            "suggested_questions": [
                "What is the BB84 Quantum Key Distribution protocol?",
                "How does quantum mechanics guarantee security over classical cryptography?",
                "What happens when Eve is toggled ON?"
            ]
        }


@app.route("/api/analyze-question", methods=["POST"])
def analyze_question():
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    sim_state = data.get("simulationState", {})
    prev_analysis = data.get("previousAnalysis", {})
    history = data.get("history", [])

    if not question:
        return jsonify({"error": "Question is required"}), 400

    system_instruction = (
        "You are an expert Quantum Cryptography AI analyzing an active BB84 simulation for the user. "
        "Answer the user's specific question directly, accurately, and concisely using the provided simulation state, "
        "stage details, and previous analysis. Connect your answer to quantum mechanical principles (superposition, measurement collapse, "
        "no-cloning theorem, bases, QBER, etc.) as they apply to the user's current numbers and execution stage. "
        "Format with clear Markdown."
    )

    summary_text = prev_analysis.get("summary") or prev_analysis.get("overview", "")
    current_stage_text = prev_analysis.get("current_stage") or prev_analysis.get("stageTitle", "")
    explanations_text = ""
    for exp in prev_analysis.get("explanations", []):
        explanations_text += f"- {exp.get('title')}: {exp.get('description')}\n"

    context_prompt = (
        f"Current Simulation State:\n{json.dumps(sim_state, indent=2)}\n\n"
        f"Current Stage: {current_stage_text}\n"
        f"Current Analysis Summary: {summary_text}\n"
        f"Section Explanations:\n{explanations_text}\n"
        f"User Question: {question}"
    )

    try:
        model = get_gemini_model(system_instruction=system_instruction)
        if not model:
            return jsonify({
                "answer": "AI service is currently unavailable. Please verify backend environment configuration."
            }), 503

        # Form formatted history
        formatted_history = []
        for item in history:
            role = "model" if item.get("role") in ["model", "assistant"] else "user"
            content = item.get("content") or ""
            if content:
                formatted_history.append({"role": role, "parts": [content]})

        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(context_prompt)
        return jsonify({"answer": response.text.strip()})
    except Exception as e:
        print(f"Error in analyze_question or rate limit reached: {e}")
        # Context-aware fallback answer based on current simulation state
        q_lower = question.lower()
        stage = sim_state.get("stage", "idle")
        qber = sim_state.get("qber")
        eve = sim_state.get("eveEnabled", False)

        if "qber" in q_lower or "error" in q_lower:
            fallback_answer = (
                f"**Quantum Bit Error Rate (QBER):** Currently, the measured QBER is {qber or 'being evaluated'}. "
                "In BB84, if an eavesdropper (Eve) intercepts qubits, measuring in a random basis introduces an expected error of 25%. "
                "The protocol defines a security threshold of 15% (accounting for physical optical channel noise). "
                f"{'Because QBER > 15%, the channel is considered compromised and transmission must be aborted.' if eve and qber and float(str(qber).replace('%','')) > 15 else 'When QBER ≤ 15%, errors can be corrected and privacy amplification extracts a secure key.'}"
            )
        elif "discard" in q_lower or "sift" in q_lower or "basis" in q_lower:
            fallback_answer = (
                "**Basis Reconciliation (Key Sifting):** Alice and Bob choose random bases (+ or ×) independently for each qubit. "
                "Since each has a 50% chance of picking either basis, their choices match approximately half the time. "
                "When their bases match, Bob's measurement is deterministic and matches Alice's bit (without noise). "
                "Bits where their bases differed are completely random and must be discarded over the classical public channel."
            )
        elif "eve" in q_lower or "eavesdrop" in q_lower or "intercept" in q_lower:
            fallback_answer = (
                "**Eavesdropping & Quantum Mechanics:** Due to the **No-Cloning Theorem**, Eve cannot duplicate unknown quantum states. "
                "To intercept, she must measure the photon in a basis she guesses. If her basis guess is wrong, the quantum state collapses into her basis. "
                "When Bob measures this disturbed photon, he has a 50% chance of getting an erroneous bit even if his basis matches Alice's, "
                "resulting in an unavoidable ~25% error rate that Alice and Bob detect during QBER analysis."
            )
        elif "next" in q_lower or "happen next" in q_lower:
            next_stage_text = prev_analysis.get("next_stage", "proceeding to the next step")
            fallback_answer = (
                f"**Next Stage:** The next operation in the simulation is **{next_stage_text}**. "
                f"Current stage is `{stage}`. Follow the controls in the simulator interface to execute the next step."
            )
        elif "one-time pad" in q_lower or "otp" in q_lower or "encrypt" in q_lower:
            fallback_answer = (
                "**One-Time Pad (OTP) Encryption:** OTP provides mathematical, information-theoretic security (proven by Claude Shannon) "
                "as long as the key is truly random, at least as long as the message, used only once, and kept completely secret. "
                "QKD uniquely solves the key distribution problem to make One-Time Pad practically unbreakable."
            )
        else:
            fallback_answer = (
                f"**Current State Analysis:** In the current `{stage}` stage, Alice and Bob are executing the BB84 protocol with {sim_state.get('numBits', 20)} bits. "
                f"{prev_analysis.get('summary', '')} "
                "Any measurement along the quantum channel projects the photon polarization state, ensuring security through physical law."
            )
        return jsonify({"answer": fallback_answer})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
