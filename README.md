<div align="center">

# 🔐 BB84 Quantum Key Distribution Simulator

### A Real-Time, Interactive Simulation of the BB84 Quantum Cryptography Protocol

[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=white)](https://react.dev)
[![Qiskit](https://img.shields.io/badge/Qiskit-Aer-6929C4?style=for-the-badge&logo=ibm&logoColor=white)](https://qiskit.org)
[![Flask](https://img.shields.io/badge/Flask-API-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Three.js](https://img.shields.io/badge/Three.js-3D-000000?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org)
[![Vite](https://img.shields.io/badge/Vite-7-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

**Experience quantum cryptography in action.** This simulator brings the BB84 protocol — the world's first quantum key distribution scheme — to life with real quantum circuit execution, interactive 3D Bloch Sphere visualizations, eavesdropper detection, and end-to-end One-Time Pad encryption.

</div>

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🧬 **Real Quantum Circuits** | Qubits are encoded, transmitted, and measured using **IBM Qiskit Aer** — not classical random numbers |
| 🌐 **3D Bloch Sphere** | Click any qubit to visualize its quantum state on an interactive, auto-rotating **Three.js** Bloch Sphere |
| 🕵️ **Eve Eavesdropper** | Toggle an eavesdropper (Eve) to see how interception disturbs quantum states and raises QBER |
| 📊 **QBER Analysis** | Real-time Quantum Bit Error Rate calculation with visual bar + threshold-based key acceptance/rejection |
| 🔑 **Key Sifting** | Animated basis comparison between Alice & Bob — hover sifted cards to trace matching qubits |
| 🔒 **OTP Encryption** | Encrypt and decrypt messages using the final shared key via One-Time Pad (XOR cipher) |
| 📈 **Comparison Graphs** | Chart.js-powered line graphs comparing Alice & Bob's sifted keys with mismatch markers |
| 🎨 **Premium UI** | Glassmorphism, micro-animations, responsive layout — designed to feel modern and intuitive |

---

## 🧪 How BB84 Works — Execution Flow

The BB84 protocol establishes a shared secret key between two parties (Alice & Bob) using quantum mechanics, making any eavesdropping attempt physically detectable.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        BB84 QUANTUM KEY DISTRIBUTION PROTOCOL                       │
└─────────────────────────────────────────────────────────────────────────────────────┘

  ALICE (Sender)                    QUANTUM CHANNEL                    BOB (Receiver)
  ══════════════                    ═══════════════                    ══════════════

  ┌──────────────────┐                                          ┌──────────────────┐
  │ 1. Generate       │                                          │                  │
  │    Random Bits     │     ╔══════════════════════════╗         │                  │
  │    [0,1,1,0,1...] │     ║  Qubits travel through   ║         │                  │
  │                    │     ║  quantum channel as       ║         │                  │
  │ 2. Choose Random   │────▶║  polarized photons        ║────▶    │ 4. Choose Random │
  │    Bases           │     ║                           ║         │    Bases         │
  │    [+,×,+,×,+...] │     ║  ⚠️ Eve may intercept!    ║         │    [×,×,+,+,×...│]
  │                    │     ╚══════════════════════════╝         │                  │
  │ 3. Encode Qubits   │                                          │ 5. Measure       │
  │    using Qiskit    │                                          │    Qubits        │
  └──────────────────┘                                          └──────────────────┘
          │                                                              │
          │              ┌────────────────────────────┐                  │
          └──────────────│  6. PUBLIC BASIS COMPARISON │──────────────────┘
                         │     (Classical Channel)     │
                         └────────────┬───────────────┘
                                      │
                         ┌────────────▼───────────────┐
                         │  7. KEY SIFTING              │
                         │  Keep only bits where        │
                         │  Alice & Bob used the        │
                         │  SAME basis                  │
                         │                              │
                         │  Same basis  → ✅ Keep bit   │
                         │  Diff basis  → ❌ Discard    │
                         └────────────┬───────────────┘
                                      │
                         ┌────────────▼───────────────┐
                         │  8. QBER ESTIMATION         │
                         │                              │
                         │  Compare a subset of         │
                         │  sifted bits                  │
                         │                              │
                         │  QBER ≤ 15% → ✅ Key Safe   │
                         │  QBER > 15% → 🚨 Eve Found! │
                         └────────────┬───────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                     │
          ┌─────────▼─────────┐              ┌───────────▼──────────┐
          │ ✅ KEY ACCEPTED    │              │ 🚨 KEY REJECTED       │
          │                    │              │                       │
          │ 9. Generate Final  │              │ Transmission Aborted  │
          │    Shared Key      │              │ Eve's interference    │
          │                    │              │ detected!             │
          │ 10. OTP Encryption │              └───────────────────────┘
          │     & Decryption   │
          └────────────────────┘
```

---

## 🖥️ Simulator Walkthrough

### Step 1 → Generate Alice's Qubits
> Alice generates random bits and random bases. Each qubit is encoded into a quantum circuit using **Qiskit Aer** (Hadamard gates for X-basis, identity for Z-basis).

### Step 2 → Bob Measures
> Bob independently picks random measurement bases. Qubits are measured through real quantum circuit simulation — if bases mismatch, results are probabilistic.

### Step 3 → Sift the Key
> Alice and Bob publicly compare **only their bases** (not the bit values). Bits where both used the same basis form the **sifted key**. Hover over any sifted card to instantly see which original qubits matched.

### Step 4 → Calculate QBER
> The Quantum Bit Error Rate reveals if an eavesdropper is present. A QBER above **15%** means the channel was compromised — the key is rejected.

### Step 5 → Encrypt & Decrypt
> If the key passes the QBER check, it's used as a **One-Time Pad** to XOR-encrypt any message. The recipient decrypts using the same shared key.

---

## 🕵️ Eavesdropper (Eve) Simulation

Toggle Eve ON to simulate a **man-in-the-middle quantum attack**:

- Eve intercepts qubits on the quantum channel
- She measures them in **random bases** (she doesn't know Alice's bases)
- She re-encodes and forwards the qubits to Bob
- **Quantum mechanics guarantees** her measurement disturbs the qubits
- This disturbance shows up as an elevated QBER (typically ~25%)
- The simulator flags mismatched sifted bits in **orange** and highlights them across Alice & Bob's panels

> 💡 **This is the power of quantum cryptography** — unlike classical encryption, any eavesdropping attempt is physically detectable. You can't copy a qubit without disturbing it (No-Cloning Theorem).

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| **React 19** | Component-based UI with hooks & state management |
| **Vite 7** | Lightning-fast dev server & optimized production builds |
| **Three.js** | 3D Bloch Sphere visualization with OrbitControls |
| **Chart.js** + react-chartjs-2 | Sifted key comparison graphs with mismatch markers |
| **React Router v7** | Client-side routing (Simulator, Graph, Architecture pages) |
| **Vanilla CSS** | Custom design system with CSS variables, glassmorphism, animations |

### Backend
| Technology | Purpose |
|---|---|
| **Python / Flask** | REST API serving the quantum simulation |
| **IBM Qiskit** | Quantum circuit construction (QuantumCircuit, gates) |
| **Qiskit Aer** | Local quantum simulator backend (AerSimulator) |
| **Flask-CORS** | Cross-origin support for frontend-backend communication |
| **Gunicorn** | Production-grade WSGI server |

### Quantum Concepts Implemented
| Concept | Implementation |
|---|---|
| **Qubit Encoding** | X gate (bit flip) + H gate (basis change) |
| **Measurement** | Projective measurement in Z or X basis |
| **No-Cloning Theorem** | Eve's interception collapses qubit states |
| **Key Sifting** | Basis matching over a classical channel |
| **QBER** | Statistical error rate estimation |
| **One-Time Pad** | XOR-based symmetric encryption using the shared key |

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** ≥ 18
- **Python** ≥ 3.9
- **pip** (Python package manager)

### 1. Clone the Repository
```bash
git clone https://github.com/akashregana77/BB84-QKD-Simulator.git
cd BB84-QKD-Simulator
```

### 2. Start the Backend (Quantum Engine)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python app.py
```
> Backend runs on `http://localhost:5000`

### 3. Start the Frontend
```bash
cd my-react
npm install
npm run dev
```
> Frontend runs on `http://localhost:5173`

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/bb84` | Run full BB84 simulation (accepts `n` bits, `eve` toggle) |
| `POST` | `/encrypt` | Encrypt a message using the shared key (OTP) |
| `POST` | `/decrypt` | Decrypt an encrypted message using the shared key |

---

## 🎯 Interactive Highlights

- 🖱️ **Click any qubit** → Opens a 3D Bloch Sphere showing the quantum state vector
- 🟢 **Hover green sifted card** → Matching qubits in Alice & Bob panels glow green
- 🟠 **Hover orange sifted card** → Eve-tampered qubits highlighted in orange
- 📉 **QBER bar** → Live progress bar with threshold indicator
- ⚡ **Quantum channel** → Animated photon particles during transmission
- 🔴 **Eve warning** → Pulsing alert when eavesdropper is active

---

## 📚 References

- Bennett, C.H. & Brassard, G. (1984). *"Quantum Cryptography: Public Key Distribution and Coin Tossing"*
- [IBM Qiskit Documentation](https://docs.quantum.ibm.com/)
- [BB84 Protocol — Wikipedia](https://en.wikipedia.org/wiki/BB84)

---

<div align="center">

**Built with ⚛️ quantum circuits and ❤️ for cryptography**

</div>
