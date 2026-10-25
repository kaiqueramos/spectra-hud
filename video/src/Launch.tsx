import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  Backdrop,
  BONE,
  BODY,
  COND,
  CodeEditor,
  CommandCenterImage,
  Corners,
  Cursor,
  DIM,
  DialogBox,
  FeatureChip,
  Grid,
  HudCard,
  INK,
  Keycap,
  Kicker,
  LINE,
  MONO,
  Mark,
  QueuePanel,
  SIGNAL,
  ScanSweep,
  Terminal,
  clamp,
  fade,
} from "./brand";

const SceneFade: React.FC<{
  duration: number;
  children: React.ReactNode;
  background?: string;
}> = ({ duration, children, background = "transparent" }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [0, 12, duration - 12, duration],
    [0, 1, 1, 0],
    clamp,
  );
  return <AbsoluteFill style={{ opacity, background }}>{children}</AbsoluteFill>;
};

const Chapter: React.FC<{ index: string; label: string; color?: string }> = ({
  index,
  label,
  color = DIM,
}) => (
  <div
    style={{
      position: "absolute",
      left: 110,
      top: 62,
      display: "flex",
      alignItems: "center",
      gap: 12,
      fontFamily: MONO,
      fontSize: 11,
      letterSpacing: "0.2em",
      color,
    }}
  >
    <span style={{ color: SIGNAL }}>{index}</span>
    <span style={{ width: 30, height: 1, background: LINE }} />
    <span>{label}</span>
  </div>
);

const Manifesto: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const lines = ["EVERY SCREEN", "HAS A NEXT MOVE."];
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.2} />
      <div
        style={{
          position: "absolute",
          left: 110,
          top: 160,
          fontFamily: COND,
          fontSize: 154,
          lineHeight: 0.88,
          letterSpacing: "-0.015em",
          color: BONE,
          textTransform: "uppercase",
        }}
      >
        {lines.map((line, li) => (
          <div key={line} style={{ display: "flex", gap: 18 }}>
            {line.split(" ").map((word, wi) => {
              const p = spring({
                frame: frame - 5 - li * 10 - wi * 4,
                fps,
                config: { damping: 18, stiffness: 110, mass: 0.7 },
              });
              return (
                <span
                  key={wi}
                  style={{
                    display: "inline-block",
                    opacity: p,
                    transform: `translateY(${(1 - p) * 70}px)`,
                  }}
                >
                  {word}
                </span>
              );
            })}
          </div>
        ))}
      </div>
      <div
        style={{
          position: "absolute",
          left: 118,
          bottom: 170,
          fontFamily: BODY,
          fontSize: 25,
          color: DIM,
          opacity: fade(frame, 38, 55),
        }}
      >
        The interface was never the app.
      </div>
      <div
        style={{
          position: "absolute",
          left: 110,
          bottom: 108,
          display: "flex",
          gap: 10,
          opacity: fade(frame, 25, 45),
        }}
      >
        <FeatureChip active>LINUX / X11</FeatureChip>
        <FeatureChip>OPEN SOURCE</FeatureChip>
        <FeatureChip>BRING YOUR OWN KEY</FeatureChip>
      </div>
      <div style={{ position: "absolute", right: 130, top: 190, opacity: 0.09 }}>
        <Mark size={420} />
      </div>
      <ScanSweep top={interpolate(frame, [0, 90], [180, 880], clamp)} opacity={0.35} />
    </AbsoluteFill>
  );
};

const TypeReveal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p1 = spring({ frame: frame - 4, fps, config: { damping: 20, stiffness: 90 } });
  const p2 = spring({ frame: frame - 18, fps, config: { damping: 20, stiffness: 90 } });
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.12} />
      <div style={{ position: "absolute", inset: 0, opacity: 0.16 }}>
        <CodeEditor x={-140} y={210} w={1500} h={760} scan={0} highlight={0.25} />
      </div>
      <div style={{ position: "absolute", inset: 0, background: "linear-gradient(90deg, #080a08 0%, rgba(8,10,8,.94) 48%, rgba(8,10,8,.25) 100%)" }} />
      <Chapter index="02" label="THE SCREEN" />
      <div
        style={{
          position: "absolute",
          left: 108,
          top: 230,
          fontFamily: COND,
          fontSize: 188,
          lineHeight: 0.84,
          letterSpacing: "-0.02em",
          color: BONE,
          textTransform: "uppercase",
        }}
      >
        <div style={{ opacity: p1, transform: `translateX(${(1 - p1) * -80}px)` }}>
          YOUR SCREEN.
        </div>
        <div style={{ opacity: p2, transform: `translateX(${(1 - p2) * -80}px)`, color: SIGNAL }}>
          IS THE INTERFACE.
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: 118,
          top: 650,
          fontFamily: BODY,
          fontSize: 29,
          color: DIM,
          maxWidth: 560,
          opacity: fade(frame, 36, 52),
        }}
      >
        No copy. No paste. No tab hunting. Spectra reads what is on screen and puts the next move where it belongs.
      </div>
      <div
        style={{
          position: "absolute",
          left: 118,
          bottom: 120,
          display: "flex",
          gap: 10,
          opacity: fade(frame, 52, 66),
        }}
      >
        <Keycap active>CTRL</Keycap>
        <span style={{ color: DIM, fontFamily: MONO, alignSelf: "center" }}>+</span>
        <Keycap active>ALT</Keycap>
        <span style={{ color: DIM, fontFamily: MONO, alignSelf: "center" }}>+</span>
        <Keycap active>SPACE</Keycap>
      </div>
      <div style={{ position: "absolute", right: 120, top: 280, opacity: 0.07 }}>
        <Mark size={380} />
      </div>
      <ScanSweep top={interpolate(frame, [0, 180], [130, 980], clamp)} opacity={0.22} />
    </AbsoluteFill>
  );
};

const ProductDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(frame, [0, 240], [1.0, 1.05], clamp);
  const scan = interpolate(frame, [12, 20, 74, 82], [0, 1, 1, 0], clamp);
  const scanY = interpolate(frame, [12, 78], [190, 900], clamp);
  const title = spring({ frame: frame - 4, fps, config: { damping: 20, stiffness: 90 } });
  const click = interpolate(frame, [140, 148, 168], [0, 1, 0], clamp);
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.12} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `scale(${zoom}) translateX(-10px)`,
          transformOrigin: "58% 55%",
        }}
      >
        <CodeEditor x={620} y={250} w={800} h={520} scan={scan} />
        <DialogBox x={1500} y={700} w={360} opacity={fade(frame, 25, 45)} />
        <QueuePanel x={610} y={820} w={470} />
        <HudCard
          x={1450}
          y={165}
          w={390}
          tag="ALERT"
          title="EARLY RETURN BUG"
          body="The return happens before the commit. The settlement is never saved."
          delay={46}
          index="01"
        />
        <HudCard
          x={1450}
          y={440}
          w={390}
          tag="ACTION"
          title="DON'T RETRY"
          body="Retry reruns the same broken path. Cancel and fix the return first."
          color={BONE}
          delay={72}
          index="02"
        />
        <HudCard
          x={1080}
          y={820}
          w={390}
          tag="ITEM"
          title="QUEUE BACKING UP"
          body="#1043 keeps failing on the same settle path."
          color="#a8b894"
          delay={98}
          index="03"
        />
        <ScanSweep top={scanY} opacity={scan} />
        <Cursor x={1330} y={500} click={click} />
      </div>
      <Chapter index="03" label="THE HUD" />
      <div style={{ position: "absolute", left: 108, top: 118, opacity: title }}>
        <Kicker>ONE SCAN / THREE ANCHORS</Kicker>
        <div
          style={{
            fontFamily: COND,
            fontSize: 96,
            lineHeight: 0.88,
            color: BONE,
            textTransform: "uppercase",
            marginTop: 14,
          }}
        >
          One hotkey.
          <br />
          Three moves.
        </div>
        <div style={{ fontFamily: BODY, fontSize: 22, color: DIM, marginTop: 14, maxWidth: 430 }}>
          Each card knows where it belongs. Click one to ask. Drag it if it is in the way.
        </div>
        <div style={{ display: "flex", gap: 9, marginTop: 24 }}>
          <FeatureChip active>ANCHORED</FeatureChip>
          <FeatureChip>CANCELABLE</FeatureChip>
          <FeatureChip>FOLLOW-UP</FeatureChip>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Command: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 4, fps, config: { damping: 20, stiffness: 80 } });
  const toPaper = fade(frame, 64, 92);
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.1} />
      <Chapter index="04" label="THE CONTROL ROOM" />
      <div style={{ position: "absolute", left: 108, top: 170 }}>
        <div
          style={{
            fontFamily: COND,
            fontSize: 126,
            lineHeight: 0.85,
            color: BONE,
            textTransform: "uppercase",
            opacity: p,
            transform: `translateY(${(1 - p) * 35}px)`,
          }}
        >
          YOUR HUD.
          <br />
          <span style={{ color: SIGNAL }}>YOUR RULES.</span>
        </div>
        <div style={{ fontFamily: BODY, fontSize: 24, color: DIM, marginTop: 24, maxWidth: 760 }}>
          Ten themes. Three languages. A YAML file for every setting. A command center that stays out of your way.
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            gap: 9,
            marginTop: 36,
          }}
        >
          <FeatureChip active>10 THEMES / 5 DARK / 5 LIGHT</FeatureChip>
          <FeatureChip active>PT-BR · EN · ES</FeatureChip>
          <FeatureChip active>YAML / RELOAD</FeatureChip>
          <FeatureChip>TRAY / HOTKEYS / TELEMETRY</FeatureChip>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          right: 96,
          top: 104,
          width: 820,
          height: 900,
          opacity: p,
          transform: `translateY(${(1 - p) * 30}px) scale(${0.98 + p * 0.02})`,
        }}
      >
        <CommandCenterImage
          src="command-center-spectra.png"
          x={0}
          y={0}
          w={800}
          opacity={1 - toPaper}
        />
        <CommandCenterImage
          src="command-center-paper.png"
          x={0}
          y={0}
          w={800}
          opacity={toPaper}
        />
      </div>
      <div
        style={{
          position: "absolute",
          right: 120,
          bottom: 74,
          fontFamily: MONO,
          fontSize: 11,
          letterSpacing: "0.18em",
          color: DIM,
        }}
      >
        {toPaper > 0.5 ? "PAPER / LIGHT / 01 OF 10" : "SPECTRA / DARK / 01 OF 10"}
      </div>
    </AbsoluteFill>
  );
};

