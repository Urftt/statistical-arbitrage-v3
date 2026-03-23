'use client';

import dynamic from 'next/dynamic';
import { Skeleton } from '@mantine/core';
import { PLOTLY_DARK_TEMPLATE } from '@/lib/theme';
import type { CSSProperties } from 'react';
import type { Data, Layout, Config } from 'plotly.js';

/**
 * Dynamically import react-plotly.js with SSR disabled.
 *
 * plotly.js accesses `window` at import time, so `ssr: false` ensures
 * the import only runs in the browser.
 */
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => <Skeleton height={400} radius="md" animate />,
});

export interface PlotlyChartProps {
  data: Data[];
  layout?: Partial<Layout>;
  config?: Partial<Config>;
  style?: CSSProperties;
  className?: string;
}

/**
 * Reusable Plotly chart wrapper that automatically applies the
 * dark theme from `lib/theme.ts`.
 */
export default function PlotlyChart({
  data,
  layout = {},
  config = {},
  style,
  className,
}: PlotlyChartProps) {
  const tpl = PLOTLY_DARK_TEMPLATE.layout;

  const mergedLayout: Partial<Layout> = {
    ...tpl,
    ...layout,
    font: { ...tpl.font, ...layout.font },
    title: {
      ...(typeof tpl.title === 'object' ? tpl.title : {}),
      ...(typeof layout.title === 'object' ? layout.title : layout.title != null ? { text: layout.title } : {}),
    },
    xaxis: { ...tpl.xaxis, ...layout.xaxis },
    yaxis: { ...tpl.yaxis, ...layout.yaxis },
    margin: { ...tpl.margin, ...layout.margin },
    legend: { ...tpl.legend, ...layout.legend },
    colorway: layout.colorway ?? [...tpl.colorway],
  };

  const mergedConfig: Partial<Config> = {
    responsive: true,
    displayModeBar: false,
    ...config,
  };

  return (
    <Plot
      data={data}
      layout={mergedLayout}
      config={mergedConfig}
      style={{ width: '100%', ...style }}
      className={className}
      useResizeHandler
    />
  );
}
