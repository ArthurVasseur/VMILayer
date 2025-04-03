import React from "react";
import {
    VictoryAxis,
    VictoryBrushContainer,
    VictoryChart,
    VictoryLine,
    VictoryTheme,
    VictoryZoomContainer,
    type ZoomDomain,
} from "victory";

export default function Trace() {
    const [state, setState] =
        React.useState({});

    function handleZoom(domain: ZoomDomain) {
        setState({
            selectedDomain: domain,
        });
    }

    function handleBrush(domain: ZoomDomain) {
        setState({ zoomDomain: domain });
    }
    return (
        <div>
            <VictoryChart
                width={550}
                height={300}
                scale={{ x: "time" }}
                theme={VictoryTheme.clean}
                containerComponent={
                    <VictoryZoomContainer
                        responsive={true}
                        zoomDimension="x"
                        zoomDomain={
                            state.zoomDomain
                        }
                        onZoomDomainChange={
                            handleZoom
                        }
                    />
                }
            >
                <VictoryLine
                    data={[
                        {
                            x: new Date(1982, 1, 1),
                            y: 125,
                        },
                        {
                            x: new Date(1987, 1, 1),
                            y: 257,
                        },
                        {
                            x: new Date(1993, 1, 1),
                            y: 345,
                        },
                        {
                            x: new Date(1997, 1, 1),
                            y: 515,
                        },
                        {
                            x: new Date(2001, 1, 1),
                            y: 132,
                        },
                        {
                            x: new Date(2005, 1, 1),
                            y: 305,
                        },
                        {
                            x: new Date(2011, 1, 1),
                            y: 270,
                        },
                        {
                            x: new Date(2015, 1, 1),
                            y: 470,
                        },
                    ]}
                />
            </VictoryChart>

            <VictoryChart
                width={550}
                height={90}
                scale={{ x: "time" }}
                theme={VictoryTheme.clean}
                padding={{
                    top: 0,
                    left: 50,
                    right: 50,
                    bottom: 30,
                }}
                containerComponent={
                    <VictoryBrushContainer
                        responsive={true}
                        brushDimension="x"
                        brushDomain={
                            state.selectedDomain
                        }
                        onBrushDomainChange={
                            handleBrush
                        }
                    />
                }
            >
                <VictoryAxis
                    tickValues={[
                        new Date(1985, 1, 1),
                        new Date(1990, 1, 1),
                        new Date(1995, 1, 1),
                        new Date(2000, 1, 1),
                        new Date(2005, 1, 1),
                        new Date(2010, 1, 1),
                        new Date(2015, 1, 1),
                    ]}
                    tickFormat={(x) =>
                        new Date(x).getFullYear()
                    }
                />
                <VictoryLine
                    data={[
                        {
                            x: new Date(1982, 1, 1),
                            y: 125,
                        },
                        {
                            x: new Date(1987, 1, 1),
                            y: 257,
                        },
                        {
                            x: new Date(1993, 1, 1),
                            y: 345,
                        },
                        {
                            x: new Date(1997, 1, 1),
                            y: 515,
                        },
                        {
                            x: new Date(2001, 1, 1),
                            y: 132,
                        },
                        {
                            x: new Date(2005, 1, 1),
                            y: 305,
                        },
                        {
                            x: new Date(2011, 1, 1),
                            y: 270,
                        },
                        {
                            x: new Date(2015, 1, 1),
                            y: 470,
                        },
                    ]}
                />
            </VictoryChart>
        </div>
    );
}