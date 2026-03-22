"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Bot, Loader2, Mic, MicOff, Square, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { postChat } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type ChatPanelProps = {
  userId: string;
};

type ChatApiResponse = {
  response: string;
  observations: string[];
  next_steps: string[];
  audio_base64?: string | null;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  observations?: string[];
  next_steps?: string[];
};

type SpeechRecognitionResultLike = {
  transcript: string;
};

type SpeechRecognitionEventLike = {
  results: ArrayLike<ArrayLike<SpeechRecognitionResultLike>>;
};

type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechWindow = Window & {
  SpeechRecognition?: new () => SpeechRecognitionLike;
  webkitSpeechRecognition?: new () => SpeechRecognitionLike;
};

export function ChatPanel({ userId }: ChatPanelProps) {
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceAgentEnabled, setVoiceAgentEnabled] = useState(false);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [lastTranscript, setLastTranscript] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "init",
      role: "assistant",
      content: "I am ready. Tell me what is happening and I will guide you step by step.",
    },
  ]);
  const endRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const loadingRef = useRef(false);
  const speakingRef = useRef(false);
  const voiceAgentEnabledRef = useRef(false);
  const stopRequestedRef = useRef(false);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior,
      });
      return;
    }
    endRef.current?.scrollIntoView({ behavior });
  }, []);

  useEffect(() => {
    const nextBehavior: ScrollBehavior = loading ? "smooth" : "auto";
    scrollToBottom(nextBehavior);
    const rafId = requestAnimationFrame(() => scrollToBottom(nextBehavior));
    return () => cancelAnimationFrame(rafId);
  }, [messages, loading, scrollToBottom]);

  useEffect(() => {
    loadingRef.current = loading;
  }, [loading]);

  useEffect(() => {
    speakingRef.current = isSpeaking;
  }, [isSpeaking]);

  useEffect(() => {
    voiceAgentEnabledRef.current = voiceAgentEnabled;
  }, [voiceAgentEnabled]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const speechWindow = window as SpeechWindow;
    const Recognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setVoiceSupported(false);
      return;
    }

    const recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      setVoiceError(null);
      setIsListening(true);
    };

    recognition.onend = () => {
      setIsListening(false);

      if (stopRequestedRef.current) {
        stopRequestedRef.current = false;
        return;
      }

      if (voiceAgentEnabledRef.current && !loadingRef.current && !speakingRef.current) {
        setTimeout(() => {
          try {
            recognition.start();
          } catch {}
        }, 250);
      }
    };

    recognition.onerror = (event) => {
      setIsListening(false);
      const errorCode = event.error ?? "";

      if (errorCode === "no-speech" || errorCode === "aborted") {
        setVoiceError(null);
        if (voiceAgentEnabledRef.current && !loadingRef.current && !speakingRef.current) {
          setTimeout(() => {
            try {
              recognition.start();
            } catch {}
          }, 300);
        }
        return;
      }

      setVoiceError(errorCode ? `Voice input error: ${errorCode}` : "Voice input failed");
    };

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript ?? "")
        .join(" ")
        .trim();

      if (transcript) {
        setLastTranscript(transcript);
        if (voiceAgentEnabledRef.current) {
          void sendMessage(transcript);
        }
      }
    };

    recognitionRef.current = recognition;
    setVoiceSupported(true);

    return () => {
      recognitionRef.current?.stop();
      audioRef.current?.pause();
      recognitionRef.current = null;
      audioRef.current = null;
    };
  }, [userId]);

  const startListening = () => {
    if (!voiceSupported || !recognitionRef.current) {
      return;
    }
    if (loadingRef.current || speakingRef.current) {
      return;
    }
    try {
      recognitionRef.current.start();
    } catch {}
  };

  const stopListening = () => {
    if (!recognitionRef.current) {
      return;
    }
    if (isListening) {
      stopRequestedRef.current = true;
      recognitionRef.current.stop();
    }
  };

  const playAssistantAudio = async (audioBase64?: string | null) => {
    if (!audioBase64) {
      return;
    }

    setIsSpeaking(true);
    const dataUrl = `data:audio/mpeg;base64,${audioBase64}`;

    await new Promise<void>((resolve) => {
      const player = new Audio(dataUrl);
      audioRef.current = player;
      player.onended = () => resolve();
      player.onerror = () => resolve();
      void player.play().catch(() => resolve());
    });

    setIsSpeaking(false);
  };

  const sendMessage = async (content: string) => {
    if (!content.trim()) {
      return;
    }

    stopListening();

    const nextUserMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
    };

    setMessages((prev) => [...prev, nextUserMessage]);
    setLoading(true);

    try {
      const data: ChatApiResponse = await postChat({
        user_id: userId,
        message: nextUserMessage.content,
        include_voice: true,
      });

      const assistantMessage: ChatMessage = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        content: data.response ?? "",
        observations: data.observations ?? [],
        next_steps: data.next_steps ?? [],
      };
      setMessages((prev) => [...prev, assistantMessage]);

      if (voiceAgentEnabledRef.current) {
        await playAssistantAudio(data.audio_base64);
      }
    } catch {
      setVoiceError("Failed to get mentor response. Check backend/API keys and try again.");
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}-assistant-error`,
          role: "assistant",
          content: "I hit a backend issue while generating a response. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
      if (voiceAgentEnabledRef.current) {
        startListening();
      }
    }
  };

  const onToggleVoiceAgent = () => {
    if (!voiceSupported || !recognitionRef.current) {
      setVoiceError("Voice input is not supported in this browser");
      return;
    }

    if (voiceAgentEnabled) {
      setVoiceAgentEnabled(false);
      stopListening();
      audioRef.current?.pause();
      setIsSpeaking(false);
      return;
    }

    setVoiceError(null);
    setVoiceAgentEnabled(true);
    startListening();
  };

  return (
    <Card className="h-[720px] overflow-hidden">
      <CardHeader className="border-b border-[#1F1F1F]">
        <CardTitle className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-[#F59E0B]" /> Axion Voice Agent
        </CardTitle>
        <CardDescription>Voice-first mode with automatic listen, response, and resume.</CardDescription>
      </CardHeader>

      <CardContent className="flex h-[calc(100%-86px)] flex-col p-0">
        <div ref={messagesContainerRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
          {messages.map((item) => {
            const isUser = item.role === "user";
            return (
              <div key={item.id} className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
                {!isUser && (
                  <span className="mt-1 inline-flex h-7 w-7 items-center justify-center rounded-full border border-[#2B1E07] bg-[rgba(245,158,11,0.12)]">
                    <Bot className="h-3.5 w-3.5 text-[#F59E0B]" />
                  </span>
                )}

                <div
                  className={`max-w-[82%] rounded-2xl px-3 py-2.5 text-sm leading-6 ${
                    isUser
                      ? "rounded-tr-sm border border-[#2C2C2C] bg-[#131313] text-[#E5E5E5]"
                      : "rounded-tl-sm border border-[#1F1F1F] bg-[#101010] text-[#E5E5E5]"
                  }`}
                >
                  {isUser ? (
                    <p>{item.content}</p>
                  ) : (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                        ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>,
                        ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>,
                        li: ({ children }) => <li className="text-[#E5E5E5]">{children}</li>,
                        strong: ({ children }) => <strong className="font-semibold text-[#F5F5F5]">{children}</strong>,
                        em: ({ children }) => <em className="italic">{children}</em>,
                        code: ({ children }) => (
                          <code className="rounded bg-[#1A1A1A] px-1 py-0.5 text-xs text-[#E5E5E5]">{children}</code>
                        ),
                        pre: ({ children }) => (
                          <pre className="mb-2 overflow-x-auto rounded-lg border border-[#1F1F1F] bg-[#0B0B0C] p-3 text-xs last:mb-0">
                            {children}
                          </pre>
                        ),
                        hr: () => <hr className="my-3 border-[#1F1F1F]" />,
                        table: ({ children }) => (
                          <div className="mb-2 overflow-x-auto last:mb-0">
                            <table className="w-full border-collapse text-xs">{children}</table>
                          </div>
                        ),
                        th: ({ children }) => <th className="border border-[#2A2A2A] bg-[#141414] px-2 py-1 text-left">{children}</th>,
                        td: ({ children }) => <td className="border border-[#2A2A2A] px-2 py-1 align-top">{children}</td>,
                      }}
                    >
                      {item.content}
                    </ReactMarkdown>
                  )}

                  {!isUser && !!item.observations?.length && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {item.observations.map((ob) => (
                        <Badge key={ob} variant="muted">
                          {ob}
                        </Badge>
                      ))}
                    </div>
                  )}

                  {!isUser && !!item.next_steps?.length && (
                    <ul className="mt-3 space-y-1.5 text-xs text-[#A1A1AA]">
                      {item.next_steps.map((step) => (
                        <li key={step} className="flex items-start gap-2">
                          <span className="mt-1 h-1.5 w-1.5 rounded-full bg-[#F59E0B]" />
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {isUser && (
                  <span className="mt-1 inline-flex h-7 w-7 items-center justify-center rounded-full border border-[#2C2C2C] bg-[#151515]">
                    <User className="h-3.5 w-3.5 text-[#A1A1AA]" />
                  </span>
                )}
              </div>
            );
          })}

          {loading && (
            <div className="flex items-center gap-2 text-sm text-[#A1A1AA]">
              <Loader2 className="h-4 w-4 animate-spin" /> Thinking...
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="border-t border-[#1F1F1F] bg-[#090909] px-5 py-6">
          {voiceError && <p className="mb-2 text-xs text-red-400">{voiceError}</p>}
          {lastTranscript && <p className="mb-2 truncate text-xs text-[#A1A1AA]">You: {lastTranscript}</p>}

          <div className="mb-3 flex justify-center gap-1.5">
            {Array.from({ length: 18 }).map((_, index) => (
              <span
                key={`bar-${index}`}
                className={`h-2 w-1 rounded-full transition-all duration-200 ${
                  isListening || isSpeaking ? "bg-[#F59E0B] opacity-90" : "bg-[#27272A]"
                }`}
                style={{ transform: isListening || isSpeaking ? `scaleY(${1 + ((index % 5) + 1) * 0.12})` : "scaleY(1)" }}
              />
            ))}
          </div>

          <div className="flex items-center justify-center gap-5">
            <button
              type="button"
              onClick={() => {
                setVoiceAgentEnabled(false);
                stopListening();
                audioRef.current?.pause();
                setIsSpeaking(false);
              }}
              className="inline-flex h-12 w-12 items-center justify-center rounded-full border border-[#1F1F1F] bg-[#0F0F10] text-[#A1A1AA] transition hover:text-[#E5E5E5] disabled:opacity-40"
              disabled={!voiceAgentEnabled}
              aria-label="Stop audio"
            >
              <MicOff className="h-5 w-5" />
            </button>

            <button
              type="button"
              onClick={onToggleVoiceAgent}
              disabled={!voiceSupported || loading}
              aria-label={voiceAgentEnabled ? "Stop voice agent" : "Start voice agent"}
              className={`inline-flex h-24 w-24 items-center justify-center rounded-full text-white shadow-[0_0_36px_rgba(245,158,11,0.22)] transition disabled:opacity-50 ${
                voiceAgentEnabled ? "bg-[#D97706]" : "bg-[#F59E0B]"
              }`}
            >
              {voiceAgentEnabled ? <Square className="h-7 w-7" /> : <Mic className="h-8 w-8" />}
            </button>

            <div className="inline-flex h-12 min-w-12 items-center justify-center rounded-full border border-[#1F1F1F] bg-[#0F0F10] px-4 text-xs text-[#A1A1AA]">
              {isSpeaking ? "AI" : isListening ? "LIVE" : "IDLE"}
            </div>
          </div>

          <p className="mt-3 text-center text-xs text-[#A1A1AA]">
            {voiceAgentEnabled
              ? isSpeaking
                ? "Agent speaking"
                : isListening
                  ? "Listening"
                  : "Voice mode active"
              : "Tap mic to start voice mode"}
          </p>

          {!voiceSupported && (
            <p className="mt-2 text-center text-xs text-[#A1A1AA]">Voice input is not supported in this browser.</p>
          )}

          <div className="mt-3 flex justify-center">
            <Badge variant="muted">Hands-free mode</Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
