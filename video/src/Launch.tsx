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
  DashboardScreen,
  DIM,
  FeatureChip,
  GameScreen,
  Grid,
  HudCard,
  INK,
  Keycap,
  Kicker,
  LINE,
  MONO,
  Mark,
  SIGNAL,
  ScanSweep,
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
    [0, 10, duration - 10, duration],
    [0, 1, 1, 0],
    clamp,
  );
  return <AbsoluteFill style={{ opacity, background }}>{children}</AbsoluteFill>;
};

const Chapter: React.FC<{ index: string; label: string }> = ({ index, label }) => (
  <div
    style={{
      position: "absolute",
      left: 110,
      top: 58,
      display: "flex",
      alignItems: "center",
      gap: 12,
      fontFamily: MONO,
      fontSize: 11,
      letterSpacing: "0.2em",
      color: DIM,
    }}
  >
    <span style={{ color: SIGNAL }}>{index}</span>
    <span style={{ width: 30, height: 1, background: LINE }} />
    <span>{label}</span>
  </div>
);

const Caption: React.FC<{ children: React.ReactNode; y?: number }> = ({
  children,
  y = 62,
}) => (
  <div
    style={{
      position: "absolute",
      left: 110,
      bottom: y,
      fontFamily: MONO,
      fontSize: 12,
      letterSpacing: "0.14em",
      color: DIM,
      textTransform: "uppercase",
    }}
  >
    {children}
  </div>
);

const UseTitle: React.FC<{ title: string; sub: string }> = ({ title, sub }) => (
  <>
    <div style={{ position: "absolute", left: 110, top: 104 }}>
      <Kicker>USE CASE</Kicker>
      <div
        style={{
          fontFamily: COND,
          fontSize: 88,
          lineHeight: 0.88,
          color: BONE,
          textTransform: "uppercase",
          marginTop: 10,
        }}
      >
        {title}
      </div>
      <div style={{ fontFamily: BODY, fontSize: 20, color: DIM, marginTop: 10 }}>
        {sub}
      </div>
    </div>
  </>
);

const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 4, fps, config: { damping: 18, stiffness: 100 } });
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.2} />
      <div style={{ position: "absolute", left: 118, top: 122 }}>
        <Kicker>INTRODUCING SPECTRA HUD</Kicker>
      </div>
      <div
        style={{
          position: "absolute",
          left: 110,
          top: 190,
          fontFamily: COND,
          fontSize: 164,
          lineHeight: 0.84,
          letterSpacing: "-0.02em",
          color: BONE,
          textTransform: "uppercase",
          opacity: p,
          transform: `translateY(${(1 - p) * 30}px)`,
        }}
      >
        One hotkey.
        <br />
        <span style={{ color: SIGNAL }}>Any screen.</span>
      </div>
      <div
        style={{
          position: "absolute",
          left: 118,
          bottom: 150,
          display: "flex",
          gap: 9,
          opacity: fade(frame, 12, 24),
        }}
      >
        <FeatureChip active>01 / CODE</FeatureChip>
        <FeatureChip active>02 / GAME</FeatureChip>
        <FeatureChip active>03 / OPS</FeatureChip>
      </div>
      <div style={{ position: "absolute", right: 120, top: 170, opacity: 0.09 }}>
        <Mark size={460} />
      </div>
      <ScanSweep top={interpolate(frame, [0, 60], [180, 940], clamp)} opacity={0.3} />
    </AbsoluteFill>
  );
};

const CodeCase: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scan = interpolate(frame, [16, 24, 66, 74], [0, 1, 1, 0], clamp);
  const scanY = interpolate(frame, [16, 72], [300, 850], clamp);
  const p = spring({ frame: frame - 4, fps, config: { damping: 20, stiffness: 90 } });
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.1} />
      <Chapter index="01" label="CODE" />
      <UseTitle title="Find the bug." sub="A real editor. The broken line, anchored." />
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: p,
          transform: `translateY(${(1 - p) * 24}px)`,
        }}
      >
        <CodeEditor x={110} y={300} w={1080} h={560} scan={scan} />
        <HudCard
          x={1230}
          y={300}
          w={430}
          tag="ALERT"
          title="EARLY RETURN BUG"
          body="The return happens before the commit. Fix line 42 before retrying."
          delay={28}
          index="01"
        />
        <ScanSweep top={scanY} opacity={scan * 0.8} />
      </div>
      <Caption>ONE SCAN · THE LINE · THE FIX · 7.5S</Caption>
    </AbsoluteFill>
  );
};

const GameCase: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 4, fps, config: { damping: 20, stiffness: 90 } });
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.1} />
      <Chapter index="02" label="GAME" />
      <UseTitle title="Read the room." sub="A dialogue choice. The cost, before you click." />
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: p,
          transform: `translateY(${(1 - p) * 24}px)`,
        }}
      >
        <GameScreen x={110} y={300} w={1250} />
        <HudCard
          x={1390}
          y={300}
          w={430}
          tag="ACTION"
          title="DON'T SELL THE RELIC"
          body="The merchant pays 120g. The quest still needs it. Keep it."
          color={BONE}
          delay={28}
          index="02"
        />
      </div>
      <Caption>THE DIALOGUE SAYS 120G · THE CARD SAYS WHAT IT COSTS</Caption>
    </AbsoluteFill>
  );
};

