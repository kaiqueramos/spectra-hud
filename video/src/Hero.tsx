import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  Sequence,
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

const INK = "#080a08";
const BONE = "#ece8dc";
const SIGNAL = "#ff5a1f";
const DIM = "#7a8276";
const LINE = "#242a22";
const MONO = '"IBM Plex Mono", monospace';
const COND = '"Barlow Condensed", sans-serif';
const BODY = '"Barlow", sans-serif';

const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

const Grain: React.FC = () => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      opacity: 0.05,
      pointerEvents: "none",
      backgroundImage:
        "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
    }}
  />
);

const Grid: React.FC<{ opacity?: number }> = ({ opacity = 0.16 }) => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      pointerEvents: "none",
      opacity,
      backgroundImage: `linear-gradient(${LINE} 1px, transparent 1px), linear-gradient(90deg, ${LINE} 1px, transparent 1px)`,
      backgroundSize: "40px 40px",
      maskImage:
        "radial-gradient(120% 90% at 50% 45%, #000 35%, transparent 100%)",
    }}
  />
);

const Corners: React.FC = () => {
  const s: React.CSSProperties = {
    position: "absolute",
    width: 26,
    height: 26,
    borderColor: SIGNAL,
    borderStyle: "solid",
    opacity: 0.55,
  };
  return (
    <>
      <div style={{ ...s, left: 34, top: 34, borderWidth: "1px 0 0 1px" }} />
      <div style={{ ...s, right: 34, top: 34, borderWidth: "1px 1px 0 0" }} />
      <div style={{ ...s, left: 34, bottom: 34, borderWidth: "0 0 1px 1px" }} />
      <div style={{ ...s, right: 34, bottom: 34, borderWidth: "0 1px 1px 0" }} />
    </>
  );
};

const Mark: React.FC<{ size?: number }> = ({ size = 34 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <path
      d="M3 8V3h5M16 3h5v5M21 16v5h-5M8 21H3v-5"
      fill="none"
      stroke={SIGNAL}
      strokeWidth="1.6"
    />
    <circle cx="12" cy="12" r="2.2" fill={SIGNAL} />
  </svg>
);

const HudChrome: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <>
      <div
        style={{
          position: "absolute",
          right: 64,
          top: 60,
          fontFamily: MONO,
          fontSize: 11,
          letterSpacing: "0.16em",
          color: DIM,
          textAlign: "right",
          lineHeight: 1.7,
        }}
      >
        <div>FRAME {String(frame).padStart(4, "0")} / 0600</div>
        <div>1920 × 1080 · 30 FPS</div>
      </div>

    </>
  );
};

const Caption: React.FC<{
  start: number;
  end: number;
  index: string;
  label: string;
  text: string;
}> = ({ start, end, index, label, text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame: frame - start, fps, config: { damping: 200 } });
  const exit = interpolate(frame, [end - 14, end], [1, 0], clamp);
  const y = interpolate(enter, [0, 1], [18, 0]);

  return (
    <div
      style={{
        position: "absolute",
        right: 88,
        top: 156,
        opacity: Math.min(enter, exit),
        transform: `translateY(${y}px)`,
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-start",
        gap: 10,
        maxWidth: 620,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          fontFamily: MONO,
          fontSize: 11,
          letterSpacing: "0.18em",
          color: SIGNAL,
        }}
      >
        <span>{index}</span>
        <span style={{ width: 36, height: 1, background: SIGNAL }} />
        <span style={{ color: DIM }}>{label}</span>
      </div>
      <div
        style={{
          fontFamily: COND,
          fontWeight: 700,
          fontSize: 42,
          lineHeight: 0.95,
          letterSpacing: "0.01em",
          textTransform: "uppercase",
          color: BONE,
          maxWidth: 620,
        }}
      >
        {text}
      </div>
    </div>
  );
};

