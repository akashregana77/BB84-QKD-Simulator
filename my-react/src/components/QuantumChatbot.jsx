import React, { useState, useRef, useEffect } from "react";
import { sendQuantumChat } from "../services/api";
import "./QuantumChatbot.css";

const INITIAL_SUGGESTIONS = [
  "How does BB84 detect eavesdropping?",
  "What is basis reconciliation (sifting)?",
  "Why does the No-Cloning theorem matter in QKD?",
  "What does a QBER higher than 15% indicate?",
];

export default function QuantumChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I am your **Quantum AI Assistant**. Ask me anything about Quantum Computing, Quantum Key Distribution (QKD), BB84 protocol stages, quantum states, or photon polarization.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen, messages]);

  const handleSend = async (textToSend) => {
    const text = (textToSend || input).trim();
    if (!text || loading) return;

    const userMessage = { role: "user", content: text };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput("");
    setLoading(true);

    try {
      // Build history for backend API (excluding latest message which is sent as message param)
      const history = updatedMessages.slice(0, -1).map((m) => ({
        role: m.role === "assistant" ? "model" : "user",
        content: m.content,
      }));

      const res = await sendQuantumChat(text, history);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.reply || "No response received." },
      ]);
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "⚠️ Failed to get an answer from the Quantum AI backend. Please verify that the Flask server is running on the configured URL.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Helper to render basic markdown formatting: bold, code, bullet lists, newlines
  const renderFormattedText = (text) => {
    if (!text) return "";
    const lines = text.split("\n");
    return lines.map((line, lineIdx) => {
      // Check for bullet line
      const isBullet = line.trim().startsWith("- ") || line.trim().startsWith("* ");
      const cleanLine = isBullet ? line.trim().replace(/^[-*]\s+/, "") : line;

      // Parse bold (**bold**) and inline code (`code`)
      const parts = [];
      let lastIndex = 0;
      const regex = /(\*\*[^*]+\*\*|`[^`]+`)/g;
      let match;

      while ((match = regex.exec(cleanLine)) !== null) {
        if (match.index > lastIndex) {
          parts.push(cleanLine.substring(lastIndex, match.index));
        }
        const token = match[0];
        if (token.startsWith("**") && token.endsWith("**")) {
          parts.push(
            <strong key={`${lineIdx}-${match.index}`}>
              {token.slice(2, -2)}
            </strong>
          );
        } else if (token.startsWith("`") && token.endsWith("`")) {
          parts.push(
            <code key={`${lineIdx}-${match.index}`}>{token.slice(1, -1)}</code>
          );
        }
        lastIndex = regex.lastIndex;
      }
      if (lastIndex < cleanLine.length) {
        parts.push(cleanLine.substring(lastIndex));
      }

      if (isBullet) {
        return (
          <li key={lineIdx} style={{ marginLeft: "14px", marginBottom: "4px" }}>
            {parts}
          </li>
        );
      }
      return (
        <p key={lineIdx} style={{ margin: "3px 0" }}>
          {parts}
        </p>
      );
    });
  };

  return (
    <>
      {/* Floating Launcher Button */}
      <button
        className="quantum-chat-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        title="Open Quantum AI Chatbot"
        aria-label="Toggle Quantum AI Assistant"
      >
        <span className="chat-pulse-dot" />
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <span>Quantum AI</span>
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="quantum-chat-window">
          {/* Header */}
          <div className="quantum-chat-header">
            <div className="chat-header-title">
              <div className="chat-avatar">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <circle cx="12" cy="12" r="2.5" />
                  <ellipse cx="12" cy="12" rx="9" ry="3.5" />
                  <ellipse
                    cx="12"
                    cy="12"
                    rx="9"
                    ry="3.5"
                    transform="rotate(60 12 12)"
                  />
                  <ellipse
                    cx="12"
                    cy="12"
                    rx="9"
                    ry="3.5"
                    transform="rotate(120 12 12)"
                  />
                </svg>
              </div>
              <div>
                <h4 className="chat-title-text">Quantum AI Assistant</h4>
                <p className="chat-subtitle-text">BB84 & Quantum Cryptography</p>
              </div>
            </div>
            <button
              className="chat-close-btn"
              onClick={() => setIsOpen(false)}
              aria-label="Close Chat"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {/* Body */}
          <div className="quantum-chat-body">
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-msg ${msg.role}`}>
                <div className="chat-bubble">
                  {renderFormattedText(msg.content)}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-loading">
                <span />
                <span />
                <span />
              </div>
            )}

            {messages.length === 1 && (
              <div className="chat-suggestions">
                <p style={{ fontSize: "11px", color: "#94a3b8", margin: "4px 0" }}>
                  Suggested questions:
                </p>
                {INITIAL_SUGGESTIONS.map((suggestion, sIdx) => (
                  <button
                    key={sIdx}
                    className="suggestion-chip"
                    onClick={() => handleSend(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Footer Input */}
          <div className="quantum-chat-footer">
            <form
              className="chat-input-form"
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
            >
              <input
                ref={inputRef}
                type="text"
                className="chat-input"
                placeholder="Ask about BB84, qubits, QBER..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
              />
              <button
                type="submit"
                className="chat-send-btn"
                disabled={loading || !input.trim()}
                title="Send message"
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
