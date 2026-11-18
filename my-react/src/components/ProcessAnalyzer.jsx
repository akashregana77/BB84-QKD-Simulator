import React, { useState, useEffect, useRef, useCallback } from "react";
import { analyzeSimulationState, askAnalysisQuestion } from "../services/api";
import "./ProcessAnalyzer.css";

// Approved frontend mapping between valid stage identifiers and actual DOM elements
const APPROVED_STAGE_SELECTORS = {
  alice: "[data-qkd-stage='alice'], .alice-panel",
  bob: "[data-qkd-stage='bob'], .bob-panel",
  channel: "[data-qkd-stage='channel'], .quantum-channel",
  eve: "[data-qkd-stage='eve'], .eve-toggle",
  sifting: "[data-qkd-stage='sifting'], [data-qkd-stage='key-panel'], .key-panel",
  qber: "[data-qkd-stage='qber'], [data-qkd-stage='key-panel'], .key-panel",
  final_key: "[data-qkd-stage='final_key'], [data-qkd-stage='key-panel'], .key-panel",
  encryption: "[data-qkd-stage='encryption'], [data-qkd-stage='controls'], .encryption-section, .controls",
  controls: "[data-qkd-stage='controls'], .controls",
};

export default function ProcessAnalyzer({
  aliceBits = [],
  aliceBases = [],
  bobBits = [],
  bobBases = [],
  eveEnabled = false,
  eveGuesses = [],
  eveBases = [],
  siftedBits = [],
  qber = null,
  finalKey = [],
  keyAccepted = null,
  numBits = 20,
  message = "",
  encryptedMessage = "",
  decryptedMessage = "",
  simulationData = null,
  isGenerating = false,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [stepIndex, setStepIndex] = useState(0);

  // Position state for Pointer, Card, and Connector
  const [targetRect, setTargetRect] = useState(null);
  const [cardPos, setCardPos] = useState({ top: 100, left: 100 });
  const [connectorPath, setConnectorPath] = useState("");

  // Context-aware Q&A state
  const [question, setQuestion] = useState("");
  const [qaLoading, setQaLoading] = useState(false);
  const [qaHistory, setQaHistory] = useState([]);

  const cardRef = useRef(null);
  const qaEndRef = useRef(null);
  const activeElementRef = useRef(null);

  // Derive the exact current protocol stage from actual live state
  const deriveCurrentStage = useCallback(() => {
    if (isGenerating) return "running";
    if (encryptedMessage || decryptedMessage) return "message_encryption";
    if (finalKey && finalKey.length > 0) return "final_key";
    if (qber !== null) {
      if (keyAccepted === false || (eveEnabled && qber > 15)) {
        return "aborted";
      }
      return "qber_evaluation";
    }
    if (siftedBits && siftedBits.length > 0) return "basis_reconciliation";
    if (bobBits && bobBits.length > 0) return "bob_measurement";
    if (aliceBits && aliceBits.length > 0) return "alice_preparation";
    return "idle";
  }, [
    isGenerating,
    encryptedMessage,
    decryptedMessage,
    finalKey,
    qber,
    keyAccepted,
    eveEnabled,
    siftedBits,
    bobBits,
    aliceBits,
  ]);

  // Clean up all DOM highlights
  const clearHighlights = useCallback(() => {
    document.querySelectorAll(".qkd-highlighted-element").forEach((el) => {
      el.classList.remove("qkd-highlighted-element");
    });
    activeElementRef.current = null;
    setTargetRect(null);
    setConnectorPath("");
  }, []);

  // Trigger state analysis
  const handleAnalyze = async () => {
    if (loading) return; // Prevent duplicate requests
    clearHighlights();
    setIsOpen(true);
    setLoading(true);
    setErrorMsg("");
    setStepIndex(0);
    setQaHistory([]);
    setAnalysis(null); // Clear stale explanations

    const currentStage = deriveCurrentStage();
    const statePayload = {
      stage: currentStage,
      numBits,
      eveEnabled,
      aliceBits,
      aliceBases,
      bobBits,
      bobBases,
      siftedBits,
      finalKey,
      qber,
      keyAccepted,
      message,
      encryptedMessage,
      decryptedMessage,
      isGenerating,
    };

    try {
      const data = await analyzeSimulationState(statePayload);
      if (data && data.explanations && data.explanations.length > 0) {
        setAnalysis(data);
      } else {
        throw new Error("No explanations returned from analysis service");
      }
    } catch (err) {
      console.error("Analysis error:", err);
      setErrorMsg("Unable to analyze current QKD state. Please check your backend connection.");
    } finally {
      setLoading(false);
    }
  };

  // Close the analyzer and remove all highlights
  const handleClose = () => {
    clearHighlights();
    setIsOpen(false);
    setErrorMsg("");
  };

  // Re-calculate target element rect, card position, and connector path
  const updateHighlightAndPositions = useCallback(() => {
    if (!isOpen || !analysis || !analysis.explanations || analysis.explanations.length === 0) {
      clearHighlights();
      return;
    }

    const currentExplanation = analysis.explanations[stepIndex] || analysis.explanations[0];
    const targetKey = (currentExplanation.target || "controls").toLowerCase().trim();
    const selector = APPROVED_STAGE_SELECTORS[targetKey] || currentExplanation.selector || "[data-qkd-stage='controls']";

    // Find target in DOM
    const targetEl = document.querySelector(selector) || document.querySelector("[data-qkd-stage='controls']") || document.querySelector(".controls");

    if (!targetEl) {
      clearHighlights();
      return;
    }

    // Remove old highlights and apply to new target
    if (activeElementRef.current && activeElementRef.current !== targetEl) {
      activeElementRef.current.classList.remove("qkd-highlighted-element");
    }
    targetEl.classList.add("qkd-highlighted-element");
    activeElementRef.current = targetEl;

    // Get live element bounding rect
    const rect = targetEl.getBoundingClientRect();
    setTargetRect(rect);

    // Compute smart dock placement for explanation card so it never covers controls
    const cardWidth = 440;
    const cardHeight = cardRef.current ? cardRef.current.offsetHeight : 360;
    const padding = 16;

    let cardLeft;
    let cardTop;

    // Place card where there is maximum free space
    if (rect.right + cardWidth + padding < window.innerWidth) {
      cardLeft = rect.right + padding;
      cardTop = Math.max(padding, Math.min(rect.top, window.innerHeight - cardHeight - padding));
    } else if (rect.left - cardWidth - padding > 0) {
      cardLeft = rect.left - cardWidth - padding;
      cardTop = Math.max(padding, Math.min(rect.top, window.innerHeight - cardHeight - padding));
    } else if (rect.bottom + cardHeight + padding < window.innerHeight) {
      cardLeft = Math.max(padding, Math.min(rect.left, window.innerWidth - cardWidth - padding));
      cardTop = rect.bottom + padding;
    } else {
      cardLeft = Math.max(padding, Math.min(rect.left, window.innerWidth - cardWidth - padding));
      cardTop = Math.max(padding, rect.top - cardHeight - padding);
    }

    // Ensure within viewport bounds
    cardLeft = Math.max(padding, Math.min(cardLeft, window.innerWidth - cardWidth - padding));
    cardTop = Math.max(padding, Math.min(cardTop, window.innerHeight - cardHeight - padding));

    setCardPos({ top: cardTop, left: cardLeft });

    // Calculate connector path
    const targetCenterX = rect.left + rect.width / 2;
    const targetCenterY = rect.top + rect.height / 2;
    const cardCenterX = cardLeft + cardWidth / 2;
    const cardCenterY = cardTop + cardHeight / 2;

    let startX = cardCenterX;
    let startY = cardTop;
    let endX = targetCenterX;
    let endY = rect.bottom;

    if (cardLeft > rect.right) {
      startX = cardLeft;
      startY = Math.min(Math.max(cardTop + 30, targetCenterY), cardTop + cardHeight - 30);
      endX = rect.right + 4;
      endY = targetCenterY;
    } else if (cardLeft + cardWidth < rect.left) {
      startX = cardLeft + cardWidth;
      startY = Math.min(Math.max(cardTop + 30, targetCenterY), cardTop + cardHeight - 30);
      endX = rect.left - 4;
      endY = targetCenterY;
    } else if (cardTop > rect.bottom) {
      startX = cardCenterX;
      startY = cardTop;
      endX = targetCenterX;
      endY = rect.bottom + 4;
    } else {
      startX = cardCenterX;
      startY = cardTop + cardHeight;
      endX = targetCenterX;
      endY = rect.top - 4;
    }

    const midX = (startX + endX) / 2;
    const midY = (startY + endY) / 2;
    setConnectorPath(`M ${startX} ${startY} Q ${midX} ${midY} ${endX} ${endY}`);
  }, [isOpen, analysis, stepIndex, clearHighlights]);

  // Update positions on changes, scroll, or resize
  useEffect(() => {
    if (isOpen) {
      updateHighlightAndPositions();
      const onReposition = () => updateHighlightAndPositions();
      window.addEventListener("resize", onReposition);
      window.addEventListener("scroll", onReposition, true);
      return () => {
        window.removeEventListener("resize", onReposition);
        window.removeEventListener("scroll", onReposition, true);
        clearHighlights();
      };
    } else {
      clearHighlights();
    }
  }, [isOpen, updateHighlightAndPositions, clearHighlights]);

  // Ask a follow-up question
  const handleAskQuestion = async (textToAsk) => {
    const qText = (textToAsk || question).trim();
    if (!qText || qaLoading) return;

    setQuestion("");
    const newEntry = { question: qText, answer: null };
    const updatedHistory = [...qaHistory, newEntry];
    setQaHistory(updatedHistory);
    setQaLoading(true);

    const currentStage = deriveCurrentStage();
    const simState = {
      stage: currentStage,
      numBits,
      eveEnabled,
      aliceBitsCount: aliceBits.length,
      bobBitsCount: bobBits.length,
      siftedBitsCount: siftedBits.length,
      finalKeyLength: finalKey.length,
      qber,
      keyAccepted,
    };

    try {
      const historyForApi = qaHistory.map((item) => [
        { role: "user", content: item.question },
        { role: "model", content: item.answer || "" },
      ]).flat();

      const res = await askAnalysisQuestion(qText, simState, analysis, historyForApi);
      setQaHistory((prev) =>
        prev.map((item, idx) =>
          idx === prev.length - 1 ? { ...item, answer: res.answer } : item
        )
      );
      setTimeout(() => qaEndRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    } catch (err) {
      setQaHistory((prev) =>
        prev.map((item, idx) =>
          idx === prev.length - 1
            ? { ...item, answer: "⚠️ Could not get an answer. Verify backend connection." }
            : item
        )
      );
    } finally {
      setQaLoading(false);
    }
  };

  const currentExplanation =
    analysis && analysis.explanations && analysis.explanations[stepIndex]
      ? analysis.explanations[stepIndex]
      : null;

  return (
    <>
      {/* Analyze Button */}
      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="btn-analyze"
        title="Analyze the current QKD simulation state"
        aria-label="Analyze QKD Process"
      >
        <svg
          className="sparkle-icon"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12 2v4m0 12v4M2 12h4m12 0h4" />
          <path d="M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
        </svg>
        <span>{loading ? "Analyzing..." : "Analyze"}</span>
      </button>

      {/* When Analyzer is active */}
      {isOpen && (
        <>
          {/* SVG Connector Canvas */}
          <svg className="analyzer-svg-canvas">
            <defs>
              <linearGradient id="qkdGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#38bdf8" />
                <stop offset="100%" stopColor="#a855f7" />
              </linearGradient>
              <marker
                id="qkdArrow"
                markerWidth="8"
                markerHeight="8"
                refX="6"
                refY="4"
                orient="auto"
              >
                <polygon points="0 0, 8 4, 0 8" fill="#38bdf8" />
              </marker>
            </defs>
            {connectorPath && (
              <path
                d={connectorPath}
                className="analyzer-connector-path"
                markerEnd="url(#qkdArrow)"
              />
            )}
          </svg>

          {/* Floating Pointer attached to highlighted target element */}
          {targetRect && currentExplanation && (
            <div
              className="qkd-target-pointer"
              style={{
                top: `${Math.max(10, targetRect.top - 32)}px`,
                left: `${targetRect.left + targetRect.width / 2}px`,
                transform: "translateX(-50%)",
              }}
            >
              <span>👉 {currentExplanation.title}</span>
              <div className="qkd-target-pointer-arrow" />
            </div>
          )}

          {/* Explanation Card */}
          <div
            ref={cardRef}
            className="analyzer-card"
            style={{
              top: `${cardPos.top}px`,
              left: `${cardPos.left}px`,
            }}
          >
            {/* Header */}
            <div className="analyzer-card-header">
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span className="analyzer-badge">QKD State</span>
                <h4 className="analyzer-stage-name">
                  {analysis?.current_stage ? analysis.current_stage.replace(/_/g, " ").toUpperCase() : "ANALYZING..."}
                </h4>
              </div>
              <button
                className="analyzer-close-btn"
                onClick={handleClose}
                title="Close Analyzer"
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
            {loading ? (
              <div className="analyzer-loading-state">
                <div className="analyzer-spinner" />
                <p style={{ margin: 0, fontSize: "13px" }}>
                  Analyzing quantum simulation state...
                </p>
              </div>
            ) : errorMsg ? (
              <div className="analyzer-card-body">
                <div className="analyzer-error-box">{errorMsg}</div>
                <button
                  className="analyzer-nav-btn"
                  onClick={handleAnalyze}
                  style={{ alignSelf: "flex-start", marginTop: "8px" }}
                >
                  Retry Analysis
                </button>
              </div>
            ) : analysis ? (
              <div className="analyzer-card-body">
                {/* Stage Summary */}
                {analysis.summary && (
                  <p className="analyzer-summary">{analysis.summary}</p>
                )}

                {/* Current Active Highlight Explanation */}
                {currentExplanation && (
                  <div className="analyzer-explanation-box">
                    <div className="analyzer-exp-header">
                      <h5 className="analyzer-exp-title">
                        {currentExplanation.title}
                      </h5>
                      {analysis.explanations.length > 1 && (
                        <span className="analyzer-step-pill">
                          Region {stepIndex + 1} of {analysis.explanations.length}
                        </span>
                      )}
                    </div>
                    <p className="analyzer-exp-desc">
                      {currentExplanation.description}
                    </p>
                  </div>
                )}

                {/* Next Stage Indication */}
                {analysis.next_stage && (
                  <div className="analyzer-next-stage">
                    <strong>Next in BB84:</strong> {analysis.next_stage}
                  </div>
                )}

                {/* Metrics Insight */}
                {analysis.metrics_insight && (
                  <div className="analyzer-metrics-insight">
                    <strong>Metrics Analysis:</strong> {analysis.metrics_insight}
                  </div>
                )}

                {/* Multi-region Navigation (Previous / Next) */}
                {analysis.explanations && analysis.explanations.length > 1 && (
                  <div className="analyzer-nav-controls">
                    <button
                      className="analyzer-nav-btn"
                      onClick={() => setStepIndex((prev) => Math.max(0, prev - 1))}
                      disabled={stepIndex === 0}
                    >
                      ← Previous Region
                    </button>
                    <button
                      className="analyzer-nav-btn"
                      onClick={() =>
                        setStepIndex((prev) =>
                          Math.min(analysis.explanations.length - 1, prev + 1)
                        )
                      }
                      disabled={stepIndex === analysis.explanations.length - 1}
                    >
                      Next Region →
                    </button>
                  </div>
                )}

                {/* Context-aware Question Box */}
                <div className="analyzer-qa-section">
                  <h6 className="analyzer-qa-title">
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <circle cx="12" cy="12" r="10" />
                      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                      <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                    Ask AI About This Stage
                  </h6>

                  {/* Q&A Message History */}
                  {qaHistory.length > 0 && (
                    <div className="analyzer-qa-history">
                      {qaHistory.map((item, idx) => (
                        <div key={idx} className="analyzer-qa-msg">
                          <div className="analyzer-qa-q">Q: {item.question}</div>
                          <div className="analyzer-qa-a">
                            {item.answer ? (
                              item.answer
                            ) : (
                              <span style={{ fontStyle: "italic", opacity: 0.7 }}>
                                Thinking...
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                      <div ref={qaEndRef} />
                    </div>
                  )}

                  {/* Suggested Question Chips */}
                  {analysis.suggested_questions &&
                    analysis.suggested_questions.length > 0 && (
                      <div className="analyzer-qa-chips">
                        {analysis.suggested_questions.map((chip, cIdx) => (
                          <button
                            key={cIdx}
                            className="analyzer-qa-chip"
                            onClick={() => handleAskQuestion(chip)}
                            disabled={qaLoading}
                          >
                            {chip}
                          </button>
                        ))}
                      </div>
                    )}

                  {/* Question Input Form */}
                  <form
                    className="analyzer-qa-form"
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleAskQuestion();
                    }}
                  >
                    <input
                      type="text"
                      className="analyzer-qa-input"
                      placeholder="Ask about this stage, bases, or QBER..."
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      disabled={qaLoading}
                    />
                    <button
                      type="submit"
                      className="analyzer-qa-submit"
                      disabled={qaLoading || !question.trim()}
                    >
                      {qaLoading ? "..." : "Ask"}
                    </button>
                  </form>
                </div>
              </div>
            ) : null}
          </div>
        </>
      )}
    </>
  );
}
