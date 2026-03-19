import { toPng } from "html-to-image";
import { useCallback } from "react";

interface Props {
  targetRef: React.RefObject<HTMLDivElement | null>;
  filename?: string;
}

export function SnapshotButton({ targetRef, filename = "market-signal" }: Props) {
  const handleSnapshot = useCallback(async () => {
    if (!targetRef.current) return;

    try {
      const dataUrl = await toPng(targetRef.current, {
        backgroundColor: "#0d1117",
        pixelRatio: 2,
      });

      // Try Web Share API on mobile
      if (navigator.share && navigator.canShare) {
        const blob = await (await fetch(dataUrl)).blob();
        const file = new File([blob], `${filename}.png`, { type: "image/png" });
        if (navigator.canShare({ files: [file] })) {
          await navigator.share({ files: [file] });
          return;
        }
      }

      // Fallback: download
      const link = document.createElement("a");
      link.download = `${filename}.png`;
      link.href = dataUrl;
      link.click();
    } catch (err) {
      console.error("Snapshot failed:", err);
    }
  }, [targetRef, filename]);

  return (
    <button className="snapshot-btn" onClick={handleSnapshot} title="Share as image">
      SNAPSHOT
    </button>
  );
}
