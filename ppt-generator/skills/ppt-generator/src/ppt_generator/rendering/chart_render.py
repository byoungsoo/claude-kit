"""Chart rendering: plotly/matplotlib → PNG BytesIO."""
import io
from ..schema.content import ChartSpec
from ..schema.design import DesignTokens


def _setup_korean_font() -> str:
    """Return a Korean-capable font name available on this system."""
    import matplotlib.font_manager as fm
    candidates = [
        "Malgun Gothic",
        "Apple SD Gothic Neo",
        "NanumGothic",
        "Noto Sans CJK KR",
        "Noto Sans KR",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return "sans-serif"


def render_chart(spec: ChartSpec, tokens: DesignTokens,
                 width_px: int = 800, height_px: int = 500) -> io.BytesIO:
    """Render a ChartSpec to PNG bytes using plotly (preferred) or matplotlib."""
    if spec.engine == "plotly":
        return _render_plotly(spec, tokens, width_px, height_px)
    return _render_matplotlib(spec, tokens, width_px, height_px)


def _build_plotly_template(tokens: DesignTokens) -> dict:
    colors = tokens.colors
    typo = tokens.typography
    # plotly에서 Malgun Gothic은 직접 지원되지 않으므로 CJK 지원 web-safe 스택 사용
    font_family = "Malgun Gothic, Apple SD Gothic Neo, Noto Sans KR, sans-serif"
    return {
        "layout": {
            "paper_bgcolor": colors.background,
            "plot_bgcolor": colors.surface,
            "font": {
                "family": font_family,
                "color": colors.text_primary,
                "size": 13,
            },
            "colorway": [
                colors.primary, colors.secondary, colors.accent,
                colors.success, colors.warning, colors.danger,
            ],
            "title": {"font": {"size": typo.heading_size_h3, "color": colors.primary,
                               "family": font_family}},
            "xaxis": {
                "gridcolor": colors.surface,
                "linecolor": colors.text_secondary,
                "tickangle": -30,
                "tickfont": {"family": font_family, "size": 11},
                "automargin": True,
            },
            "yaxis": {
                "gridcolor": colors.surface,
                "linecolor": colors.text_secondary,
                "tickfont": {"family": font_family, "size": 11},
            },
            "legend": {"bgcolor": "rgba(0,0,0,0)", "font": {"family": font_family}},
            "margin": {"l": 60, "r": 30, "t": 70, "b": 80},
        }
    }


def _render_plotly(spec: ChartSpec, tokens: DesignTokens,
                   width_px: int, height_px: int) -> io.BytesIO:
    import plotly.graph_objects as go

    template = _build_plotly_template(tokens)
    colors = tokens.colors
    color_seq = [
        colors.primary, colors.secondary, colors.accent,
        colors.success, colors.warning,
    ]

    fig = go.Figure()

    if spec.chart_type == "bar":
        for i, series in enumerate(spec.series):
            fig.add_trace(go.Bar(
                name=series.name,
                x=spec.categories,
                y=series.values,
                marker_color=color_seq[i % len(color_seq)],
            ))
        fig.update_layout(barmode="group")

    elif spec.chart_type == "line":
        for i, series in enumerate(spec.series):
            fig.add_trace(go.Scatter(
                name=series.name,
                x=spec.categories,
                y=series.values,
                mode="lines+markers",
                line=dict(color=color_seq[i % len(color_seq)], width=2),
            ))

    elif spec.chart_type == "pie":
        series = spec.series[0]
        fig.add_trace(go.Pie(
            labels=spec.categories,
            values=series.values,
            marker_colors=color_seq,
            hole=0.35,
        ))

    elif spec.chart_type == "radar":
        for i, series in enumerate(spec.series):
            fig.add_trace(go.Scatterpolar(
                name=series.name,
                r=series.values + [series.values[0]],
                theta=spec.categories + [spec.categories[0]],
                fill="toself",
                line_color=color_seq[i % len(color_seq)],
            ))

    elif spec.chart_type == "area":
        for i, series in enumerate(spec.series):
            fig.add_trace(go.Scatter(
                name=series.name,
                x=spec.categories,
                y=series.values,
                mode="lines",
                fill="tonexty" if i > 0 else "tozeroy",
                line=dict(color=color_seq[i % len(color_seq)]),
            ))

    elif spec.chart_type == "scatter":
        for i, series in enumerate(spec.series):
            fig.add_trace(go.Scatter(
                name=series.name,
                x=spec.categories,
                y=series.values,
                mode="markers",
                marker=dict(color=color_seq[i % len(color_seq)], size=10),
            ))

    fig.update_layout(
        title=dict(text=spec.title, font=template["layout"]["title"]["font"]),
        showlegend=spec.show_legend,
        xaxis_title=spec.x_label,
        yaxis_title=spec.y_label,
        paper_bgcolor=template["layout"]["paper_bgcolor"],
        plot_bgcolor=template["layout"]["plot_bgcolor"],
        font=template["layout"]["font"],
        colorway=template["layout"]["colorway"],
        margin=template["layout"]["margin"],
        xaxis=template["layout"]["xaxis"],
        yaxis=template["layout"]["yaxis"],
        legend=template["layout"]["legend"],
    )

    buf = io.BytesIO()
    fig.write_image(buf, format="png", width=width_px, height=height_px, scale=2)
    buf.seek(0)
    return buf


def _render_matplotlib(spec: ChartSpec, tokens: DesignTokens,
                        width_px: int, height_px: int) -> io.BytesIO:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    font_name = _setup_korean_font()
    matplotlib.rcParams["font.family"] = font_name
    matplotlib.rcParams["axes.unicode_minus"] = False

    colors = tokens.colors
    color_seq = [colors.primary, colors.secondary, colors.accent, colors.success, colors.warning]

    dpi = 150
    fig, ax = plt.subplots(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    fig.patch.set_facecolor(colors.background)
    ax.set_facecolor(colors.surface)

    if spec.chart_type == "bar":
        x = np.arange(len(spec.categories))
        width = 0.8 / max(len(spec.series), 1)
        for i, series in enumerate(spec.series):
            offset = (i - len(spec.series) / 2 + 0.5) * width
            ax.bar(x + offset, series.values, width, label=series.name,
                   color=color_seq[i % len(color_seq)])
        ax.set_xticks(x)
        max_label_len = max((len(c) for c in spec.categories), default=0)
        rotation = -30 if max_label_len > 6 else 0
        ax.set_xticklabels(spec.categories, color=colors.text_primary,
                           rotation=rotation, ha="left" if rotation else "center")

    elif spec.chart_type == "line":
        for i, series in enumerate(spec.series):
            ax.plot(spec.categories, series.values, label=series.name,
                    color=color_seq[i % len(color_seq)], linewidth=2, marker="o")

    elif spec.chart_type == "pie":
        series = spec.series[0]
        ax.pie(series.values, labels=spec.categories,
               colors=color_seq[:len(spec.categories)],
               autopct="%1.1f%%", startangle=90)

    ax.set_title(spec.title, color=colors.primary, fontsize=14, fontweight="bold")
    if spec.x_label:
        ax.set_xlabel(spec.x_label, color=colors.text_secondary)
    if spec.y_label:
        ax.set_ylabel(spec.y_label, color=colors.text_secondary)
    ax.tick_params(colors=colors.text_secondary)
    for spine in ax.spines.values():
        spine.set_edgecolor(colors.text_secondary)

    if spec.show_legend and len(spec.series) > 1:
        ax.legend(facecolor=colors.surface, labelcolor=colors.text_primary)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                facecolor=colors.background)
    plt.close(fig)
    buf.seek(0)
    return buf
