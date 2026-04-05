import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, Bot, User, BrainCircuit, Loader2, ArrowUpRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { HumanMessage } from "@langchain/core/messages";
import { appGraph } from '../lib/graph';

type Message = {
  id: string;
  role: 'user' | 'model';
  content: string;
  isError?: boolean;
};

export default function AIChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isChatOpen) scrollToBottom();
  }, [messages, isChatOpen]);

  const handleSend = async (text: string = input) => {
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setIsChatOpen(true);

    try {
      const initialState = {
        messages: [new HumanMessage(text.trim())],
      };
      
      const result = await appGraph.invoke(initialState);
      
      const modelMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        content: result.finalResponse || "I processed your request.",
      };

      setMessages((prev) => [...prev, modelMessage]);
    } catch (error) {
      console.error("Error generating response:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        content: "I'm sorry, I encountered an error connecting to the AI agent.",
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickPrompts = [
    "Reduce my expenses",
    "Rebalance portfolio",
    "Save more tax",
    "Explain health score",
    "Am I on track?"
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-slate-200 bg-[#FDFDF9]/95 p-4 backdrop-blur-xl shadow-[0_-10px_40px_-15px_rgba(15,23,42,0.08)]">
      <div className="max-w-4xl mx-auto">
        <AnimatePresence>
          {isChatOpen && (
            <motion.div 
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: '400px', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mb-4 flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
            >
              <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 p-3">
                <div className="flex items-center gap-2">
                  <BrainCircuit className="w-5 h-5 text-indigo-600" />
                  <span className="font-semibold text-sm text-slate-800">AI Financial Advisor</span>
                </div>
                <button onClick={() => setIsChatOpen(false)} className="text-slate-400 hover:text-slate-600 text-sm font-medium px-2">
                  Close
                </button>
              </div>
              
              <div className="flex-1 space-y-4 overflow-y-auto bg-[#FDFDF9] p-4">
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                      msg.role === 'user' ? 'bg-slate-800' : 'bg-indigo-100'
                    }`}>
                      {msg.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-indigo-600" />}
                    </div>
                    <div className={`max-w-[85%] rounded-2xl p-3 text-sm ${
                      msg.role === 'user' 
                        ? 'bg-slate-800 text-white rounded-tr-sm' 
                        : msg.isError 
                          ? 'bg-red-50 text-red-800 border border-red-100 rounded-tl-sm'
                          : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm shadow-sm'
                    }`}>
                      <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4 text-indigo-600" />
                    </div>
                    <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm p-3 flex items-center gap-2 text-slate-500 shadow-sm">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm">Analyzing your finances...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {!isChatOpen && (
          <div className="flex gap-2 overflow-x-auto pb-3 scrollbar-hide">
            {quickPrompts.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleSend(prompt)}
                className="flex items-center gap-1.5 whitespace-nowrap rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm transition-colors hover:border-slate-300 hover:bg-slate-50"
              >
                {prompt} <ArrowUpRight className="w-3 h-3 text-slate-400" />
              </button>
            ))}
          </div>
        )}

        <div className="relative flex items-center gap-2 rounded-full border border-slate-300 bg-white p-1.5 shadow-sm transition-all focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500">
          <div className="pl-3 text-slate-400">
            <Bot className="w-5 h-5" />
          </div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask anything about your finances..."
            className="flex-1 bg-transparent border-none focus:ring-0 py-2 px-2 text-sm text-slate-800 placeholder-slate-400 outline-none"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center shrink-0 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:hover:bg-indigo-600 transition-colors"
          >
            <Send className="w-4 h-4 ml-0.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
