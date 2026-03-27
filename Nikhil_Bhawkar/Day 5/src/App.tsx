import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import { Toaster, toast } from 'sonner';
import { 
  Zap, 
  TrendingUp, 
  Users, 
  Calendar, 
  ChevronRight, 
  CheckCircle2, 
  ArrowRight, 
  BarChart3, 
  MessageSquare, 
  Sparkles,
  Linkedin,
  Menu,
  X,
  Copy,
  Check,
  RefreshCw,
  ArrowLeft
} from 'lucide-react';

// --- Components ---

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 orange-gradient rounded-lg flex items-center justify-center">
              <Zap className="text-white w-5 h-5" />
            </div>
            <span className="text-xl font-bold tracking-tight font-display">Ghostly</span>
          </Link>
          
          <div className="hidden md:flex items-center gap-8">
            <a href="/#features" className="text-sm text-muted-foreground hover:text-white transition-colors">Features</a>
            <a href="/#pricing" className="text-sm text-muted-foreground hover:text-white transition-colors">Pricing</a>
            <button className="text-sm font-medium px-4 py-2 rounded-full border border-white/10 hover:bg-white/5 transition-colors text-white">
              Sign In
            </button>
            <button 
              onClick={() => navigate('/editor')}
              className="text-sm font-medium px-5 py-2 rounded-full orange-gradient text-white hover:opacity-90 transition-opacity"
            >
              Start Scaling Now
            </button>
          </div>

          <div className="md:hidden">
            <button onClick={() => setIsOpen(!isOpen)} className="text-white">
              {isOpen ? <X /> : <Menu />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="md:hidden glass border-b border-white/10 absolute top-16 left-0 right-0 p-4 space-y-4"
          >
            <a href="/#features" className="block text-lg text-muted-foreground">Features</a>
            <a href="/#pricing" className="block text-lg text-muted-foreground">Pricing</a>
            <div className="pt-4 flex flex-col gap-3">
              <button className="w-full py-3 rounded-xl border border-white/10 text-white">Sign In</button>
              <button 
                onClick={() => { navigate('/editor'); setIsOpen(false); }}
                className="w-full py-3 rounded-xl orange-gradient text-white"
              >
                Start Scaling Now
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

const Hero = () => {
  const navigate = useNavigate();
  return (
    <section className="relative pt-32 pb-20 overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-orange-500/10 blur-[120px] rounded-full -z-10" />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-primary mb-6">
            <Sparkles className="w-3 h-3" />
            AI-Powered LinkedIn Growth
          </span>
          <h1 className="text-5xl md:text-7xl font-bold font-display tracking-tight mb-6">
            Become a <span className="text-gradient">Top 1% Creator</span> <br />
            Without the Burnout
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            Ghostly is your AI ghostwriter and growth engine. Generate viral posts, schedule content, and engage with your audience—all in one slick interface.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <button 
              onClick={() => navigate('/editor')}
              className="w-full sm:w-auto px-8 py-4 rounded-full orange-gradient text-white font-semibold text-lg flex items-center justify-center gap-2 hover:scale-105 transition-transform"
            >
              Start Scaling Now <ArrowRight className="w-5 h-5" />
            </button>
            <button className="w-full sm:w-auto px-8 py-4 rounded-full bg-white/5 border border-white/10 text-white font-semibold text-lg hover:bg-white/10 transition-colors">
              Watch Demo
            </button>
          </div>
        </motion.div>

        {/* Dashboard Preview */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="relative max-w-5xl mx-auto"
        >
          <div className="glass rounded-2xl p-2 border-white/10 shadow-2xl shadow-orange-500/5">
            <div className="bg-zinc-900 rounded-xl overflow-hidden border border-white/5">
              <div className="h-8 bg-zinc-800 flex items-center px-4 gap-2">
                <div className="w-2 h-2 rounded-full bg-red-500/50" />
                <div className="w-2 h-2 rounded-full bg-amber-500/50" />
                <div className="w-2 h-2 rounded-full bg-emerald-500/50" />
              </div>
              <div className="p-6 grid grid-cols-12 gap-6">
                <div className="col-span-3 space-y-4">
                  <div className="h-4 w-3/4 bg-white/5 rounded" />
                  <div className="h-4 w-1/2 bg-white/5 rounded" />
                  <div className="h-4 w-2/3 bg-white/5 rounded" />
                  <div className="pt-8 space-y-4">
                    <div className="h-10 w-full bg-orange-500/20 rounded-lg border border-orange-500/30" />
                    <div className="h-10 w-full bg-white/5 rounded-lg" />
                  </div>
                </div>
                <div className="col-span-9 space-y-6">
                  <div className="grid grid-cols-3 gap-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-24 glass rounded-xl p-4 flex flex-col justify-between">
                        <div className="h-2 w-1/2 bg-white/10 rounded" />
                        <div className="h-6 w-3/4 bg-white/20 rounded" />
                      </div>
                    ))}
                  </div>
                  <div className="h-64 glass rounded-xl p-6 relative overflow-hidden">
                    <div className="flex justify-between mb-8">
                      <div className="h-4 w-32 bg-white/10 rounded" />
                      <div className="h-4 w-24 bg-white/10 rounded" />
                    </div>
                    <div className="flex items-end gap-2 h-32">
                      {[40, 70, 45, 90, 65, 80, 55, 95, 75].map((h, i) => (
                        <motion.div 
                          key={i}
                          initial={{ height: 0 }}
                          animate={{ height: `${h}%` }}
                          transition={{ delay: 0.5 + (i * 0.1) }}
                          className="flex-1 orange-gradient rounded-t-sm opacity-80"
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

const Features = () => {
  const features = [
    {
      icon: <Sparkles className="w-6 h-6" />,
      title: "AI Ghostwriting",
      description: "Generate high-converting LinkedIn posts in your unique voice. No more writer's block."
    },
    {
      icon: <Calendar className="w-6 h-6" />,
      title: "Smart Scheduling",
      description: "Queue your content for the best times to post. Set it and forget it while you scale."
    },
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: "Deep Analytics",
      description: "Understand what works. Track impressions, engagement, and profile visits with precision."
    },
    {
      icon: <Users className="w-6 h-6" />,
      title: "Engagement Hub",
      description: "Manage comments and network with key industry leaders directly from your dashboard."
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "Trend Detection",
      description: "Our AI scans LinkedIn to find trending topics in your niche before they go viral."
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Hook Generator",
      description: "Stop the scroll with 50+ proven hook templates optimized for the LinkedIn algorithm."
    }
  ];

  return (
    <section id="features" className="py-24 bg-zinc-950/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold font-display mb-4">Everything you need to <span className="text-primary">Dominate</span></h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Stop guessing and start growing. Our suite of tools is designed for serious creators who want to scale their personal brand.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              whileHover={{ y: -5 }}
              className="p-8 rounded-2xl glass border-white/5 hover:border-primary/20 transition-all group"
            >
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary mb-6 group-hover:orange-gradient group-hover:text-white transition-all">
                {feature.icon}
              </div>
              <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

const Pricing = () => {
  const plans = [
    {
      name: "Starter",
      price: "29",
      description: "Perfect for new creators finding their voice.",
      features: ["15 AI Posts / month", "Basic Analytics", "Content Calendar", "5 Hook Templates"],
      cta: "Get Started",
      popular: false
    },
    {
      name: "Pro",
      price: "79",
      description: "For serious creators scaling their brand.",
      features: ["Unlimited AI Posts", "Advanced Analytics", "Engagement Hub", "Trend Detection", "Priority Support"],
      cta: "Start Free Trial",
      popular: true
    },
    {
      name: "Agency",
      price: "199",
      description: "Manage multiple profiles with ease.",
      features: ["Up to 5 Profiles", "Team Collaboration", "White-label Reports", "Dedicated Manager", "API Access"],
      cta: "Contact Sales",
      popular: false
    }
  ];

  return (
    <section id="pricing" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold font-display mb-4">Simple, <span className="text-primary">Transparent</span> Pricing</h2>
          <p className="text-muted-foreground">Choose the plan that fits your growth stage.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <div 
              key={index}
              className={`p-8 rounded-3xl border ${plan.popular ? 'border-primary bg-primary/5 relative' : 'border-white/10 glass'} flex flex-col`}
            >
              {plan.popular && (
                <span className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full orange-gradient text-white text-xs font-bold uppercase tracking-widest">
                  Most Popular
                </span>
              )}
              <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="text-4xl font-bold">${plan.price}</span>
                <span className="text-muted-foreground">/mo</span>
              </div>
              <p className="text-sm text-muted-foreground mb-8">{plan.description}</p>
              
              <ul className="space-y-4 mb-10 flex-1">
                {plan.features.map((feature, fIndex) => (
                  <li key={fIndex} className="flex items-center gap-3 text-sm">
                    <CheckCircle2 className="w-5 h-5 text-primary shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>

              <button className={`w-full py-4 rounded-xl font-bold transition-all ${plan.popular ? 'orange-gradient text-white hover:scale-[1.02]' : 'bg-white/5 border border-white/10 hover:bg-white/10 text-white'}`}>
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

const Footer = () => {
  return (
    <footer className="py-12 border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 orange-gradient rounded-lg flex items-center justify-center">
              <Zap className="text-white w-5 h-5" />
            </div>
            <span className="text-xl font-bold tracking-tight font-display">Ghostly</span>
          </div>
          
          <div className="flex gap-8 text-sm text-muted-foreground">
            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-white transition-colors">Twitter</a>
            <a href="#" className="hover:text-white transition-colors">LinkedIn</a>
          </div>

          <p className="text-sm text-muted-foreground">
            © 2026 Ghostly AI. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

// --- Pages ---

const LandingPage = () => {
  const navigate = useNavigate();
  return (
    <>
      <Navbar />
      <Hero />
      
      {/* Social Proof */}
      <section className="py-12 border-y border-white/5 bg-white/[0.02]">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground mb-8">Trusted by creators at</p>
          <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 opacity-40 grayscale hover:grayscale-0 transition-all">
            <div className="flex items-center gap-2 text-xl font-bold"><Linkedin className="w-6 h-6" /> LinkedIn</div>
            <div className="text-xl font-bold">Google</div>
            <div className="text-xl font-bold">Meta</div>
            <div className="text-xl font-bold">Amazon</div>
            <div className="text-xl font-bold">Netflix</div>
          </div>
        </div>
      </section>

      <Features />

      {/* CTA Section */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 orange-gradient opacity-10 -z-10" />
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-4xl md:text-6xl font-bold font-display mb-6">Ready to scale your <br />LinkedIn presence?</h2>
          <p className="text-xl text-muted-foreground mb-10">Join 5,000+ creators who are already using Ghostly to build their personal brand.</p>
          <button 
            onClick={() => navigate('/editor')}
            className="px-10 py-5 rounded-full orange-gradient text-white font-bold text-xl hover:scale-105 transition-transform shadow-2xl shadow-orange-500/20"
          >
            Get Started for Free
          </button>
          <p className="mt-6 text-sm text-muted-foreground">No credit card required. 14-day free trial.</p>
        </div>
      </section>

      <Pricing />
      <Footer />
    </>
  );
};

const EditorPage = () => {
  const [topic, setTopic] = useState('');
  const [style, setStyle] = useState('Authority (Expert & Confident)');
  const [category, setCategory] = useState('Thought Leadership (Industry Insights)');
  const [length, setLength] = useState(2);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [generatedPost, setGeneratedPost] = useState('');
  const [copied, setCopied] = useState(false);
  const navigate = useNavigate();

  const writingStyles = [
    "Authority (Expert & Confident)",
    "Storyteller (Narrative & Emotional)",
    "Educator (Clear & Instructive)",
    "Provocateur (Contrarian & Bold)",
    "Conversationalist (Relatable & Friendly)",
    "Minimalist (Punchy & Direct)",
    "Visionary (Inspirational & Future-focused)"
  ];

  const categories = [
    "Thought Leadership (Industry Insights)",
    "Personal Branding (Behind-the-scenes)",
    "Actionable Advice (Step-by-step)",
    "Industry Analysis (Trends & Data)",
    "Case Study (Results & Proof)",
    "Contrarian Take (Myth Busting)",
    "Resource Roundup (Curated Lists)"
  ];

  const getLengthLabel = (val: number) => {
    if (val === 1) return "Short";
    if (val === 2) return "Medium";
    return "Large";
  };

  const handleGenerate = async () => {
    if (!topic) {
      toast.error("Please enter a topic first.");
      return;
    }
    
    setIsGenerating(true);
    const apiUrl = "/api/generate-post";
    
    const payload = {
      topic,
      writingStyle: style,
      postCategory: category,
      postLength: getLengthLabel(length)
    };

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // Handle different possible response formats from n8n
        let postContent = "";
        try {
          let parsed = typeof result.data === 'string' ? JSON.parse(result.data) : result.data;
          
          // If it's an array, take the first element
          if (Array.isArray(parsed) && parsed.length > 0) {
            parsed = parsed[0];
          }
          
          postContent = parsed.post || 
                        parsed.content || 
                        parsed.text || 
                        parsed.output || 
                        parsed.message || 
                        (typeof parsed === 'string' ? parsed : JSON.stringify(parsed, null, 2));
        } catch (e) {
          postContent = result.data;
        }
        setGeneratedPost(postContent);
        toast.success("Post generated successfully!");
      } else {
        toast.error(`Failed to generate post: ${result.error || "Unknown error"}`);
      }
    } catch (error) {
      console.error("Error generating post:", error);
      toast.error("Network error. Please check your connection.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePublish = async () => {
    if (!generatedPost) {
      toast.error("There is no content to publish.");
      return;
    }

    setIsPublishing(true);
    const apiUrl = "/api/publish-post";

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ post: generatedPost }),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        toast.success("Post successfully published to LinkedIn!");
      } else {
        toast.error(`Failed to publish: ${result.error || "Unknown error"}`);
      }
    } catch (error) {
      console.error("Error publishing post:", error);
      toast.error("Network error. Please check your connection.");
    } finally {
      setIsPublishing(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedPost);
    setCopied(true);
    toast.success("Copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Toaster position="top-center" theme="dark" />
      {/* Editor Header */}
      <header className="h-16 glass border-b border-white/5 flex items-center justify-between px-6 sticky top-0 z-50">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate('/')}
            className="p-2 hover:bg-white/5 rounded-lg transition-colors text-muted-foreground hover:text-white"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 orange-gradient rounded flex items-center justify-center">
              <Zap className="text-white w-4 h-4" />
            </div>
            <span className="font-bold font-display">Ghostly Editor</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => toast.info("Draft saved locally.")}
            className="text-sm font-medium px-4 py-2 rounded-lg border border-white/10 hover:bg-white/5 transition-colors text-white"
          >
            Save Draft
          </button>
          <button 
            onClick={handlePublish}
            disabled={isPublishing || !generatedPost}
            className={`text-sm font-medium px-4 py-2 rounded-lg orange-gradient text-white hover:opacity-90 transition-opacity flex items-center gap-2 ${isPublishing || !generatedPost ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isPublishing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Publishing...
              </>
            ) : (
              <>
                <ArrowRight className="w-4 h-4" />
                Publish to LinkedIn
              </>
            )}
          </button>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Configuration (30%) */}
        <aside className="w-[30%] min-w-[320px] border-r border-white/5 p-8 overflow-y-auto bg-zinc-950/30">
          <div className="max-w-md mx-auto space-y-8">
            <div>
              <h2 className="text-xl font-bold font-display mb-2">Post Configuration</h2>
              <p className="text-sm text-muted-foreground">Fine-tune your AI ghostwriter settings.</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">Main Topic / Theme</label>
                <textarea 
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g. The future of remote work in 2026..."
                  rows={4}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-primary/50 transition-colors resize-none text-sm leading-relaxed"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">Writing Style</label>
                <div className="relative">
                  <select 
                    value={style}
                    onChange={(e) => setStyle(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-primary/50 transition-colors appearance-none text-sm"
                  >
                    {writingStyles.map(s => <option key={s} value={s} className="bg-zinc-900">{s}</option>)}
                  </select>
                  <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground rotate-90 pointer-events-none" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-widest text-muted-foreground mb-3">Post Category</label>
                <div className="relative">
                  <select 
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-primary/50 transition-colors appearance-none text-sm"
                  >
                    {categories.map(c => <option key={c} value={c} className="bg-zinc-900">{c}</option>)}
                  </select>
                  <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground rotate-90 pointer-events-none" />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-4">
                  <label className="block text-xs font-bold uppercase tracking-widest text-muted-foreground">Target Length</label>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-primary/20 text-primary uppercase tracking-wider">
                    {getLengthLabel(length)}
                  </span>
                </div>
                <input 
                  type="range"
                  min="1"
                  max="3"
                  step="1"
                  value={length}
                  onChange={(e) => setLength(parseInt(e.target.value))}
                  className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <div className="flex justify-between mt-2 px-1">
                  <span className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest">Short</span>
                  <span className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest">Medium</span>
                  <span className="text-[9px] text-muted-foreground font-bold uppercase tracking-widest">Long</span>
                </div>
              </div>

              <button 
                onClick={handleGenerate}
                disabled={isGenerating || !topic}
                className={`w-full py-4 rounded-xl orange-gradient text-white font-bold text-lg shadow-lg shadow-primary/20 transition-all flex items-center justify-center gap-2 mt-8 ${isGenerating || !topic ? 'opacity-50 cursor-not-allowed' : 'hover:scale-[1.02]'}`}
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Generate Post
                  </>
                )}
              </button>
            </div>
          </div>
        </aside>

        {/* Right Main: Editor (70%) */}
        <main className="flex-1 p-12 bg-zinc-950 overflow-y-auto">
          <div className="max-w-4xl mx-auto h-full flex flex-col">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] animate-pulse" />
                <span className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">Editor Workspace</span>
              </div>
              {generatedPost && (
                <div className="flex items-center gap-4">
                  <button 
                    onClick={handleCopy}
                    className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground hover:text-white transition-colors py-2 px-3 rounded-lg hover:bg-white/5"
                  >
                    {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                </div>
              )}
            </div>

            <div className="flex-1 relative glass rounded-3xl border-white/5 p-10 shadow-2xl overflow-hidden">
              {!generatedPost && !isGenerating && (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-12 pointer-events-none z-0">
                  <div className="w-20 h-20 rounded-3xl bg-white/5 flex items-center justify-center mb-8 border border-white/10">
                    <Linkedin className="w-10 h-10 text-white/10" />
                  </div>
                  <h3 className="text-2xl font-bold mb-3 opacity-40 font-display">Your masterpiece starts here</h3>
                  <p className="text-muted-foreground text-base max-w-sm opacity-40 leading-relaxed">
                    Configure your parameters on the left and click "Generate Post" to craft your next viral LinkedIn post.
                  </p>
                </div>
              )}

              {isGenerating && (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-12 z-20 bg-zinc-950/80 backdrop-blur-sm">
                  <div className="w-32 h-1 bg-white/10 rounded-full overflow-hidden mb-6">
                    <motion.div 
                      initial={{ x: "-100%" }}
                      animate={{ x: "100%" }}
                      transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                      className="w-full h-full orange-gradient"
                    />
                  </div>
                  <p className="text-sm font-bold uppercase tracking-[0.3em] text-primary animate-pulse">AI is crafting your viral post...</p>
                </div>
              )}

              <textarea 
                value={generatedPost}
                onChange={(e) => setGeneratedPost(e.target.value)}
                placeholder="Start typing or generate a post..."
                className={`w-full h-full bg-transparent border-none focus:ring-0 text-xl leading-[1.8] resize-none transition-opacity duration-500 scrollbar-hide font-sans ${isGenerating ? 'opacity-10' : 'opacity-100'}`}
                spellCheck="false"
              />
            </div>
            
            <div className="mt-6 flex justify-between items-center text-[10px] text-muted-foreground font-bold uppercase tracking-widest px-4">
              <div className="flex gap-6">
                <span>Characters: {generatedPost.length}</span>
                <span>Words: {generatedPost.trim() ? generatedPost.trim().split(/\s+/).length : 0}</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                <span>Auto-save enabled</span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/editor" element={<EditorPage />} />
      </Routes>
    </BrowserRouter>
  );
}
