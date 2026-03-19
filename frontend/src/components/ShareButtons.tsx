interface Props {
  pairId: string;
  signalDate: string;
}

const BASE_URL = "https://leadlag.dev";

export function ShareButtons({ pairId, signalDate }: Props) {
  const pageUrl = encodeURIComponent(BASE_URL);
  const text = encodeURIComponent(
    `Today's cross-market signal (${signalDate}) - see where the US market move hits next`
  );
  const snapshotUrl = `${import.meta.env.VITE_DATA_BASE_URL || "/data"}/${pairId}/snapshot.png`;

  return (
    <div className="share-buttons">
      <a
        href={`https://www.reddit.com/submit?url=${pageUrl}&title=${text}`}
        target="_blank"
        rel="noopener noreferrer"
        className="share-btn share-reddit"
        title="Share on Reddit"
      >
        Reddit
      </a>
      <a
        href={`https://www.linkedin.com/sharing/share-offsite/?url=${pageUrl}`}
        target="_blank"
        rel="noopener noreferrer"
        className="share-btn share-linkedin"
        title="Share on LinkedIn"
      >
        LinkedIn
      </a>
      <a
        href={snapshotUrl}
        download={`market-signal-${pairId}-${signalDate}.png`}
        className="share-btn share-download"
        title="Download snapshot image"
      >
        PNG
      </a>
    </div>
  );
}
