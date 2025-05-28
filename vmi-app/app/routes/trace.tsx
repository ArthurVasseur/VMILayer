import React, { useState, useMemo } from "react";
import {
  VictoryChart,
  VictoryStack,
  VictoryBar,
  VictoryTheme,
  VictoryLabel,
  VictoryZoomContainer,
  VictoryAxis,
  VictoryClipContainer,
  type ZoomDomain,
} from "victory";
import { invoke } from "@tauri-apps/api/core";
import type { Frame } from "~/interfaces/frames";

export default function TimelineBar() {
  const initialFrames: Frame[] = [];

  const [frames, setFrames] = useState(initialFrames);
  const [zoomScale, setZoomScale] = useState(1);
  const [visibleDomain, setVisibleDomain] = useState({ y: [0, Infinity] });

  const calculateFrameDurations = (frameData: Frame[]) => {
    const durations = [];
    let lastCumulative = 0;
    for (let i = 0; i < frameData.length - 1; i++) {
      let duration = (frameData[i + 1].started_at - frameData[i].started_at) / 1000;
      durations.push({
        frame_index: frameData[i].frame_index,
        duration: duration,
        started_at: i === 0 ? 0 : lastCumulative + duration,
      });
      lastCumulative += duration;
    }
    return durations;
  };

  const allDurations = useMemo(() => calculateFrameDurations(frames), [frames]);


  const visibleDurations = useMemo(() => {
    const [minY, maxY] = visibleDomain.y;
    return allDurations.filter(d => d.started_at >= minY && d.started_at <= maxY);
  }, [allDurations, visibleDomain]);

  const styles = [
    { data: { fill: "#f3d437", stroke: "#d1b322", strokeWidth: 1 } },
    { data: { fill: "#0ca340", stroke: "#0ca340", strokeWidth: 1 } },
    { data: { fill: "#f3d437", stroke: "#d1b322", strokeWidth: 1 } },
  ];

  return (
    <VictoryChart
      domainPadding={{ x: 20 }}
      theme={VictoryTheme.clean}
      containerComponent={
        <VictoryZoomContainer
          zoomDimension="y"
          zoomDomain={{ x: [0, 1] }}
          minimumZoom={{ x: 1 }}
          clipContainerComponent={<VictoryClipContainer clipPadding={{ top: 5, right: 10 }} />}
          onZoomDomainChange={(domain: ZoomDomain) => {
            const scale = domain.y[1] - domain.y[0];
            setZoomScale(scale);
            setVisibleDomain({ y: domain.y });

            (async () => {
              try {
                const newFrames = await invoke("get_frame_data", { size: 500 }) as Frame[];
                setFrames(newFrames);
              } catch (error) {
                console.error("Error fetching frame data:", error);
              }
            })();
            return domain;
          }}
        />
      }
    >
      {/* Axis Configuration */}
      <VictoryAxis
        dependentAxis
        tickValues={allDurations.map((f) => f.started_at)}
        tickFormat={() => ""}
        style={{
          grid: { stroke: "#ddd", strokeDasharray: "4,4" },
        }}
      />
      {/* Render only the visible bar segments */}
      <VictoryStack style={{ data: { width: 24 } }} horizontal>
        {visibleDurations.map((segment, i) => (
          <VictoryBar
            key={segment.frame_index}
            data={[segment.duration]}
            labels={() => segment.duration.toFixed(2) + "ms"}
            labelComponent={
              <VictoryLabel
                dy={-4}
                dx={10}
                style={{ fontSize: Math.max(5, 10 / zoomScale) }}
              />
            }
            horizontal
            style={styles[i % styles.length]}
          />
        ))}
      </VictoryStack>
    </VictoryChart>
  );
}