const Title: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const line1 = spring({ frame: frame - 10, fps, config: { damping: 200 } });
  const line2 = spring({ frame: frame - 20, fps, config: { damping: 200 } });
  const fade = interpolate(frame, [0, 8, 74, 90], [0, 1, 1, 0], clamp);
  const y1 = interpolate(line1, [0, 1], [112, 0]);
  const y2 = interpolate(line2, [0, 1], [112, 0]);

  return (
    <div
      style={{
        position: "absolute",
        left: 88,
        top: 300,
        opacity: fade,
        maxWidth: 1100,
      }}
    >
      <div style={{ overflow: "hidden", paddingBottom: 4 }}>
        <div
          style={{
            transform: `translateY(${y1}%)`,
            fontFamily: COND,
            fontWeight: 700,
            fontSize: 148,
            lineHeight: 0.82,
            letterSpacing: "-0.01em",
            textTransform: "uppercase",
            color: BONE,
          }}
        >
          Your screen,
        </div>
      </div>
      <div style={{ overflow: "hidden", paddingBottom: 8 }}>
        <div
          style={{
            transform: `translateY(${y2}%)`,
            fontFamily: COND,
            fontWeight: 700,
            fontSize: 148,
            lineHeight: 0.82,
            letterSpacing: "-0.01em",
            textTransform: "uppercase",
            color: SIGNAL,
          }}
        >
          annotated.
        </div>
      </div>
    </div>
  );
};

const ScanSweep: React.FC = () => {
  const frame = useCurrentFrame();
  const top = interpolate(frame, [42, 76], [-40, 1120], clamp);
  const opacity = interpolate(frame, [42, 48, 70, 78], [0, 0.9, 0.9, 0], clamp);
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top,
        height: 1,
        background: SIGNAL,
        boxShadow: "0 0 18px rgba(255,90,31,.85)",
        opacity,
      }}
    />
  );
};

const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bg = interpolate(frame, [0, 12], [0, 1], clamp);
  const rise = spring({ frame: frame - 16, fps, config: { damping: 200 } });
  const sub = spring({ frame: frame - 26, fps, config: { damping: 200 } });
  const url = spring({ frame: frame - 36, fps, config: { damping: 200 } });
  const fadeOut = interpolate(frame, [160, 178], [1, 0], clamp);

  return (
    <AbsoluteFill style={{ background: INK, opacity: bg * fadeOut }}>
      <Grid opacity={0.22} />
      <Corners />
      <Grain />

      <div
        style={{
          position: "absolute",
          left: 96,
          top: 92,
          display: "flex",
          alignItems: "center",
          gap: 14,
          fontFamily: MONO,
          fontSize: 13,
          letterSpacing: "0.18em",
          color: BONE,
        }}
      >
        <Mark size={38} />
        SPECTRA <span style={{ color: DIM }}>HUD</span>
      </div>

      <div
        style={{
          position: "absolute",
          left: 96,
          top: 300,
          transform: `translateY(${interpolate(rise, [0, 1], [30, 0])}px)`,
          opacity: rise,
        }}
      >
        <div
          style={{
            fontFamily: COND,
            fontWeight: 700,
            fontSize: 124,
            lineHeight: 0.84,
            letterSpacing: "-0.01em",
            textTransform: "uppercase",
            color: BONE,
          }}
        >
          Your screen,
          <br />
          <span style={{ color: SIGNAL }}>annotated.</span>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 100,
          top: 560,
          opacity: sub,
          transform: `translateY(${interpolate(sub, [0, 1], [16, 0])}px)`,
          fontFamily: BODY,
          fontSize: 26,
          color: "#c9c6ba",
          maxWidth: 700,
          lineHeight: 1.45,
        }}
      >
        A screen-aware HUD for Linux. One hotkey, three anchored cards,
        no server.
      </div>

      <div
        style={{
          position: "absolute",
          left: 100,
          top: 690,
          opacity: url,
          transform: `translateY(${interpolate(url, [0, 1], [16, 0])}px)`,
          display: "flex",
          alignItems: "center",
          gap: 18,
        }}
      >
        <div
          style={{
            border: `1px solid ${SIGNAL}`,
            color: SIGNAL,
            fontFamily: MONO,
            fontSize: 14,
            letterSpacing: "0.08em",
            padding: "14px 20px",
          }}
        >
          github.com/kaiqueramos/spectra-hud
        </div>
        <div
          style={{
            fontFamily: MONO,
            fontSize: 11,
            letterSpacing: "0.14em",
            color: DIM,
          }}
        >
          APACHE 2.0 · LINUX / X11 · BYOK
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          right: 150,
          top: 210,
          width: 520,
          height: 520,
          opacity: rise,
        }}
      >
        <div style={{ position: "absolute", inset: 0, border: `1px solid ${LINE}` }} />
        <div style={{ position: "absolute", left: "50%", top: 0, width: 1, height: "100%", background: LINE }} />
        <div style={{ position: "absolute", top: "50%", left: 0, height: 1, width: "100%", background: LINE }} />
        {[
          { left: 0, top: 0, borderWidth: "2px 0 0 2px" },
          { right: 0, top: 0, borderWidth: "2px 2px 0 0" },
          { left: 0, bottom: 0, borderWidth: "0 0 2px 2px" },
          { right: 0, bottom: 0, borderWidth: "0 2px 2px 0" },
        ].map((corner, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              width: 64,
              height: 64,
              borderColor: SIGNAL,
              borderStyle: "solid",
              ...corner,
            }}
          />
        ))}
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            width: 12,
            height: 12,
            background: SIGNAL,
            transform: "translate(-50%, -50%)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 0,
            bottom: -32,
            fontFamily: MONO,
            fontSize: 10,
            letterSpacing: "0.18em",
            color: DIM,
          }}
        >
          SPECTRA / HUD
        </div>
        <div
          style={{
            position: "absolute",
            right: 0,
            top: -32,
            fontFamily: MONO,
            fontSize: 10,
            letterSpacing: "0.18em",
            color: DIM,
          }}
        >
          DISPLAY 1
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          right: 96,
          bottom: 92,
          fontFamily: MONO,
          fontSize: 10,
          letterSpacing: "0.18em",
          color: DIM,
        }}
      >
        v0.1.0 / 2026
      </div>
    </AbsoluteFill>
  );
};

