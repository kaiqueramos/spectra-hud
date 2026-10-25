import React from "react";
import { Composition } from "remotion";
import { Hero } from "./Hero";

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Hero"
    component={Hero}
    durationInFrames={600}
    fps={30}
    width={1920}
    height={1080}
  />
);
