import React from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {
  Backdrop,
  BODY,
  BONE,
  Cursor,
  COND,
  CodeEditor,
  DialogBox,
  DIM,
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
    [0, 14, duration - 14, duration],
    [0, 1, 1, 0],
    clamp,
  );
  return (
    <AbsoluteFill style={{ opacity, background }}>
      {children}
    </AbsoluteFill>
  );
};

const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, config: { damping: 18, stiffness: 80, mass: 0.8 } });
  const line = interpolate(frame, [20, 55], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ background: INK }}>
      <Grid opacity={0.18} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          gap: 20,
          opacity: p,
          transform: `scale(${0.96 + p * 0.04})`,
        }}
      >
        <Mark size={84} />
        <div
          style={{
            fontFamily: COND,
            fontSize: 96,
            color: BONE,
            letterSpacing: "0.14em",
            lineHeight: 1,
          }}
        >
          SPECTRA
        </div>
        <div
          style={{
            fontFamily: MONO,
            fontSize: 13,
            color: DIM,
            letterSpacing: "0.24em",
          }}
        >
          SCREEN-AWARE HUD / LINUX X11
        </div>
        <div
          style={{
            width: 360 * line,
            height: 1,
            background: SIGNAL,
            marginTop: 12,
            boxShadow: "0 0 22px rgba(255,90,31,.45)",
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

const Demo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(frame, [0, 300], [1.0, 1.045], clamp);
  const shift = interpolate(frame, [0, 300], [0, -18], clamp);
  const scan = interpolate(frame, [20, 28, 85, 92], [0, 0, 1, 0], clamp);
  const scanY = interpolate(frame, [20, 90], [200, 860], clamp);
  const click = interpolate(frame, [140, 148, 170], [0, 1, 0], clamp);
  const key = interpolate(frame, [4, 12, 45, 55], [0, 1, 1, 0], clamp);
  const title = spring({ frame: frame - 6, fps, config: { damping: 20, stiffness: 90 } });

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `scale(${zoom}) translateX(${shift}px)`,
          transformOrigin: "55% 48%",
        }}
      >
        <CodeEditor x={120} y={330} w={980} h={520} scan={scan} />
        <DialogBox x={1160} y={690} w={560} opacity={fade(frame, 20, 40)} />
        <QueuePanel x={120} y={870} w={600} />
        <HudCard
          x={1040}
          y={180}
          tag="ALERT"
          title="EARLY RETURN BUG"
          body="The return happens before the commit. The settlement is never saved."
          delay={58}
          index="01"
        />
        <HudCard
          x={1060}
          y={470}
          tag="ACTION"
          title="DON'T RETRY"
          body="Retry reruns the same broken path. Cancel and fix the return first."
          color={BONE}
          delay={88}
          index="02"
        />
        <HudCard
          x={720}
          y={740}
          tag="ITEM"
          title="QUEUE BACKING UP"
          body="#1043 keeps failing on the same settle path."
          color="#a8b894"
          delay={118}
          index="03"
        />
        <ScanSweep top={scanY} opacity={scan} />
        <Cursor x={1500} y={620} click={click} />
      </div>

      <div style={{ position: "absolute", left: 120, top: 92, opacity: title }}>
        <Kicker>SCAN / ANCHOR / ASK</Kicker>
        <div
          style={{
            fontFamily: COND,
            fontSize: 82,
            lineHeight: 0.94,
            color: BONE,
            marginTop: 12,
            textTransform: "uppercase",
          }}
        >
          One hotkey.
          <br />
          Three moves.
        </div>
        <div style={{ fontFamily: BODY, fontSize: 22, color: DIM, marginTop: 12 }}>
          Your screen becomes the interface.
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 740,
          bottom: 36,
          display: "flex",
          alignItems: "center",
          gap: 10,
          opacity: 0.8 + key * 0.2,
        }}
      >
        <Keycap active={key > 0.5}>CTRL</Keycap>
        <span style={{ color: DIM, fontFamily: MONO }}>+</span>
        <Keycap active={key > 0.5}>ALT</Keycap>
        <span style={{ color: DIM, fontFamily: MONO }}>+</span>
        <Keycap active={key > 0.5} scale={1 + key * 0.04}>
          SPACE
        </Keycap>
      </div>

      <div
        style={{
          position: "absolute",
          right: 120,
          top: 96,
          fontFamily: MONO,
          fontSize: 11,
          letterSpacing: "0.16em",
          color: DIM,
        }}
      >
        3 POINTS / 7.5s / X11
      </div>
    </AbsoluteFill>
  );
};

