"use client";

import React, { useState, useRef, useEffect } from "react";
import { sendCopilotMessage, CopilotChatResponse } from "../lib/api";
import { useVillageContext } from "./VillageContext";

type Message = {
  id: string;
  role: "user" | "assistant" | "error";
  text: string;
  metadata?: CopilotChatResponse["metadata"];
};

export default function CopilotChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Attempt to use context, but CopilotChat might be rendered outside provider? No, we wrapped it in VillageProvider.
  const context = useVillageContext();
  const selectedLgdCode = context?.selectedLgdCode;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      text: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await sendCopilotMessage(userMessage.text);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: response.status === "error" ? "error" : "assistant",
        text: response.text,
        metadata: response.metadata,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: unknown) {
      const errMsg = error instanceof Error ? error.message : "Failed to communicate with the Copilot.";
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "error",
          text: errMsg,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (example: string) => {
    setInput(example);
  };

  return (
    <div className="flex flex-col h-[600px] max-h-[80vh] w-full max-w-2xl bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-50 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-800">Intelligence Copilot</h2>
        <span className="text-xs font-medium px-2 py-1 bg-blue-100 text-blue-700 rounded-full">
          PUBLIC EVIDENCE ONLY
        </span>
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-4 bg-gray-50 flex flex-col gap-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 space-y-4">
            <p className="text-sm">Ask questions about civic analytics data.</p>
            <div className="flex flex-col gap-2 w-full max-w-sm">
              <button
                onClick={() => handleExampleClick("What is the current reported household tap-connection gap?")}
                className="text-left px-3 py-2 text-sm bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
              >
                &quot;What is the current reported household tap-connection gap?&quot;
              </button>
              <button
                onClick={() => handleExampleClick("Show me the current analytics readiness.")}
                className="text-left px-3 py-2 text-sm bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
              >
                &quot;Show me the current analytics readiness.&quot;
              </button>
              <button
                onClick={() => handleExampleClick(selectedLgdCode ? `What is the status for village ${selectedLgdCode}?` : "What is the status for village 586842?")}
                className="text-left px-3 py-2 text-sm bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
              >
                &quot;What is the status for village {selectedLgdCode || "586842"}?&quot;
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col max-w-[85%] ${
                msg.role === "user" ? "self-end items-end" : "self-start items-start"
              }`}
            >
              <div
                className={`px-4 py-2 rounded-lg text-sm ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : msg.role === "error"
                    ? "bg-red-50 text-red-800 border border-red-200"
                    : "bg-white text-gray-800 border border-gray-200"
                }`}
              >
                {msg.text}
              </div>

              {/* Provenance Metadata (only for successful assistant messages) */}
              {msg.metadata && msg.metadata.provenance.length > 0 && (
                <div className="mt-1 text-xs text-gray-500 flex flex-wrap gap-1">
                  {msg.metadata.provenance.map((prov, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 bg-gray-100 px-1.5 py-0.5 rounded text-gray-600 border border-gray-200"
                      title={`Version: ${prov.calculation_version || "N/A"}`}
                    >
                      <svg
                        className="w-3 h-3"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                      {prov.source_dataset || "Deterministic Source"}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="self-start items-start flex flex-col max-w-[85%]">
            <div className="px-4 py-3 bg-white border border-gray-200 rounded-lg text-sm flex gap-1 items-center">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-3 bg-white border-t border-gray-200 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={isLoading}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
          aria-label="Copilot message input"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-300 transition-colors"
          aria-label="Send message"
        >
          Send
        </button>
      </form>
    </div>
  );
}
