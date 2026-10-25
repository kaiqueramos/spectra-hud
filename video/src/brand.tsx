import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { loadFont } from "@remotion/fonts";

loadFont({
  family: "Barlow Condensed",
  url: staticFile("fonts/barlow-condensed-700.woff2"),
  weight: "700",
});
loadFont({
  family: "Barlow",
  url: staticFile("fonts/barlow-400.woff2"),
  weight: "400",
});
loadFont({
  family: "Barlow",
  url: staticFile("fonts/barlow-500.woff2"),
  weight: "500",
});
loadFont({
  family: "IBM Plex Mono",
  url: staticFile("fonts/ibm-plex-mono-400.woff2"),
  weight: "400",
});
loadFont({
  family: "IBM Plex Mono",
  url: staticFile("fonts/ibm-plex-mono-500.woff2"),
  weight: "500",
});

export const INK = "#080a08";
export const BONE = "#ece8dc";
export const SIGNAL = "#ff5a1f";
export const DIM = "#7a8276";
export const LINE = "#242a22";
export const PANEL = "#0d110d";
export const MONO = '"IBM Plex Mono", monospace';
export const COND = '"Barlow Condensed", sans-serif';
export const BODY = '"Barlow", sans-serif';

export const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

export const fade = (
  frame: number,
  start: number,
  end: number,
  from = 0,
  to = 1,
) => interpolate(frame, [start, end], [from, to], clamp);

export const Grain: React.FC = () => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      opacity: 0.055,
      pointerEvents: "none",
      backgroundImage:
        "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
    }}
  />
);

export const Grid: React.FC<{ opacity?: number }> = ({ opacity = 0.14 }) => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      opacity,
      pointerEvents: "none",
      backgroundImage: `linear-gradient(${LINE} 1px, transparent 1px), linear-gradient(90deg, ${LINE} 1px, transparent 1px)`,
      backgroundSize: "48px 48px",
      maskImage: "radial-gradient(120% 90% at 55% 45%, #000 30%, transparent 100%)",
    }}
  />
);

export const Scanlines: React.FC<{ opacity?: number }> = ({ opacity = 0.05 }) => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      opacity,
      pointerEvents: "none",
      backgroundImage:
        "repeating-linear-gradient(0deg, rgba(255,255,255,.7) 0px, rgba(255,255,255,.7) 1px, transparent 1px, transparent 4px)",
    }}
  />
);

export const Corners: React.FC<{ color?: string; inset?: number }> = ({
  color = SIGNAL,
  inset = 34,
}) => {
  const s: React.CSSProperties = {
    position: "absolute",
    width: 28,
    height: 28,
    borderColor: color,
    borderStyle: "solid",
    opacity: 0.6,
  };
  return (
    <>
      <div style={{ ...s, left: inset, top: inset, borderWidth: "1px 0 0 1px" }} />
      <div style={{ ...s, right: inset, top: inset, borderWidth: "1px 1px 0 0" }} />
      <div style={{ ...s, left: inset, bottom: inset, borderWidth: "0 0 1px 1px" }} />
      <div style={{ ...s, right: inset, bottom: inset, borderWidth: "0 1px 1px 0" }} />
    </>
  );
};

export const Backdrop: React.FC<{ grid?: number; corners?: boolean }> = ({
  grid = 0.14,
  corners = true,
}) => (
  <AbsoluteFill style={{ background: INK }}>
    <Grid opacity={grid} />
    <div
      style={{
        position: "absolute",
        inset: 0,
        background:
          "radial-gradient(90% 70% at 58% 36%, rgba(255,90,31,.055) 0%, transparent 60%), radial-gradient(80% 80% at 20% 90%, rgba(168,184,148,.035) 0%, transparent 55%)",
      }}
    />
    {corners && <Corners />}
    <Scanlines />
    <Grain />
  </AbsoluteFill>
);

