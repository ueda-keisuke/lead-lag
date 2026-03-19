import { useState } from "react";

interface Props {
  text: string;
}

export function Tooltip({ text }: Props) {
  const [visible, setVisible] = useState(false);

  return (
    <span
      className="tooltip-wrapper"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onClick={() => setVisible((v) => !v)}
    >
      <span className="tooltip-trigger">?</span>
      {visible && <span className="tooltip-content">{text}</span>}
    </span>
  );
}