const Shield: React.FC<{ frame: number; fps: number }> = ({ frame, fps }) => {
  const p = spring({ frame: frame - 4, fps, config: { damping: 18, stiffness: 80 } });
  const dash = interpolate(frame, [10, 55], [0, 1], clamp);
  return (
    <svg width={430} height={500} viewBox="0 0 430 500" style={{ opacity: p, transform: `translateY(${(1 - p) * 40}px)` }}>
      <path
        d="M215 24l158 58v144c0 108-64 196-158 250C121 422 57 334 57 226V82l158-58z"
        fill="rgba(255,90,31,.045)"
        stroke={SIGNAL}
        strokeWidth="1.5"
        strokeDasharray="900"
        strokeDashoffset={900 * (1 - dash)}
      />
      <path
        d="M215 68l118 43v115c0 82-47 149-118 193-71-44-118-111-118-193V111l118-43z"
        fill="none"
        stroke="rgba(255,90,31,.35)"
        strokeWidth="1"
      />
      <rect x="170" y="218" width="90" height="78" rx="6" fill="none" stroke={BONE} strokeWidth="2" />
      <path d="M188 218v-18a27 27 0 0154 0v18" fill="none" stroke={BONE} strokeWidth="2" />
      <circle cx="215" cy="252" r="7" fill={SIGNAL} />
      <path d="M215 259v18" stroke={SIGNAL} strokeWidth="2" />
    </svg>
  );
};

