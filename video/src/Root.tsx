import React from "react";
import { Composition } from "remotion";
import { Hero } from "./Hero";
import { Launch } from "./Launch";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Hero"
      component={Hero}
      durationInFrames={540}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="Launch"
      component={Launch}
      durationInFrames={720}
      fps={30}
      width={1920}
      height={1080}
    />
  </>
);