const Ask: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame: frame - 8, fps, config: { damping: 20, stiffness: 85 } });
  const question = "Why is #1043 failing?";
  const typed = question.slice(0, Math.max(0, Math.floor(interpolate(frame, [18, 62], [0, question.length], clamp))));
  const answer = fade(frame, 70, 82);
  return (
    <AbsoluteFill style={{ background: "rgba(8,10,8,.82)" }}>
      <div style={{ position: "absolute", right: 120, top: 180, opacity: 0.07 }}>
        <Mark size={520} />
      </div>
      <div style={{ position: "absolute", left: 120, top: 120 }}>
        <Kicker>ASK IN PLACE</Kicker>
        <div
          style={{
            fontFamily: COND,
            fontSize: 108,
            lineHeight: 0.9,
            color: BONE,
            textTransform: "uppercase",
            marginTop: 14,
          }}
        >
          Ask anything.
          <br />
          Right there.
        </div>
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 360,
            fontFamily: BODY,
            fontSize: 24,
            color: DIM,
            maxWidth: 560,
          }}
        >
          Click a card. The screenshot and the session context go with the question.
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          right: 120,
          top: 330,
          width: 820,
          opacity: p,
          transform: `translateY(${(1 - p) * 30}px)`,
        }}
      >
        <div
          style={{
            border: `1px solid ${SIGNAL}`,
            background: "rgba(13,17,13,.98)",
            boxShadow: "0 30px 90px rgba(0,0,0,.5)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              padding: "13px 16px",
              borderBottom: `1px solid ${LINE}`,
              fontFamily: MONO,
              fontSize: 11,
              letterSpacing: "0.12em",
              color: SIGNAL,
            }}
          >
            <span>◈ SPECTRA / FOLLOW-UP</span>
            <span style={{ color: DIM }}>ESC CLOSES</span>
          </div>
          <div style={{ padding: "24px 20px" }}>
            <div style={{ fontFamily: BODY, fontSize: 19, color: DIM }}>
              Focus selected: #1043 · Queue
            </div>
            <div
              style={{
                fontFamily: MONO,
                fontSize: 25,
                color: BONE,
                marginTop: 18,
                minHeight: 36,
              }}
            >
              {typed}
              <span style={{ color: SIGNAL }}>▌</span>
            </div>
          </div>
          <div
            style={{
              padding: "12px 20px 16px",
              fontFamily: MONO,
              fontSize: 11,
              color: DIM,
              borderTop: `1px solid ${LINE}`,
            }}
          >
            ENTER SENDS · 1 REQUEST · YOUR PROVIDER
          </div>
        </div>
        <div
          style={{
            marginTop: 16,
            border: `1px solid ${LINE}`,
            background: "rgba(8,10,8,.9)",
            padding: "18px 20px",
            opacity: answer,
            transform: `translateY(${(1 - answer) * 16}px)`,
          }}
        >
          <div style={{ fontFamily: MONO, fontSize: 11, color: SIGNAL, letterSpacing: "0.12em" }}>
            ANSWER / 2.1s
          </div>
          <div style={{ fontFamily: BODY, fontSize: 22, color: BONE, marginTop: 10, lineHeight: 1.35 }}>
            #1043 fails on the same settle path. Fix the early return on line 42 before retrying.
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const End: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = spring({ frame, fps, config: { damping: 20, stiffness: 80 } });
  const out = interpolate(frame, [62, 90], [1, 0], clamp);
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
          transform: `translateY(${(1 - p) * 20}px)`,
        }}
      >
        <Mark size={74} />
        <div
          style={{
            fontFamily: COND,
            fontSize: 132,
            color: BONE,
            textTransform: "uppercase",
            lineHeight: 0.9,
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
            marginTop: 34,
            fontFamily: MONO,
            fontSize: 17,
            letterSpacing: "0.18em",
            color: DIM,
            textAlign: "center",
          }}
        >
          SPECTRA HUD · 10 THEMES · 3 LANGUAGES · APACHE 2.0
          <br />
          <span style={{ color: BONE }}>kaiqueramos.github.io/spectra-hud</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const Hero: React.FC = () => (
  <AbsoluteFill style={{ background: INK }}>
    <Backdrop />
    <Sequence from={0} durationInFrames={90}>
      <SceneFade duration={90}>
        <Intro />
      </SceneFade>
    </Sequence>
    <Sequence from={60} durationInFrames={330}>
      <SceneFade duration={330}>
        <Demo />
      </SceneFade>
    </Sequence>
    <Sequence from={360} durationInFrames={120}>
      <SceneFade duration={120}>
        <Ask />
      </SceneFade>
    </Sequence>
    <Sequence from={450} durationInFrames={90}>
      <SceneFade duration={90}>
        <End />
      </SceneFade>
    </Sequence>
  </AbsoluteFill>
);

