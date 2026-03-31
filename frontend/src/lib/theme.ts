import { createTheme } from "@mantine/core";

/**
 * Mantine theme for the StatArb v3 platform.
 * Dark scheme by default, blue primary color.
 */
export const theme = createTheme({
  primaryColor: "blue",
  fontFamily:
    "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
  fontFamilyMonospace: "ui-monospace, SFMono-Regular, Menlo, Monaco, monospace",
  headings: {
    fontFamily:
      "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
  },
  defaultRadius: "sm",
  cursorType: "pointer",
  respectReducedMotion: true,
});

/**
 * Plotly layout template that matches the Mantine dark theme.
 *
 * Every value is tuned to look native inside the Mantine dark shell.
 */
export const PLOTLY_DARK_TEMPLATE = {
  layout: {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(26, 27, 30, 1)", // Mantine dark[7]
    font: {
      color: "#C1C2C5",
      family:
        "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
    },
    title: { font: { color: "#C1C2C5", size: 15 } },
    xaxis: {
      gridcolor: "rgba(55, 58, 64, 0.8)",
      zerolinecolor: "rgba(55, 58, 64, 0.8)",
      title: { font: { color: "#909296" } },
      tickfont: { color: "#909296" },
    },
    yaxis: {
      gridcolor: "rgba(55, 58, 64, 0.8)",
      zerolinecolor: "rgba(55, 58, 64, 0.8)",
      title: { font: { color: "#909296" } },
      tickfont: { color: "#909296" },
    },
    legend: { font: { color: "#C1C2C5" } },
    colorway: [
      "#339AF0", // blue[5]
      "#51CF66", // green[5]
      "#FF6B6B", // red[5]
      "#FCC419", // yellow[5]
      "#CC5DE8", // violet[5]
      "#20C997", // teal[5]
      "#FF922B", // orange[5]
      "#845EF7", // grape[5]
    ],
    margin: { t: 48, b: 40, l: 56, r: 24 },
  },
} as const;