const OpsCase: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 4, fps, config: { damping: 20, stiffness: 90 } });
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.1} />
      <Chapter index="03" label="OPS" />
      <UseTitle title="Spot the spike." sub="A dashboard. The anomaly, named." />
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: p,
          transform: `translateY(${(1 - p) * 24}px)`,
        }}
      >
        <DashboardScreen x={110} y={300} w={1250} />
        <HudCard
          x={1390}
          y={300}
          w={430}
          tag="ALERT"
          title="CHECKOUT P99"
          body="Spike starts at 14:02. Roll back build 4821."
          delay={28}
          index="03"
        />
      </div>
      <Caption>THE SPIKE STARTED AT 14:02 · ROLLBACK 4821</Caption>
    </AbsoluteFill>
  );
};

const Montage: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 4, fps, config: { damping: 20, stiffness: 80 } });
  const screens = [
    {
      label: "CODE",
      node: <CodeEditor x={0} y={0} w={1080} h={560} scan={0} />,
      scale: 0.42,
      left: 110,
    },
    {
      label: "GAME",
      node: <GameScreen x={0} y={0} w={1250} />,
      scale: 0.36,
      left: 690,
    },
    {
      label: "OPS",
      node: <DashboardScreen x={0} y={0} w={1250} />,
      scale: 0.36,
      left: 1270,
    },
  ];
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.13} />
      <div style={{ position: "absolute", left: 110, top: 110 }}>
        <Kicker>ONE HUD / ANY APP</Kicker>
        <div
          style={{
            fontFamily: COND,
            fontSize: 112,
            lineHeight: 0.88,
            color: BONE,
            textTransform: "uppercase",
            marginTop: 12,
          }}
        >
          Any screen.
          <br />
          <span style={{ color: SIGNAL }}>One hotkey.</span>
        </div>
      </div>
      {screens.map((screen) => (
        <div
          key={screen.label}
          style={{
            position: "absolute",
            left: screen.left,
            top: 410,
            width: 460,
            height: 300,
            overflow: "hidden",
            border: `1px solid ${LINE}`,
            background: "#0a0d09",
            opacity: p,
            transform: `translateY(${(1 - p) * 28}px)`,
          }}
        >
          <div style={{ position: "absolute", transform: `scale(${screen.scale})`, transformOrigin: "top left", width: 1250 }}>
            {screen.node}
          </div>
          <div
            style={{
              position: "absolute",
              left: 12,
              bottom: 10,
              fontFamily: MONO,
              fontSize: 11,
              letterSpacing: "0.16em",
              color: SIGNAL,
            }}
          >
            {screen.label}
          </div>
        </div>
      ))}
      <div style={{ position: "absolute", left: 110, bottom: 90, display: "flex", gap: 10 }}>
        <Keycap active>CTRL</Keycap>
        <span style={{ color: DIM, fontFamily: MONO, alignSelf: "center" }}>+</span>
        <Keycap active>ALT</Keycap>
        <span style={{ color: DIM, fontFamily: MONO, alignSelf: "center" }}>+</span>
        <Keycap active>SPACE</Keycap>
      </div>
      <Caption y={54}>THREE SCREENS · ONE REQUEST PER SCAN · YOUR PROVIDER</Caption>
    </AbsoluteFill>
  );
};

const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, config: { damping: 20, stiffness: 75 } });
  const out = interpolate(frame, [78, 90], [1, 0], clamp);
  return (
    <AbsoluteFill style={{ background: INK, opacity: out }}>
      <Grid opacity={0.16} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          opacity: p,
          transform: `translateY(${(1 - p) * 24}px)`,
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
            marginTop: 24,
          }}
        >
          Your screen,
          <br />
          <span style={{ color: SIGNAL }}>annotated.</span>
        </div>
        <div
          style={{
            marginTop: 32,
            fontFamily: MONO,
            fontSize: 18,
            letterSpacing: "0.16em",
            color: BONE,
            textAlign: "center",
            lineHeight: 1.9,
          }}
        >
          KAQUERAMOS.GITHUB.IO/SPECTRA-HUD
          <br />
          <span style={{ color: DIM, fontSize: 13 }}>
            NO TELEMETRY · KEYRING · 66 TESTS · APACHE 2.0 · v0.3.0-beta
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Launch: React.FC = () => (
  <AbsoluteFill style={{ background: INK }}>
    <Audio src={staticFile("launch-audio.mp3")} volume={0.9} />
    <Backdrop grid={0.09} />
    <Sequence from={0} durationInFrames={60}>
      <SceneFade duration={60}>
        <Hook />
      </SceneFade>
    </Sequence>
    <Sequence from={60} durationInFrames={150}>
      <SceneFade duration={150}>
        <CodeCase />
      </SceneFade>
    </Sequence>
    <Sequence from={210} durationInFrames={150}>
      <SceneFade duration={150}>
        <GameCase />
      </SceneFade>
    </Sequence>
    <Sequence from={360} durationInFrames={150}>
      <SceneFade duration={150}>
        <OpsCase />
      </SceneFade>
    </Sequence>
    <Sequence from={510} durationInFrames={120}>
      <SceneFade duration={120}>
        <Montage />
      </SceneFade>
    </Sequence>
    <Sequence from={630} durationInFrames={90}>
      <SceneFade duration={90}>
        <EndCard />
      </SceneFade>
    </Sequence>
  </AbsoluteFill>
);