export const Mark: React.FC<{ size?: number; color?: string }> = ({
  size = 38,
  color = SIGNAL,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <path
      d="M3 8V3h5M16 3h5v5M21 16v5h-5M8 21H3v-5"
      fill="none"
      stroke={color}
      strokeWidth="1.6"
    />
    <circle cx="12" cy="12" r="2.2" fill={color} />
  </svg>
);

export const Wordmark: React.FC<{ size?: number; sub?: string }> = ({
  size = 26,
  sub,
}) => (
  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
    <Mark size={size * 1.2} />
    <div
      style={{
        fontFamily: COND,
        fontSize: size,
        letterSpacing: "0.16em",
        color: BONE,
        lineHeight: 1,
      }}
    >
      SPECTRA
    </div>
    {sub && (
      <div
        style={{
          fontFamily: MONO,
          fontSize: size * 0.36,
          letterSpacing: "0.2em",
          color: DIM,
          textTransform: "uppercase",
        }}
      >
        {sub}
      </div>
    )}
  </div>
);

export const Kicker: React.FC<{ children: React.ReactNode; color?: string }> = ({
  children,
  color = SIGNAL,
}) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 10,
      fontFamily: MONO,
      fontSize: 13,
      letterSpacing: "0.2em",
      textTransform: "uppercase",
      color,
    }}
  >
    <span
      style={{
        width: 7,
        height: 7,
        borderRadius: "50%",
        background: color,
        boxShadow: `0 0 16px ${color}`,
      }}
    />
    {children}
  </div>
);

export const FeatureChip: React.FC<{
  children: React.ReactNode;
  color?: string;
  active?: boolean;
}> = ({ children, color = SIGNAL, active = false }) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 8,
      padding: "9px 13px",
      border: `1px solid ${active ? color : LINE}`,
      background: active ? `${color}18` : "rgba(13,17,13,.8)",
      color: active ? color : DIM,
      fontFamily: MONO,
      fontSize: 12,
      letterSpacing: "0.13em",
      textTransform: "uppercase",
    }}
  >
    <span
      style={{
        width: 5,
        height: 5,
        background: active ? color : DIM,
        borderRadius: "50%",
      }}
    />
    {children}
  </div>
);

export const Keycap: React.FC<{
  children: React.ReactNode;
  active?: boolean;
  scale?: number;
}> = ({ children, active = false, scale = 1 }) => (
  <div
    style={{
      padding: "10px 15px",
      border: `1px solid ${active ? SIGNAL : "#394134"}`,
      background: active ? "rgba(255,90,31,.13)" : "rgba(8,10,8,.7)",
      boxShadow: active
        ? "0 0 24px rgba(255,90,31,.18), inset 0 1px 0 rgba(255,255,255,.06)"
        : "inset 0 1px 0 rgba(255,255,255,.04)",
      color: active ? SIGNAL : BONE,
      fontFamily: MONO,
      fontSize: 12,
      letterSpacing: "0.08em",
      transform: `scale(${scale})`,
    }}
  >
    {children}
  </div>
);

export const ChipRow: React.FC<{ items: string[]; y: number; active?: number }> = ({
  items,
  y,
  active = -1,
}) => (
  <div
    style={{
      position: "absolute",
      left: 130,
      top: y,
      display: "flex",
      gap: 9,
    }}
  >
    {items.map((item, i) => (
      <FeatureChip key={item} active={i === active}>
        {item}
      </FeatureChip>
    ))}
  </div>
);

const CODE_LINES = [
  ["38", "def settle(payment):", BONE],
  ["39", "    ledger = load(payment.id)", BONE],
  ["40", "    if ledger.closed:", BONE],
  ["41", '        return "skipped"', BONE],
  ["42", "    return payment.user.id", "#ffb394"],
  ["43", "    commit(ledger)", BONE],
];

export const CodeEditor: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  scan?: number;
  highlight?: number;
}> = ({ x, y, w, h, scan = 1, highlight = 1 }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: w,
      height: h,
      background: "rgba(10,13,9,.96)",
      border: `1px solid ${LINE}`,
      boxShadow: "0 32px 100px rgba(0,0,0,.5)",
      overflow: "hidden",
    }}
  >
    <div
      style={{
        height: 42,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 16px",
        borderBottom: `1px solid ${LINE}`,
        background: "#111610",
        fontFamily: MONO,
        fontSize: 12,
        color: DIM,
      }}
    >
      <span>payment_service.py</span>
      <span>UTF-8</span>
    </div>
    <div style={{ padding: "30px 24px", position: "relative" }}>
      {highlight > 0 && (
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: 30 + 4 * 35 - 5,
            height: 32,
            background: "rgba(255,90,31,.09)",
            opacity: highlight,
          }}
        />
      )}
      {CODE_LINES.map(([num, code, color], i) => (
        <div
          key={num}
          style={{
            display: "flex",
            gap: 26,
            height: 35,
            alignItems: "center",
            fontFamily: MONO,
            fontSize: 19,
            color,
            position: "relative",
          }}
        >
          <span style={{ color: "#4e564b", width: 25, textAlign: "right" }}>{num}</span>
          <span>{code}</span>
          {num === "42" && (
            <span
              style={{
                position: "absolute",
                left: -24,
                top: 5,
                width: 4,
                height: 25,
                background: SIGNAL,
                boxShadow: "0 0 16px rgba(255,90,31,.55)",
                opacity: highlight,
              }}
            />
          )}
        </div>
      ))}
    </div>
    {scan > 0 && (
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: `${Math.min(98, Math.max(0, scan * 100))}%`,
          height: 2,
          background:
            "linear-gradient(90deg, transparent, rgba(255,90,31,.8), transparent)",
          boxShadow: "0 0 22px rgba(255,90,31,.45)",
        }}
      />
    )}
  </div>
);

