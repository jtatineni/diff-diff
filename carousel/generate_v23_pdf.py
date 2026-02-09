#!/usr/bin/env python3
"""Generate LinkedIn carousel PDF for diff-diff v2.3 release."""

import math

from fpdf import FPDF

# LinkedIn carousel dimensions (4:5 aspect ratio)
WIDTH = 270  # mm
HEIGHT = 337.5  # mm

# Colors - Light theme with amber/gold accent
LIGHT_BLUE_BG = (235, 245, 255)
MID_BLUE = (59, 130, 246)  # #3b82f6
DARK_BLUE = (30, 64, 175)  # #1e40af
NAVY = (15, 23, 42)  # #0f172a
BLUE_ACCENT = (37, 99, 235)  # #2563eb
WHITE = (255, 255, 255)
RED = (220, 38, 38)  # #dc2626
GREEN = (22, 163, 74)  # #16a34a
GRAY = (100, 116, 139)  # #64748b
LIGHT_GRAY = (148, 163, 184)  # #94a3b8
AMBER = (245, 158, 11)  # #f59e0b - NEW gold accent
DARK_SLATE = (30, 41, 59)  # #1e293b - code block bg


class CarouselV23PDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format=(WIDTH, HEIGHT))
        self.set_auto_page_break(False)

    def add_connector_graphic(self, position="right"):
        """Add decorative connector graphic to bottom corner."""
        if position == "right":
            cx = WIDTH + 20
            cy = HEIGHT - 40
        else:
            cx = -20
            cy = HEIGHT - 40

        self.set_draw_color(*MID_BLUE)
        for i, radius in enumerate([60, 80, 100]):
            self.set_line_width(2.5 - i * 0.5)
            segments = 30
            if position == "right":
                start_angle = math.pi * 0.5
                end_angle = math.pi * 1.0
            else:
                start_angle = 0
                end_angle = math.pi * 0.5

            for j in range(segments):
                t1 = start_angle + (end_angle - start_angle) * j / segments
                t2 = start_angle + (end_angle - start_angle) * (j + 1) / segments
                x1 = cx + radius * math.cos(t1)
                y1 = cy + radius * math.sin(t1)
                x2 = cx + radius * math.cos(t2)
                y2 = cy + radius * math.sin(t2)
                self.line(x1, y1, x2, y2)

        self.set_fill_color(*MID_BLUE)
        if position == "right":
            dot_positions = [(35, HEIGHT - 60), (50, HEIGHT - 45), (30, HEIGHT - 35)]
        else:
            dot_positions = [
                (WIDTH - 35, HEIGHT - 60),
                (WIDTH - 50, HEIGHT - 45),
                (WIDTH - 30, HEIGHT - 35),
            ]
        for i, (dx, dy) in enumerate(dot_positions):
            dot_radius = 3 - i * 0.5
            self.ellipse(
                dx - dot_radius, dy - dot_radius, dot_radius * 2, dot_radius * 2, "F"
            )

    def light_gradient_background(self):
        """Draw light gradient background (top #e1f0ff fading to white)."""
        steps = 50
        for i in range(steps):
            ratio = i / steps
            r = int(225 + (255 - 225) * ratio)
            g = int(240 + (255 - 240) * ratio)
            b = 255
            self.set_fill_color(r, g, b)
            y = i * HEIGHT / steps
            self.rect(0, y, WIDTH, HEIGHT / steps + 1, "F")

    def add_footer(self):
        """Add footer with logo."""
        self.set_xy(0, HEIGHT - 25)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*GRAY)
        self.cell(WIDTH, 10, "diff-diff", align="C")

    def centered_text(self, y, text, size=28, bold=True, color=NAVY):
        """Add centered text."""
        self.set_xy(0, y)
        self.set_font("Helvetica", "B" if bold else "", size)
        self.set_text_color(*color)
        self.cell(WIDTH, size * 0.5, text, align="C")

    def add_list_item(self, y, icon, text, icon_color, text_size=22):
        """Add a list item with icon."""
        margin = 50
        self.set_xy(margin, y)
        self.set_font("Helvetica", "B", text_size + 2)
        self.set_text_color(*icon_color)
        self.cell(25, 12, icon, align="C")
        self.set_text_color(*NAVY)
        self.set_font("Helvetica", "", text_size)
        self.cell(WIDTH - margin * 2 - 25, 12, text)

    def draw_split_logo(self, y, size=18):
        """Draw the split-color diff-diff logo."""
        self.set_xy(0, y)
        self.set_font("Helvetica", "B", size)
        self.set_text_color(*NAVY)
        self.cell(WIDTH / 2 - 5, 10, "diff", align="R")
        self.set_text_color(*MID_BLUE)
        self.cell(10, 10, "-", align="C")
        self.set_text_color(*NAVY)
        self.cell(WIDTH / 2 - 5, 10, "diff", align="L")

    # ── Slide 1: Hook ──────────────────────────────────────────────────

    def slide_hook(self):
        """Slide 1: diff-diff v2.3 hook."""
        self.add_page()
        self.light_gradient_background()

        # Library name as hero element
        self.draw_split_logo(55, size=60)

        # Version number, prominent but secondary
        self.centered_text(120, "v2.3", size=50, color=AMBER)

        # Headline
        self.centered_text(170, "The Python DiD library", size=26)
        self.centered_text(193, "just got a lot more powerful.", size=26)

        # Three-line teaser
        teasers = [
            "The efficient estimator for staggered DiD",
            "Rust-powered acceleration",
            "Windows support",
        ]
        y_start = 230
        for i, teaser in enumerate(teasers):
            self.set_xy(0, y_start + i * 22)
            self.set_font("Helvetica", "", 17)
            self.set_text_color(*GRAY)
            self.cell(WIDTH, 10, teaser, align="C")

        self.add_connector_graphic("right")
        self.add_footer()

    # ── Slide 2: Recap ─────────────────────────────────────────────────

    def slide_recap(self):
        """Slide 2: Quick catch-up on what diff-diff is."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(40, "What is", size=38)
        self.centered_text(73, "diff-diff?", size=38, color=MID_BLUE)

        items = [
            "Complete DiD toolkit for Python",
            "sklearn-like API, statsmodels-style output",
            "Up to 2,000x faster than R",
            "Validated to 10+ decimal places vs R",
        ]

        y_start = 130
        for i, item in enumerate(items):
            self.add_list_item(y_start + i * 35, "+", item, GREEN, text_size=21)

        self.centered_text(
            285,
            "If you missed v1, here's what you need to know.",
            size=16,
            bold=False,
            color=GRAY,
        )
        self.add_connector_graphic("left")
        self.add_footer()

    # ── Slide 3: Imputation DiD Introduction ───────────────────────────

    def slide_imputation_intro(self):
        """Slide 3: Introducing Imputation DiD."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(30, "New Estimator", size=36)
        self.centered_text(60, "Imputation DiD", size=36, color=MID_BLUE)

        # Citation block
        self.set_xy(0, 95)
        self.set_font("Helvetica", "I", 15)
        self.set_text_color(*GRAY)
        self.cell(WIDTH, 8, "Borusyak, Jaravel & Spiess (2024)", align="C")
        self.set_xy(0, 110)
        self.set_font("Helvetica", "I", 14)
        self.cell(WIDTH, 8, "Review of Economic Studies", align="C")

        # Three numbered step boxes
        margin = 35
        box_width = WIDTH - margin * 2
        box_height = 38
        step_y_start = 130
        step_gap = 48

        steps = [
            "Estimate unit + time FE on untreated observations",
            "Impute counterfactual Y(0) for treated units",
            "Aggregate to get treatment effects",
        ]

        for i, step_text in enumerate(steps):
            y = step_y_start + i * step_gap

            # Step number circle
            circle_r = 12
            circle_x = margin + circle_r
            circle_y = y + box_height / 2

            self.set_fill_color(*MID_BLUE)
            self.ellipse(
                circle_x - circle_r,
                circle_y - circle_r,
                circle_r * 2,
                circle_r * 2,
                "F",
            )
            self.set_xy(circle_x - circle_r, circle_y - 6)
            self.set_font("Helvetica", "B", 16)
            self.set_text_color(*WHITE)
            self.cell(circle_r * 2, 12, str(i + 1), align="C")

            # Step text box
            text_x = margin + circle_r * 2 + 8
            text_width = box_width - circle_r * 2 - 8

            self.set_fill_color(*WHITE)
            self.set_draw_color(*MID_BLUE)
            self.set_line_width(0.6)
            self.rect(text_x, y, text_width, box_height, "DF")

            # Single line of step text, centered vertically
            self.set_font("Helvetica", "", 15)
            self.set_text_color(*NAVY)
            self.set_xy(text_x + 8, y + (box_height - 10) / 2)
            self.cell(text_width - 16, 10, step_text)

        self.centered_text(
            275,
            "The semi-parametrically efficient estimator",
            size=15,
            bold=False,
            color=GRAY,
        )
        self.centered_text(
            290,
            "for staggered adoption.",
            size=15,
            bold=False,
            color=GRAY,
        )
        self.add_connector_graphic("right")
        self.add_footer()

    # ── Slide 4: Key Stat ──────────────────────────────────────────────

    def slide_key_stat(self):
        """Slide 4: ~50% shorter confidence intervals."""
        self.add_page()
        self.light_gradient_background()

        # Hero stat
        self.centered_text(45, "~50%", size=100, color=AMBER)

        # Supporting text
        self.centered_text(135, "shorter confidence intervals", size=28)
        self.centered_text(162, "than Callaway-Sant'Anna", size=20, bold=False, color=GRAY)

        # CI comparison bars
        center_x = WIDTH / 2
        bar_y_top = 200
        bar_y_bottom = 245
        bar_height = 22

        # Vertical dashed center line
        self.set_draw_color(*NAVY)
        self.set_line_width(0.5)
        dash_len = 4
        gap_len = 3
        for y_pos_f in range(int(bar_y_top - 5), int(bar_y_bottom + bar_height + 5), dash_len + gap_len):
            self.line(center_x, y_pos_f, center_x, min(y_pos_f + dash_len, bar_y_bottom + bar_height + 5))

        # Top bar: Callaway-SA (wide, red)
        wide_half = 90
        self.set_fill_color(*RED)
        self.rect(center_x - wide_half, bar_y_top, wide_half * 2, bar_height, "F")
        # Point estimate dot
        self.set_fill_color(*WHITE)
        dot_r = 4
        self.ellipse(center_x - dot_r, bar_y_top + bar_height / 2 - dot_r, dot_r * 2, dot_r * 2, "F")
        # Label
        self.set_xy(center_x - wide_half - 5, bar_y_top + 3)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*RED)
        self.cell(wide_half * 2 + 10, 14, "", align="C")
        self.set_xy(0, bar_y_top + 3)
        self.cell(center_x - wide_half - 5, 14, "Callaway-SA", align="R")

        # Bottom bar: Imputation DiD (narrow, blue)
        narrow_half = 45
        self.set_fill_color(*MID_BLUE)
        self.rect(center_x - narrow_half, bar_y_bottom, narrow_half * 2, bar_height, "F")
        # Point estimate dot
        self.set_fill_color(*WHITE)
        self.ellipse(center_x - dot_r, bar_y_bottom + bar_height / 2 - dot_r, dot_r * 2, dot_r * 2, "F")
        # Label
        self.set_xy(0, bar_y_bottom + 3)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*MID_BLUE)
        self.cell(center_x - narrow_half - 5, 14, "Imputation DiD", align="R")

        # Small note at bottom
        self.centered_text(
            290,
            "Under homogeneous treatment effects.",
            size=13,
            bold=False,
            color=GRAY,
        )
        self.centered_text(
            303,
            "Similar gains vs Sun-Abraham.",
            size=13,
            bold=False,
            color=GRAY,
        )
        self.add_connector_graphic("left")
        self.add_footer()

    # ── Slide 5: Why It Works ──────────────────────────────────────────

    def slide_why_precise(self):
        """Slide 5: Uses all untreated data."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(35, "Why it's", size=38)
        self.centered_text(68, "more precise", size=38, color=MID_BLUE)

        # Two-panel comparison
        margin = 25
        panel_width = (WIDTH - margin * 3) / 2
        panel_height = 130
        panel_y = 110

        panels = [
            {
                "title": "Callaway-SA",
                "label": "Defaults to\nnever-treated only",
                "bar_fill": 0.3,  # small portion of data
                "color": RED,
            },
            {
                "title": "Imputation DiD",
                "label": "Uses never-treated\n+ not-yet-treated",
                "bar_fill": 0.8,  # large portion of data
                "color": MID_BLUE,
            },
        ]

        for i, panel in enumerate(panels):
            x = margin + i * (panel_width + margin)

            # Panel box
            self.set_fill_color(*WHITE)
            self.set_draw_color(*panel["color"])
            self.set_line_width(1.0)
            self.rect(x, panel_y, panel_width, panel_height, "DF")

            # Panel title
            self.set_xy(x, panel_y + 10)
            self.set_font("Helvetica", "B", 17)
            self.set_text_color(*panel["color"])
            self.cell(panel_width, 10, panel["title"], align="C")

            # Data bar background
            bar_x = x + 15
            bar_width = panel_width - 30
            bar_y = panel_y + 40
            bar_h = 30

            self.set_fill_color(230, 235, 245)
            self.rect(bar_x, bar_y, bar_width, bar_h, "F")

            # Data bar fill
            fill_w = bar_width * panel["bar_fill"]
            self.set_fill_color(*panel["color"])
            self.rect(bar_x, bar_y, fill_w, bar_h, "F")

            # Label text below bar
            lines = panel["label"].split("\n")
            self.set_font("Helvetica", "", 13)
            self.set_text_color(*NAVY)
            for li, line in enumerate(lines):
                self.set_xy(x, panel_y + 80 + li * 16)
                self.cell(panel_width, 10, line, align="C")

        # Callout box
        callout_y = 245
        callout_margin = 50
        callout_w = WIDTH - callout_margin * 2
        self.set_fill_color(245, 248, 255)
        self.set_draw_color(*MID_BLUE)
        self.set_line_width(0.6)
        self.rect(callout_margin, callout_y, callout_w, 30, "DF")
        self.set_xy(callout_margin, callout_y + 8)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*NAVY)
        self.cell(
            callout_w,
            12,
            "More data in the counterfactual model = tighter inference",
            align="C",
        )

        # Bonus bullet
        self.centered_text(
            285,
            "Built-in pre-trend test, independent of treatment estimation",
            size=13,
            bold=False,
            color=GRAY,
        )
        self.add_connector_graphic("right")
        self.add_footer()

    # ── Slide 6: Code Example ──────────────────────────────────────────

    def slide_code(self):
        """Slide 6: Drop-in replacement code example."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(30, "Drop-in", size=36)
        self.centered_text(60, "replacement", size=36, color=MID_BLUE)

        # Code block
        margin = 30
        code_y = 95
        code_lines = [
            ("# Switch in one line", 1.0),
            ("from diff_diff import ImputationDiD", 1.0),
            ("", 0.5),  # half-height blank line
            ("est = ImputationDiD()", 1.0),
            ("results = est.fit(", 1.0),
            ("    data,", 1.0),
            ("    outcome='sales',", 1.0),
            ("    unit='firm_id',", 1.0),
            ("    time='year',", 1.0),
            ("    first_treat='first_treat',", 1.0),
            ("    aggregate='event_study'", 1.0),
            (")", 1.0),
        ]
        line_height = 11
        total_lines = sum(h for _, h in code_lines)
        code_height = total_lines * line_height + 20

        self.set_fill_color(*DARK_SLATE)
        self.rect(margin, code_y, WIDTH - margin * 2, code_height, "F")

        self.set_font("Courier", "", 13)
        self.set_text_color(*WHITE)
        cumulative_y = 0.0
        for line_text, height_mult in code_lines:
            self.set_xy(margin + 15, code_y + 10 + cumulative_y)
            self.cell(0, 10, line_text)
            cumulative_y += line_height * height_mult

        subtitle_y = code_y + code_height + 12
        self.centered_text(
            subtitle_y,
            "Same fit() signature as CallawaySantAnna.",
            size=15,
            bold=False,
            color=GRAY,
        )
        self.centered_text(
            subtitle_y + 17,
            "Same results object.",
            size=15,
            bold=False,
            color=GRAY,
        )
        self.add_connector_graphic("left")
        self.add_footer()

    # ── Slide 7: Also New ──────────────────────────────────────────────

    def slide_also_new(self):
        """Slide 7: Rust backend + Windows support."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(35, "Also in", size=38)
        self.centered_text(68, "v2.0-2.3", size=38, color=AMBER)

        margin = 20
        gap = 15
        block_width = (WIDTH - margin * 2 - gap) / 2
        block_height = 155
        block_y = 110

        # Feature block data
        blocks = [
            {
                "title": "Rust Backend",
                "version": "v2.0",
                "bullets": [
                    "4-8x additional speedup",
                    "Parallel bootstrap & OLS",
                    "Auto-fallback to pure Python",
                ],
            },
            {
                "title": "Windows Support",
                "version": "v2.2",
                "bullets": [
                    "pip install just works",
                    "No BLAS/LAPACK setup needed",
                    "Linux, macOS, Windows",
                ],
            },
        ]

        for i, block in enumerate(blocks):
            x = margin + i * (block_width + gap)

            # Rounded-rect box
            self.set_fill_color(*WHITE)
            self.set_draw_color(*MID_BLUE)
            self.set_line_width(1.0)
            self.rect(x, block_y, block_width, block_height, "DF")

            # Title
            self.set_xy(x, block_y + 12)
            self.set_font("Helvetica", "B", 19)
            self.set_text_color(*MID_BLUE)
            self.cell(block_width, 10, block["title"], align="C")

            # Version badge
            badge_w = 36
            badge_h = 16
            badge_x = x + (block_width - badge_w) / 2
            badge_y = block_y + 30
            self.set_fill_color(*AMBER)
            self.rect(badge_x, badge_y, badge_w, badge_h, "F")
            self.set_xy(badge_x, badge_y + 2)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*WHITE)
            self.cell(badge_w, 12, block["version"], align="C")

            # Bullets
            pad = 12
            for j, bullet in enumerate(block["bullets"]):
                bullet_y = block_y + 60 + j * 26
                self.set_xy(x + pad, bullet_y)
                self.set_font("Helvetica", "B", 16)
                self.set_text_color(*GREEN)
                self.cell(15, 10, "+")
                self.set_font("Helvetica", "", 13)
                self.set_text_color(*NAVY)
                self.cell(block_width - pad * 2 - 15, 10, bullet)

        self.add_connector_graphic("right")
        self.add_footer()

    # ── Slide 8: Full Toolkit ──────────────────────────────────────────

    def slide_full_toolkit(self):
        """Slide 8: 8 estimators, one library (4x2 grid)."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(25, "Every Method", size=36)
        self.centered_text(55, "You Need", size=36, color=MID_BLUE)

        margin = 25
        box_width = (WIDTH - margin * 3) / 2
        box_height = 42
        gap_y = 6
        y_start = 88

        methods = [
            ("Basic DiD / TWFE", "Classic 2x2 and panel", False),
            ("Callaway-Sant'Anna", "Staggered adoption (2021)", False),
            ("Sun-Abraham", "Interaction-weighted (2021)", False),
            ("Imputation DiD", "Borusyak et al. (2024)", True),  # NEW badge
            ("Synthetic DiD", "Arkhangelsky et al. (2021)", False),
            ("Triple Difference", "DDD with proper covariates", False),
            ("Honest DiD", "Rambachan-Roth sensitivity", False),
            ("Bacon Decomposition", "TWFE diagnostic weights", False),
        ]

        for i, (title, desc, is_new) in enumerate(methods):
            col = i % 2
            row = i // 2
            x = margin + col * (box_width + margin)
            y = y_start + row * (box_height + gap_y)

            # Box — use amber border for the NEW item
            self.set_fill_color(*WHITE)
            if is_new:
                self.set_draw_color(*AMBER)
                self.set_line_width(1.2)
            else:
                self.set_draw_color(*MID_BLUE)
                self.set_line_width(0.8)
            self.rect(x, y, box_width, box_height, "DF")

            # Title
            self.set_xy(x + 5, y + 5)
            self.set_font("Helvetica", "B", 15)
            self.set_text_color(*AMBER if is_new else MID_BLUE)
            display_title = title + "  [NEW]" if is_new else title
            self.cell(box_width - 10, 10, display_title, align="C")

            # Description
            self.set_xy(x + 5, y + 24)
            self.set_font("Helvetica", "", 12)
            self.set_text_color(*GRAY)
            self.cell(box_width - 10, 10, desc, align="C")

        self.centered_text(
            y_start + 4 * (box_height + gap_y) + 5,
            "The most complete DiD toolkit in any language.",
            size=15,
            bold=False,
            color=GRAY,
        )
        self.add_connector_graphic("left")
        self.add_footer()

    # ── Slide 9: Validation ────────────────────────────────────────────

    def slide_validated(self):
        """Slide 9: Battle-tested validation."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(30, "Validated.", size=34)
        self.centered_text(58, "Production-Ready.", size=34, color=MID_BLUE)

        # Table
        margin = 30
        table_y = 105
        row_height = 36

        data = [
            ("Point estimates vs R", "Identical (10+ decimals)"),
            ("R packages tested", "did, synthdid, fixest, didimputation"),
            ("Jupyter tutorials", "11 notebooks included"),
        ]

        # Header
        col1_width = (WIDTH - margin * 2) * 0.45
        col2_width = (WIDTH - margin * 2) * 0.55

        self.set_fill_color(*MID_BLUE)
        self.rect(margin, table_y, WIDTH - margin * 2, row_height, "F")
        self.set_xy(margin, table_y + 10)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*WHITE)
        self.cell(col1_width, 14, "Comparison", align="C")
        self.cell(col2_width, 14, "Result", align="C")

        # Rows
        for i, (label, value) in enumerate(data):
            y = table_y + row_height * (i + 1)

            if i % 2 == 0:
                self.set_fill_color(245, 248, 255)
            else:
                self.set_fill_color(*WHITE)
            self.rect(margin, y, WIDTH - margin * 2, row_height, "F")

            self.set_xy(margin + 10, y + 10)
            self.set_font("Helvetica", "", 15)
            self.set_text_color(*NAVY)
            self.cell(col1_width - 10, 14, label)

            self.set_xy(margin + col1_width, y + 10)
            self.set_font("Helvetica", "B", 15)
            self.set_text_color(*GREEN)
            self.cell(col2_width - 10, 14, value, align="C")

        # Table bottom = table_y + row_height * 4 = 105 + 144 = 249
        self.centered_text(
            255,
            "Academic-grade accuracy. Validated against 4 R packages.",
            size=15,
            bold=False,
            color=GRAY,
        )
        self.add_connector_graphic("right")
        self.add_footer()

    # ── Slide 10: CTA ──────────────────────────────────────────────────

    def slide_cta(self):
        """Slide 10: Upgrade today."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(45, "Upgrade to", size=38)
        self.centered_text(78, "v2.3", size=38, color=AMBER)

        # pip install box
        box_width = 195
        box_x = (WIDTH - box_width) / 2
        box_y = 125
        box_h = 36
        self.set_fill_color(*MID_BLUE)
        self.rect(box_x, box_y, box_width, box_h, "F")

        self.set_xy(box_x, box_y + 10)
        self.set_font("Courier", "B", 15)
        self.set_text_color(*WHITE)
        self.cell(box_width, 14, "$ pip install --upgrade diff-diff", align="C")

        # GitHub link
        self.centered_text(200, "github.com/igerber/diff-diff", size=20, color=MID_BLUE)

        # Info lines
        self.centered_text(
            232,
            "Full documentation & 11 tutorials included",
            size=16,
            bold=False,
            color=GRAY,
        )
        self.centered_text(
            252,
            "MIT Licensed  |  Open Source",
            size=16,
            bold=False,
            color=GRAY,
        )

        # Large logo
        self.draw_split_logo(278, size=28)

        # Subtitle
        self.centered_text(
            298,
            "Difference-in-Differences for Python",
            size=14,
            bold=False,
            color=GRAY,
        )

        self.add_connector_graphic("left")


def main():
    pdf = CarouselV23PDF()

    pdf.slide_hook()
    pdf.slide_recap()
    pdf.slide_imputation_intro()
    pdf.slide_key_stat()
    pdf.slide_why_precise()
    pdf.slide_code()
    pdf.slide_also_new()
    pdf.slide_full_toolkit()
    pdf.slide_validated()
    pdf.slide_cta()

    output_path = "/Users/igerber/diff-diff/carousel/diff-diff-v23-carousel.pdf"
    pdf.output(output_path)
    print(f"PDF saved to: {output_path}")


if __name__ == "__main__":
    main()
