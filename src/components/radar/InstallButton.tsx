import { useEffect, useState } from "react";

type BIPEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

export function InstallButton({ className = "" }: { className?: string }) {
  const [deferred, setDeferred] = useState<BIPEvent | null>(null);
  const [installed, setInstalled] = useState(false);
  const [showHint, setShowHint] = useState(false);

  useEffect(() => {
    const onPrompt = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BIPEvent);
    };
    const onInstalled = () => {
      setInstalled(true);
      setDeferred(null);
    };
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);

    if (window.matchMedia("(display-mode: standalone)").matches) setInstalled(true);

    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  if (installed) return null;

  const handleClick = async () => {
    if (deferred) {
      await deferred.prompt();
      const choice = await deferred.userChoice;
      if (choice.outcome === "accepted") setInstalled(true);
      setDeferred(null);
    } else {
      setShowHint(true);
      setTimeout(() => setShowHint(false), 6000);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={handleClick}
        className={`inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-xs font-medium text-foreground transition hover:border-ember hover:text-ember ${className}`}
        aria-label="Instalar Radar Urbano"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d="M12 3v12" />
          <path d="m7 10 5 5 5-5" />
          <path d="M5 21h14" />
        </svg>
        <span className="hidden sm:inline">Instalar app</span>
        <span className="sm:hidden">Instalar</span>
      </button>
      {showHint && (
        <div className="absolute right-0 top-full z-30 mt-2 w-64 rounded-md border border-border bg-surface-elevated p-3 text-[11px] leading-relaxed text-muted-foreground shadow-elevated">
          Para instalar: no Chrome/Edge use o menu <span className="text-foreground">Instalar app</span>.
          No iPhone (Safari) toque em <span className="text-foreground">Compartilhar → Adicionar à tela inicial</span>.
        </div>
      )}
    </div>
  );
}
