import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const Lumina = () => {
    const [messages, setMessages] = useState([{ role: 'ai', content: 'SUN AI is online. How can I assist you?' }]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const scrollRef = useRef(null);
}

useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
         const response = await fetch('http://localhost:8000/chat', {
            method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: input })
          });
        const data = await response.json();
        setMessages(prev => [...prev, { role: 'ai', content: data.response }]);
         } catch (err) {
            setMessages(prev => [...prev, { role: 'ai', content: "Connection lost. Is the Backend running?" }]);
         }finally {
      setIsTyping(false);
    }
}

return (
    <div className="min-h-screen bg-[#050505] text-slate-200 flex flex-col items-center p-4 selection:bg-cyan-500/30">
        <div className="fixed top-0 left-1/2 -translate-x-1/2 w-125 h-75 bg-cyan-600/20 blur-[120px] rounded-full -z-10" />
        <header className="w-full max-w-3xl flex justify-between items-center py-6 border-b border-white/10 mb-6">
        
        </header>
    </div>
)