export const Hero: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const zoom = interpolate(frame, [0, 180, 420], [1.0, 1.02, 1.03], clamp);
  const tx = 0;
  const ty = 0;

  const fadeIn = interpolate(frame, [0, 10], [0, 1], clamp);
  const scrim = interpolate(frame, [0, 10, 70, 92], [0, 0.92, 0.92, 0], clamp);

  return (
    <AbsoluteFill style={{ background: INK }}>
      <AbsoluteFill style={{ opacity: fadeIn }}>
        <div
          style={{
            position: "absolute",
            inset: 0,
            transform: `scale(${zoom}) translate(${tx}px, ${ty}px)`,
            transformOrigin: "58% 42%",
          }}
        >
          <OffthreadVideo
            src={staticFile("footage.mp4")}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </div>

        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "linear-gradient(90deg, rgba(8,10,8,0.94) 0%, rgba(8,10,8,0.72) 34%, rgba(8,10,8,0.12) 62%, rgba(8,10,8,0.35) 100%)",
            opacity: scrim,
            pointerEvents: "none",
          }}
        />

        <Grid opacity={0.10} />
        <ScanSweep />
        <HudChrome />
        <Title />

        <Caption
          start={60}
          end={120}
          index="01"
          label="SCAN"
          text="One hotkey. Three points."
        />
        <Caption
          start={120}
          end={186}
          index="02"
          label="ASK"
          text="Click a card. Go deeper."
        />
        <Caption
          start={186}
          end={306}
          index="03"
          label="ANSWER"
          text="In place, not in a chat."
        />
        <Caption
          start={306}
          end={408}
          index="04"
          label="PRIVACY"
          text="No server. Your key."
        />

        <Grain />
        <Corners />
      </AbsoluteFill>

      <Sequence from={420} durationInFrames={180}>
        <EndCard />
      </Sequence>

      <div
        style={{
          position: "absolute",
          inset: 0,
          background: INK,
          opacity: interpolate(frame, [0, 8], [1, 0], clamp),
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
