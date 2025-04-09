import React, { useState } from "react";
import {
    VictoryChart,
    VictoryStack,
    VictoryBar,
    VictoryTheme,
    VictoryLabel,
    VictoryZoomContainer,
    VictoryAxis,
    type VictoryZoomContainerProps,
    type ZoomDomain,
} from "victory";

export default function TimelineBar() {
    // Local frame data (will be updated from an event in the future)
    const frames = [
        { frameIndex: 0, startedAt: 1743762977665199 },
        { frameIndex: 1, startedAt: 1743762977783834 },
        { frameIndex: 2, startedAt: 1743762977820285 },
        { frameIndex: 3, startedAt: 1743762977824282 },
        { frameIndex: 4, startedAt: 1743762977839716 },
        { frameIndex: 5, startedAt: 1743762977855324 },
        { frameIndex: 6, startedAt: 1743762977871917 },
        { frameIndex: 7, startedAt: 1743762977888711 },
        { frameIndex: 8, startedAt: 1743762977905937 },
        { frameIndex: 9, startedAt: 1743762977922457 },
        { frameIndex: 10, startedAt: 1743762977938740 },
        { frameIndex: 11, startedAt: 1743762977955107 },
        { frameIndex: 12, startedAt: 1743762977971756 },
        { frameIndex: 13, startedAt: 1743762977988374 },
        { frameIndex: 14, startedAt: 1743762978004951 },
        { frameIndex: 15, startedAt: 1743762978021703 },
        { frameIndex: 16, startedAt: 1743762978038827 },
        { frameIndex: 17, startedAt: 1743762978055120 },
        { frameIndex: 18, startedAt: 1743762978071622 },
        { frameIndex: 19, startedAt: 1743762978088886 },
        { frameIndex: 20, startedAt: 1743762978105961 },
        { frameIndex: 21, startedAt: 1743762978121890 },
        { frameIndex: 22, startedAt: 1743762978138341 },
        { frameIndex: 23, startedAt: 1743762978155136 },
        { frameIndex: 24, startedAt: 1743762978171716 },
        { frameIndex: 25, startedAt: 1743762978189974 },
        { frameIndex: 26, startedAt: 1743762978205503 },
        { frameIndex: 27, startedAt: 1743762978221765 },
        { frameIndex: 28, startedAt: 1743762978238339 },
        { frameIndex: 29, startedAt: 1743762978254917 }
    ];

    function calculateFrameDurations() {
        let durations = [];
        let lastFrame = 0;
        for (let i = 0; i < frames.length - 1; i++) {
            let duration = (frames[i + 1].startedAt - frames[i].startedAt) / 1000;
            durations.push({
                frameIndex: frames[i].frameIndex,
                duration: duration,
                startedAt: i === 0 ? 0 : duration + lastFrame,
            });
            lastFrame += duration;
        }
        return durations;
    }

    const frameDurations = calculateFrameDurations();

    const styles = [
        { data: { fill: "#f3d437", stroke: "#d1b322", strokeWidth: 1 } },
        { data: { fill: "#0ca340", stroke: "#0ca340", strokeWidth: 1 } },
        { data: { fill: "#f3d437", stroke: "#d1b322", strokeWidth: 1 } },
    ];

    // This state will store the zoom scale from the y-axis zoom
    const [zoomScale, setZoomScale] = useState(1);

    return (
        <VictoryChart
            domainPadding={{ x: 20 }}
            theme={VictoryTheme.clean}
            containerComponent={
                <VictoryZoomContainer
                    zoomDimension="y"
                    zoomDomain={{ x: [0, 1] }}
                    minimumZoom={{ x: 1 }}
                    onZoomDomainChange={(domain: ZoomDomain) => {
                        const scale = domain.y[1] - domain.y[0];
                        setZoomScale(scale);
                        return domain;
                    }}
                />
            }
        >
            <VictoryAxis
                dependentAxis
                tickValues={frameDurations.map((f) => f.startedAt)}
                tickFormat={() => ""}
                style={{
                    grid: { stroke: "#ddd", strokeDasharray: "4,4" },
                }}
            />
            <VictoryStack style={{ data: { width: 24 } }} horizontal>
                {frameDurations.map((segment, i) => (
                    <VictoryBar
                        key={i}
                        data={[segment.duration]}
                        labels={() =>
                            segment.duration.toFixed(2) + "ms"
                        }
                        labelComponent={
                            <VictoryLabel
                                dy={-4}
                                dx={10}
                                style={{ fontSize: Math.max(5, 10 / zoomScale) }}
                            />
                        }
                        horizontal
                        style={styles[i]}
                    />
                ))}
            </VictoryStack>
        </VictoryChart>
    );
}