export const DialogBox: React.FC<{ x: number; y: number; w?: number; opacity?: number }> = ({
  x,
  y,
  w = 560,
  opacity = 1,
}) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: w,
      background: "rgba(13,17,13,.98)",
      border: `1px solid ${LINE}`,
      boxShadow: "0 30px 90px rgba(0,0,0,.55)",
      opacity,
    }}
  >
    <div
      style={{
        height: 36,
        display: "flex",
        alignItems: "center",
        padding: "0 14px",
        borderBottom: `1px solid ${LINE}`,
        fontFamily: MONO,
        fontSize: 11,
        color: DIM,
      }}
    >
      Confirm retry
    </div>
    <div style={{ padding: "26px 22px 20px" }}>
      <div style={{ fontFamily: BODY, fontSize: 25, color: BONE, lineHeight: 1.25 }}>
        The previous request timed out.
      </div>
      <div style={{ fontFamily: BODY, fontSize: 19, color: DIM, marginTop: 10 }}>
        Retry the settlement for #1042?
      </div>
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 32 }}>
        {["Cancel", "Retry"].map((label, i) => (
          <div
            key={label}
            style={{
              padding: "11px 20px",
              border: `1px solid ${i ? SIGNAL : "#394134"}`,
              color: i ? SIGNAL : DIM,
              background: i ? "rgba(255,90,31,.07)" : "transparent",
              fontFamily: BODY,
              fontSize: 16,
            }}
          >
            {label}
          </div>
        ))}
      </div>
    </div>
  </div>
);

export const QueuePanel: React.FC<{ x: number; y: number; w?: number }> = ({
  x,
  y,
  w = 620,
}) => {
  const rows = [
    ["#1041", "settle", BONE],
    ["#1042", "settle", BONE],
    ["#1043", "settle", SIGNAL],
    ["#1044", "retry", BONE],
  ];
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: w,
        background: "rgba(13,17,13,.96)",
        border: `1px solid ${LINE}`,
      }}
    >
      <div
        style={{
          height: 36,
          display: "flex",
          alignItems: "center",
          padding: "0 14px",
          borderBottom: `1px solid ${LINE}`,
          fontFamily: MONO,
          fontSize: 11,
          color: DIM,
        }}
      >
        Queue
      </div>
      {rows.map(([id, action, color], i) => (
        <div
          key={id}
          style={{
            display: "flex",
            justifyContent: "space-between",
            padding: "9px 14px",
            borderBottom: i < rows.length - 1 ? "1px solid rgba(36,42,34,.6)" : "none",
            fontFamily: MONO,
            fontSize: 14,
            color,
          }}
        >
          <span>{id}</span>
          <span>{action}</span>
        </div>
      ))}
    </div>
  );
};

export const HudCard: React.FC<{
  x: number;
  y: number;
  w?: number;
  tag: string;
  title: string;
  body: string;
  color?: string;
  delay?: number;
  index?: string;
}> = ({ x, y, w = 430, tag, title, body, color = SIGNAL, delay = 0, index = "01" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({
    frame: frame - delay,
    fps,
    config: { damping: 18, stiffness: 90, mass: 0.9 },
  });
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: w,
        background: PANEL,
        border: `1px solid ${color}`,
        boxShadow: `0 24px 70px rgba(0,0,0,.55), 0 0 36px ${color}12`,
        opacity: p,
        transform: `translateY(${(1 - p) * 34}px) scale(${0.96 + p * 0.04})`,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          height: 38,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: `1px solid ${LINE}`,
          background: "#111610",
          padding: "0 12px",
          fontFamily: MONO,
          fontSize: 11,
        }}
      >
        <span style={{ color, letterSpacing: "0.12em" }}>▲ {tag}</span>
        <span style={{ color: DIM }}>{index}</span>
      </div>
      <div style={{ padding: "20px 18px 18px" }}>
        <div style={{ fontFamily: COND, fontSize: 27, color: BONE, letterSpacing: "0.02em" }}>
          {title}
        </div>
        <div
          style={{
            fontFamily: BODY,
            fontSize: 19,
            lineHeight: 1.35,
            color: "#c9c6ba",
            marginTop: 9,
          }}
        >
          {body}
        </div>
      </div>
      <div
        style={{
          borderTop: `1px solid ${LINE}`,
          padding: "9px 12px",
          fontFamily: MONO,
          fontSize: 9,
          letterSpacing: "0.12em",
          color: DIM,
        }}
      >
        CLICK TO ASK · DRAG TO MOVE
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: 4,
          background: color,
        }}
      />
    </div>
  );
};