const Trust: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.12} />
      <Chapter index="05" label="THE BOUNDARY" />
      <div style={{ position: "absolute", left: 108, top: 150 }}>
        <Kicker>PRIVACY / BY DESIGN</Kicker>
        <div
          style={{
            fontFamily: COND,
            fontSize: 138,
            lineHeight: 0.84,
            color: BONE,
            textTransform: "uppercase",
            marginTop: 18,
          }}
        >
          No telemetry.
          <br />
          No account.
          <br />
          <span style={{ color: SIGNAL }}>Your key.</span>
        </div>
        <div style={{ fontFamily: BODY, fontSize: 24, color: DIM, marginTop: 26, maxWidth: 620 }}>
          Your screenshot goes only to the provider you choose. The key stays in the system keyring. Local models are one preset away.
        </div>
        <div style={{ display: "flex", gap: 9, marginTop: 34, flexWrap: "wrap", maxWidth: 760 }}>
          <FeatureChip active>CONSENT FIRST</FeatureChip>
          <FeatureChip active>PRIVATE MODE</FeatureChip>
          <FeatureChip active>WINDOW BLOCKLIST</FeatureChip>
          <FeatureChip>KEYRING</FeatureChip>
          <FeatureChip>LOCAL MODELS</FeatureChip>
        </div>
      </div>
      <div style={{ position: "absolute", right: 170, top: 240 }}>
        <Shield frame={frame} fps={fps} />
        <div
          style={{
            position: "absolute",
            left: -38,
            right: -38,
            bottom: 8,
            textAlign: "center",
            fontFamily: MONO,
            fontSize: 11,
            lineHeight: 1.8,
            letterSpacing: "0.14em",
            color: DIM,
          }}
        >
          NO SPECTRA SERVER
          <br />
          <span style={{ color: BONE }}>ONLY THE PROVIDER YOU POINT AT</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Proof: React.FC = () => {
  const frame = useCurrentFrame();
  const count = Math.round(interpolate(frame, [10, 55], [0, 61], clamp));
  const p = spring({ frame: frame - 4, fps: 30, config: { damping: 20, stiffness: 80 } });
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.12} />
      <Chapter index="06" label="THE RECEIPTS" />
      <div style={{ position: "absolute", left: 108, top: 132 }}>
        <Kicker>OPEN SOURCE / APACHE 2.0</Kicker>
        <div
          style={{
            fontFamily: COND,
            fontSize: 126,
            lineHeight: 0.86,
            color: BONE,
            textTransform: "uppercase",
            marginTop: 14,
          }}
        >
          Built in public.
          <br />
          <span style={{ color: SIGNAL }}>Tested in public.</span>
        </div>
      </div>
      <div style={{ position: "absolute", left: 108, top: 460, display: "flex", alignItems: "flex-end", gap: 24 }}>
        <div
          style={{
            fontFamily: COND,
            fontSize: 300,
            lineHeight: 0.7,
            color: SIGNAL,
            opacity: p,
            transform: `translateY(${(1 - p) * 30}px)`,
          }}
        >
          {count}
        </div>
        <div style={{ fontFamily: MONO, fontSize: 14, letterSpacing: "0.18em", color: DIM, paddingBottom: 22 }}>
          TESTS
          <br />
          PASSING
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: 108,
          bottom: 100,
          display: "flex",
          gap: 9,
          flexWrap: "wrap",
          maxWidth: 850,
        }}
      >
        <FeatureChip active>APACHE 2.0</FeatureChip>
        <FeatureChip active>X11 / LINUX</FeatureChip>
        <FeatureChip>NO TELEMETRY</FeatureChip>
        <FeatureChip>BRING YOUR OWN KEY</FeatureChip>
      </div>
      <div style={{ position: "absolute", right: 110, top: 210, width: 720, opacity: p, transform: `translateY(${(1 - p) * 25}px)` }}>
        <Terminal
          x={0}
          y={0}
          w={720}
          lines={[
            "$ pytest -q",
            "61 passed in 0.55s",
            "$ ruff check .",
            "All checks passed!",
            "$ git log --oneline -1",
            "v0.2.1 / security patch",
            "github.com/kaiqueramos/spectra-hud",
          ]}
        />
      </div>
    </AbsoluteFill>
  );
};

const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, config: { damping: 20, stiffness: 75 } });
  const out = interpolate(frame, [128, 150], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ background: INK, opacity: out }}>
      <Grid opacity={0.16} />
      <Corners />
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          opacity: p,
          transform: `translateY(${(1 - p) * 26}px)`,
        }}
      >
        <Mark size={76} />
        <div
          style={{
            fontFamily: COND,
            fontSize: 154,
            lineHeight: 0.86,
            color: BONE,
            textTransform: "uppercase",
            textAlign: "center",
            marginTop: 26,
          }}
        >
          Your screen,
          <br />
          <span style={{ color: SIGNAL }}>annotated.</span>
        </div>
        <div
          style={{
            fontFamily: MONO,
            fontSize: 17,
            letterSpacing: "0.2em",
            color: DIM,
            textAlign: "center",
            marginTop: 38,
            lineHeight: 2,
          }}
        >
          <span style={{ color: BONE }}>SPECTRA HUD</span>
          <br />
          KAQUERAMOS.GITHUB.IO/SPECTRA-HUD
          <br />
          LINUX / X11 · APACHE 2.0 · v0.2.1
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Launch: React.FC = () => (
  <AbsoluteFill style={{ background: INK }}>
    <Audio src={staticFile("launch-audio.mp3")} volume={0.9} />
    <Backdrop grid={0.1} />
    <Sequence from={0} durationInFrames={90}>
      <SceneFade duration={90}>
        <Manifesto />
      </SceneFade>
    </Sequence>
    <Sequence from={90} durationInFrames={180}>
      <SceneFade duration={180}>
        <TypeReveal />
      </SceneFade>
    </Sequence>
    <Sequence from={270} durationInFrames={240}>
      <SceneFade duration={240}>
        <ProductDemo />
      </SceneFade>
    </Sequence>
    <Sequence from={510} durationInFrames={180}>
      <SceneFade duration={180}>
        <Command />
      </SceneFade>
    </Sequence>
    <Sequence from={690} durationInFrames={180}>
      <SceneFade duration={180}>
        <Trust />
      </SceneFade>
    </Sequence>
    <Sequence from={870} durationInFrames={180}>
      <SceneFade duration={180}>
        <Proof />
      </SceneFade>
    </Sequence>
    <Sequence from={1050} durationInFrames={150}>
      <SceneFade duration={150}>
        <EndCard />
      </SceneFade>
    </Sequence>
  </AbsoluteFill>
);