export const Cursor: React.FC<{ x: number; y: number; click?: number }> = ({
  x,
  y,
  click = 0,
}) => (
  <div style={{ position: "absolute", left: x, top: y, pointerEvents: "none" }}>
    {click > 0 && (
      <div
        style={{
          position: "absolute",
          left: -22,
          top: -22,
          width: 44,
          height: 44,
          borderRadius: "50%",
          border: `1px solid ${SIGNAL}`,
          opacity: click,
          transform: `scale(${0.5 + (1 - click) * 1.5})`,
        }}
      />
    )}
    <svg width="27" height="34" viewBox="0 0 27 34">
      <path
        d="M2 2l7.5 27 4-10 10-4L2 2z"
        fill={BONE}
        stroke={INK}
        strokeWidth="1.8"
      />
    </svg>
  </div>
);

export const ScanSweep: React.FC<{ top: number; opacity?: number }> = ({
  top,
  opacity = 1,
}) => (
  <div
    style={{
      position: "absolute",
      left: 0,
      right: 0,
      top,
      height: 2,
      opacity,
      background:
        "linear-gradient(90deg, transparent 2%, rgba(255,90,31,.15) 12%, rgba(255,90,31,.9) 50%, rgba(255,90,31,.15) 88%, transparent 98%)",
      boxShadow: "0 0 32px rgba(255,90,31,.45)",
    }}
  />
);

export const CommandCenterImage: React.FC<{
  src: string;
  x: number;
  y: number;
  w: number;
  scale?: number;
  opacity?: number;
}> = ({ src, x, y, w, scale = 1, opacity = 1 }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: w,
      opacity,
      transform: `scale(${scale})`,
      transformOrigin: "50% 50%",
      filter: "drop-shadow(0 40px 80px rgba(0,0,0,.55))",
    }}
  >
    <div
      style={{
        border: `1px solid #394134`,
        background: "#0a0d09",
        padding: 5,
        boxShadow: "0 0 70px rgba(255,90,31,.08)",
      }}
    >
      <Img src={staticFile(src)} style={{ width: "100%", display: "block" }} />
    </div>
    <div
      style={{
        position: "absolute",
        left: 0,
        top: -27,
        fontFamily: MONO,
        fontSize: 10,
        letterSpacing: "0.18em",
        color: DIM,
      }}
    >
      SPECTRA / COMMAND CENTER
    </div>
    <div
      style={{
        position: "absolute",
        right: 0,
        bottom: -27,
        fontFamily: MONO,
        fontSize: 10,
        letterSpacing: "0.18em",
        color: DIM,
      }}
    >
      X11 · LIVE
    </div>
  </div>
);

export const Terminal: React.FC<{
  lines: string[];
  x: number;
  y: number;
  w?: number;
  opacity?: number;
}> = ({ lines, x, y, w = 700, opacity = 1 }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: w,
      border: `1px solid ${LINE}`,
      background: "rgba(8,10,8,.92)",
      padding: "18px 20px",
      fontFamily: MONO,
      fontSize: 15,
      lineHeight: 1.8,
      color: DIM,
      opacity,
      boxShadow: "0 20px 60px rgba(0,0,0,.35)",
    }}
  >
    {lines.map((line, i) => (
      <div key={i} style={{ color: line.startsWith("$") ? SIGNAL : i === lines.length - 1 ? "#a8b894" : DIM }}>
        {line}
      </div>
    ))}
  </div>
);

export const SceneTitle: React.FC<{
  children: React.ReactNode;
  x?: number;
  y?: number;
  size?: number;
  color?: string;
}> = ({ children, x = 110, y = 110, size = 92, color = BONE }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      fontFamily: COND,
      fontSize: size,
      lineHeight: 0.92,
      letterSpacing: "-0.01em",
      color,
      textTransform: "uppercase",
    }}
  >
    {children}
  </div>
);

export const Divider: React.FC<{ x: number; y: number; w: number }> = ({ x, y, w }) => (
  <div style={{ position: "absolute", left: x, top: y, width: w, height: 1, background: LINE }} />
);
