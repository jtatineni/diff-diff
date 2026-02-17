#!/usr/bin/env python3
"""Generate LinkedIn carousel PDF for diff-diff v2.4 release."""

import math
import os
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image as PILImage  # noqa: E402

from fpdf import FPDF  # noqa: E402

# Use Computer Modern math font (LaTeX-like)
plt.rcParams["mathtext.fontset"] = "cm"

# LinkedIn carousel dimensions (4:5 aspect ratio)
WIDTH = 270  # mm
HEIGHT = 337.5  # mm

# Colors - Light theme with teal accent
MID_BLUE = (59, 130, 246)  # #3b82f6
NAVY = (15, 23, 42)  # #0f172a
WHITE = (255, 255, 255)
RED = (220, 38, 38)  # #dc2626
GREEN = (22, 163, 74)  # #16a34a
GRAY = (100, 116, 139)  # #64748b
LIGHT_GRAY = (148, 163, 184)  # #94a3b8
TEAL = (8, 145, 178)  # #0891b2 - v2.4 accent
DARK_SLATE = (30, 41, 59)  # #1e293b - code block bg

# Navy as hex for matplotlib
NAVY_HEX = "#0f172a"


class CarouselV24PDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format=(WIDTH, HEIGHT))
        self.set_auto_page_break(False)
        self._temp_files = []

    def cleanup(self):
        """Remove temporary equation image files."""
        for f in self._temp_files:
            try:
                os.unlink(f)
            except OSError:
                pass

    # ── Equation Rendering ────────────────────────────────────────────

    def _render_equations(self, latex_lines, fontsize=26):
        """Render one or more LaTeX equations to a single PNG image.

        Args:
            latex_lines: list of LaTeX math strings (each wrapped in $...$)
            fontsize: matplotlib font size

        Returns:
            (path, pixel_width, pixel_height)
        """
        n = len(latex_lines)
        fig_h = max(0.7, 0.55 * n + 0.15)
        fig = plt.figure(figsize=(10, fig_h))

        for i, line in enumerate(latex_lines):
            y_frac = 1.0 - (2 * i + 1) / (2 * n)
            fig.text(
                0.5, y_frac, line,
                fontsize=fontsize, ha="center", va="center",
                color=NAVY_HEX,
            )

        fig.patch.set_alpha(0)
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        fig.savefig(path, dpi=250, bbox_inches="tight", pad_inches=0.06,
                    transparent=True)
        plt.close(fig)

        with PILImage.open(path) as img:
            pw, ph = img.size

        self._temp_files.append(path)
        return path, pw, ph

    def _place_equation(self, path, pw, ph, box_x, _box_y, box_w,
                        content_top, content_bottom):
        """Place an equation image centered in a region of a box."""
        max_w = box_w * 0.82
        aspect = ph / pw
        display_w = max_w
        display_h = display_w * aspect

        # Shrink if too tall for the available space
        avail_h = content_bottom - content_top
        if display_h > avail_h:
            display_h = avail_h
            display_w = display_h / aspect

        eq_x = box_x + (box_w - display_w) / 2
        eq_y = content_top + (avail_h - display_h) / 2
        self.image(path, eq_x, eq_y, display_w)

    # ── Helper Methods ────────────────────────────────────────────────

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

    # ── Slide 1: Hook ─────────────────────────────────────────────────

    def slide_hook(self):
        """Slide 1: diff-diff v2.4 hook."""
        self.add_page()
        self.light_gradient_background()

        self.draw_split_logo(55, size=60)
        self.centered_text(120, "v2.4", size=50, color=TEAL)

        self.centered_text(170, "Your variance estimator", size=26)
        self.centered_text(193, "is lying to you.", size=26)

        teasers = [
            "Gardner (2022) Two-Stage DiD",
            "GMM sandwich variance that tells the truth",
            "Per-observation treatment effects",
        ]
        y_start = 230
        for i, teaser in enumerate(teasers):
            self.set_xy(0, y_start + i * 22)
            self.set_font("Helvetica", "", 17)
            self.set_text_color(*GRAY)
            self.cell(WIDTH, 10, teaser, align="C")

        self.add_footer()

    # ── Slide 2: Recap ────────────────────────────────────────────────

    def slide_recap(self):
        """Slide 2: Quick catch-up on what diff-diff is."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(40, "What is", size=38)
        self.centered_text(73, "diff-diff?", size=38, color=MID_BLUE)

        items = [
            "Complete DiD toolkit for Python",
            "sklearn-like API, statsmodels-style output",
            "10 methods, 12 tutorials, validated vs R",
            "The most complete DiD toolkit in any language",
        ]
        y_start = 130
        for i, item in enumerate(items):
            self.add_list_item(y_start + i * 35, "+", item, GREEN, text_size=21)

        self.centered_text(
            285, "Now with the Two-Stage DiD estimator.",
            size=16, bold=False, color=GRAY,
        )
        self.add_footer()

    # ── Slide 3: The TWFE Problem ─────────────────────────────────────

    def slide_twfe_problem(self):
        """Slide 3: The TWFE problem — treated outcomes contaminate counterfactual."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(30, "The TWFE", size=38)
        self.centered_text(63, "Problem", size=38, color=RED)

        # Panel data grid: 4 units x 6 periods showing staggered treatment
        margin = 40
        grid_y = 100
        n_units = 4
        n_periods = 6
        cell_w = (WIDTH - margin * 2) / n_periods
        cell_h = 18  # compact cells

        # Period labels
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*GRAY)
        for p in range(n_periods):
            self.set_xy(margin + p * cell_w, grid_y - 12)
            self.cell(cell_w, 10, f"t={p + 1}", align="C")

        # Unit labels
        for u in range(n_units):
            self.set_xy(margin - 28, grid_y + u * cell_h + 2)
            self.set_text_color(*NAVY)
            self.set_font("Helvetica", "", 10)
            self.cell(26, 10, f"Unit {u + 1}", align="R")

        # Treatment onset: unit 1 at t=3, unit 2 at t=4, units 3-4 never treated
        treat_onset = {0: 3, 1: 4, 2: None, 3: None}

        for u in range(n_units):
            for p in range(n_periods):
                x = margin + p * cell_w
                y = grid_y + u * cell_h
                onset = treat_onset[u]
                is_treated = onset is not None and (p + 1) >= onset

                if is_treated:
                    self.set_fill_color(254, 202, 202)
                    self.set_draw_color(220, 38, 38)
                else:
                    self.set_fill_color(219, 234, 254)
                    self.set_draw_color(147, 197, 253)

                self.set_line_width(0.5)
                self.rect(x, y, cell_w, cell_h, "DF")

        grid_bottom = grid_y + n_units * cell_h

        # Diagram label
        self.set_xy(margin, grid_bottom + 4)
        self.set_font("Helvetica", "I", 12)
        self.set_text_color(*GRAY)
        self.cell(
            WIDTH - margin * 2, 10,
            "TWFE estimates FEs using ALL data, including treated outcomes",
            align="C",
        )

        # Legend
        legend_y = grid_bottom + 18
        legend_x = margin + 25
        self.set_fill_color(219, 234, 254)
        self.rect(legend_x, legend_y, 10, 8, "F")
        self.set_xy(legend_x + 13, legend_y - 1)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*NAVY)
        self.cell(45, 10, "Untreated")
        self.set_fill_color(254, 202, 202)
        self.rect(legend_x + 75, legend_y, 10, 8, "F")
        self.set_xy(legend_x + 88, legend_y - 1)
        self.cell(45, 10, "Treated")

        # Explanation
        explain_y = legend_y + 18
        self.centered_text(
            explain_y,
            "Treated outcomes contaminate the counterfactual",
            size=16, bold=True, color=NAVY,
        )
        self.centered_text(
            explain_y + 18,
            "Heterogeneous effects create negative weights",
            size=14, bold=False, color=GRAY,
        )

        # Callout box
        callout_y = explain_y + 40
        callout_margin = 40
        callout_w = WIDTH - callout_margin * 2
        self.set_fill_color(240, 253, 250)
        self.set_draw_color(*TEAL)
        self.set_line_width(0.8)
        self.rect(callout_margin, callout_y, callout_w, 26, "DF")
        self.set_xy(callout_margin, callout_y + 6)
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*TEAL)
        self.cell(
            callout_w, 12,
            "Solution: estimate the model on untreated data only.",
            align="C",
        )

        self.add_footer()

    # ── Slide 4: Two-Stage Procedure ──────────────────────────────────

    def slide_two_stage_intro(self):
        """Slide 4: Two-Stage DiD procedure with 2 numbered step boxes."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(30, "Two-Stage DiD", size=36, color=NAVY)

        # Citation block
        self.set_xy(0, 65)
        self.set_font("Helvetica", "I", 15)
        self.set_text_color(*GRAY)
        self.cell(
            WIDTH, 8,
            "Gardner (2022)  |  Butts & Gardner (R Journal, 2022)",
            align="C",
        )

        # Two numbered step boxes
        margin = 35
        box_width = WIDTH - margin * 2
        box_height = 42
        circle_r = 14
        step_y_start = 95
        total_step_unit = 65  # box_height + gap between boxes

        steps = [
            "Estimate unit + time FEs on untreated observations only",
            "Residualize ALL outcomes, regress on treatment",
        ]

        for i, step_text in enumerate(steps):
            y = step_y_start + i * total_step_unit

            # Step number circle
            circle_x = margin + circle_r
            circle_y = y + box_height / 2

            self.set_fill_color(*TEAL)
            self.ellipse(
                circle_x - circle_r, circle_y - circle_r,
                circle_r * 2, circle_r * 2, "F",
            )
            self.set_xy(circle_x - circle_r, circle_y - 6)
            self.set_font("Helvetica", "B", 18)
            self.set_text_color(*WHITE)
            self.cell(circle_r * 2, 12, str(i + 1), align="C")

            # Step text box
            text_x = margin + circle_r * 2 + 10
            text_width = box_width - circle_r * 2 - 10

            self.set_fill_color(*WHITE)
            self.set_draw_color(*TEAL)
            self.set_line_width(0.8)
            self.rect(text_x, y, text_width, box_height, "DF")

            self.set_font("Helvetica", "", 15)
            self.set_text_color(*NAVY)
            self.set_xy(text_x + 10, y + (box_height - 10) / 2)
            self.cell(text_width - 20, 10, step_text)

        # Downward arrow between boxes
        arrow_x = margin + circle_r
        arrow_top = step_y_start + box_height + 2
        arrow_bottom = step_y_start + total_step_unit - 2
        self.set_draw_color(*TEAL)
        self.set_line_width(1.2)
        self.line(arrow_x, arrow_top, arrow_x, arrow_bottom)
        # Arrowhead
        head_size = 5
        self.line(arrow_x - head_size, arrow_bottom - head_size, arrow_x, arrow_bottom)
        self.line(arrow_x + head_size, arrow_bottom - head_size, arrow_x, arrow_bottom)

        # Footer text
        footer_y = step_y_start + 2 * total_step_unit + 8
        self.centered_text(
            footer_y,
            "Clean counterfactual from untreated data.",
            size=15, bold=False, color=GRAY,
        )
        self.centered_text(
            footer_y + 18,
            "Unbiased treatment effects from the residuals.",
            size=15, bold=False, color=GRAY,
        )

        # Caveat
        self.centered_text(
            footer_y + 45,
            "Requires parallel trends + no anticipation + absorbing treatment.",
            size=11, bold=False, color=LIGHT_GRAY,
        )

        self.add_footer()

    # ── Slide 5: The Math ─────────────────────────────────────────────

    def slide_math(self):
        """Slide 5: Three equation boxes with LaTeX-rendered equations."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(30, "The Math", size=38)
        self.centered_text(63, "Two stages, three equations", size=18, bold=False, color=GRAY)

        margin = 30
        box_w = WIDTH - margin * 2
        badge_w = 65
        badge_h = 18

        # Pre-render all equations
        eq1_path, eq1_pw, eq1_ph = self._render_equations(
            [r"$Y_{it} = \alpha_i + \delta_t + \varepsilon_{it}$"]
        )
        eq2_path, eq2_pw, eq2_ph = self._render_equations([
            r"$\tilde{Y}_{it} = Y_{it} - \hat{\alpha}_i - \hat{\delta}_t$",
            r"$\tilde{Y}_{it} = \tau \cdot D_{it} + u_{it}$",
        ])
        eq3_path, eq3_pw, eq3_ph = self._render_equations(
            [r"$V = (D^\prime\! D)^{-1}\left[\sum_c S_c\, S_c^\prime\right](D^\prime\! D)^{-1}$"],
            fontsize=24,
        )

        # Box definitions: (badge_label, eq_path/pw/ph, annotation, box_height)
        boxes = [
            {
                "badge": "Stage 1",
                "eq": (eq1_path, eq1_pw, eq1_ph),
                "annotation": "(on  D_it = 0  only)",
                "height": 48,
            },
            {
                "badge": "Stage 2",
                "eq": (eq2_path, eq2_pw, eq2_ph),
                "annotation": "(on ALL observations)",
                "height": 62,
            },
            {
                "badge": "Variance",
                "eq": (eq3_path, eq3_pw, eq3_ph),
                "annotation": None,
                "height": 48,
            },
        ]

        y_cursor = 85
        box_gap = 8

        for box in boxes:
            bh = box["height"]

            # White box with teal border
            self.set_fill_color(*WHITE)
            self.set_draw_color(*TEAL)
            self.set_line_width(0.8)
            self.rect(margin, y_cursor, box_w, bh, "DF")

            # Teal badge overlapping top edge
            badge_x = margin + 8
            badge_y = y_cursor - badge_h / 2
            self.set_fill_color(*TEAL)
            self.rect(badge_x, badge_y, badge_w, badge_h, "F")
            self.set_xy(badge_x, badge_y + 3)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*WHITE)
            self.cell(badge_w, 12, box["badge"], align="C")

            # Determine content region (between badge and annotation)
            content_top = y_cursor + badge_h / 2 + 2
            if box["annotation"]:
                ann_y = y_cursor + bh - 14
                content_bottom = ann_y - 2
            else:
                content_bottom = y_cursor + bh - 6

            # Place equation image centered
            eq_path, eq_pw, eq_ph = box["eq"]
            self._place_equation(
                eq_path, eq_pw, eq_ph,
                margin, y_cursor, box_w,
                content_top, content_bottom,
            )

            # Annotation text
            if box["annotation"]:
                self.set_xy(margin, ann_y)
                self.set_font("Helvetica", "I", 12)
                self.set_text_color(*GRAY)
                self.cell(box_w, 10, box["annotation"], align="C")

            y_cursor += bh + box_gap

        # GMM annotation below all boxes
        self.centered_text(
            y_cursor + 2,
            "GMM sandwich corrects for Stage 1 uncertainty",
            size=14, bold=True, color=TEAL,
        )

        self.add_footer()

    # ── Slide 6: Honest Standard Errors ───────────────────────────────

    def slide_honest_se(self):
        """Slide 6: Three CI bars comparing TWFE, GMM, and naive OLS."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(30, "Honest", size=38)
        self.centered_text(63, "Standard Errors", size=38, color=TEAL)

        self.centered_text(
            100, "Not all confidence intervals tell the truth",
            size=16, bold=False, color=GRAY,
        )

        center_x = WIDTH / 2
        bar_height = 22
        bar_y_start = 122
        bar_gap = 14

        # Vertical dashed center line
        self.set_draw_color(*NAVY)
        self.set_line_width(0.5)
        dash_len = 4
        gap_len = 3
        line_top = bar_y_start - 6
        line_bottom = bar_y_start + 3 * (bar_height + bar_gap) - bar_gap + 6
        for y_pos in range(int(line_top), int(line_bottom), dash_len + gap_len):
            self.line(center_x, y_pos, center_x,
                      min(y_pos + dash_len, line_bottom))

        dot_r = 4
        bars = [
            {"half_width": 95, "color": RED, "label": "Naive TWFE",
             "annotation": "biased", "marker": None},
            {"half_width": 65, "color": TEAL, "label": "GMM Sandwich",
             "annotation": "correct coverage", "marker": "check"},
            {"half_width": 40, "color": GRAY, "label": "Naive Stage 2 OLS",
             "annotation": "false precision", "marker": "x"},
        ]

        for i, bar in enumerate(bars):
            y = bar_y_start + i * (bar_height + bar_gap)
            hw = bar["half_width"]

            # Bar
            self.set_fill_color(*bar["color"])
            self.rect(center_x - hw, y, hw * 2, bar_height, "F")

            # Point estimate dot
            self.set_fill_color(*WHITE)
            self.ellipse(
                center_x - dot_r, y + bar_height / 2 - dot_r,
                dot_r * 2, dot_r * 2, "F",
            )

            # Marker to the right of the bar
            if bar["marker"] == "check":
                mark_x = center_x + hw + 6
                self.set_xy(mark_x, y + 2)
                self.set_font("Helvetica", "B", 16)
                self.set_text_color(*GREEN)
                self.cell(15, 14, "OK")
            elif bar["marker"] == "x":
                mark_x = center_x + hw + 6
                self.set_xy(mark_x, y + 2)
                self.set_font("Helvetica", "B", 16)
                self.set_text_color(*RED)
                self.cell(15, 14, "X")

            # Label to the left
            self.set_xy(0, y + 3)
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(*bar["color"])
            self.cell(center_x - hw - 6, 14, bar["label"], align="R")

            # Annotation to the right (after marker)
            ann_x = center_x + hw + (23 if bar["marker"] else 6)
            self.set_xy(ann_x, y + 3)
            self.set_font("Helvetica", "I", 11)
            self.set_text_color(*bar["color"])
            self.cell(60, 14, bar["annotation"])

        # Notes
        note_y = bar_y_start + 3 * (bar_height + bar_gap) + 2
        self.centered_text(
            note_y,
            "Naive OLS ignores that alpha-hat and delta-hat are estimated.",
            size=13, bold=False, color=GRAY,
        )
        self.centered_text(
            note_y + 15,
            "The GMM correction accounts for first-stage uncertainty.",
            size=13, bold=False, color=GRAY,
        )

        # Callout
        callout_y = note_y + 34
        callout_margin = 50
        callout_w = WIDTH - callout_margin * 2
        self.set_fill_color(240, 253, 250)
        self.set_draw_color(*TEAL)
        self.set_line_width(0.8)
        self.rect(callout_margin, callout_y, callout_w, 24, "DF")
        self.set_xy(callout_margin, callout_y + 5)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*TEAL)
        self.cell(
            callout_w, 12,
            "Narrower isn't better if it's wrong. GMM gets it right.",
            align="C",
        )

        # Caveat (single line)
        self.centered_text(
            callout_y + 30,
            "Under homogeneous effects. Compare with ImputationDiD for robustness.",
            size=10, bold=False, color=LIGHT_GRAY,
        )

        self.add_footer()

    # ── Slide 7: Per-Observation Treatment Effects ────────────────────

    def slide_per_obs_effects(self):
        """Slide 7: DataFrame-style table showing per-observation effects."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(30, "Per-Observation", size=36)
        self.centered_text(63, "Treatment Effects", size=36, color=TEAL)

        self.centered_text(
            98, "Every treated unit-period gets its own tau-hat",
            size=16, bold=False, color=GRAY,
        )

        # DataFrame-style table
        margin = 40
        table_x = margin
        table_y = 118
        table_width = WIDTH - margin * 2
        row_height = 22
        n_cols = 4
        col_width = table_width / n_cols

        headers = ["unit", "time", "tau_hat", "weight"]
        data_rows = [
            ["firm_3", "2019", "2.14", "0.0033"],
            ["firm_3", "2020", "1.87", "0.0033"],
            ["firm_7", "2020", "3.21", "0.0033"],
            ["firm_7", "2021", "2.95", "0.0033"],
            ["...", "...", "...", "..."],
        ]

        # Header row
        self.set_fill_color(*DARK_SLATE)
        self.rect(table_x, table_y, table_width, row_height, "F")
        self.set_font("Courier", "B", 13)
        self.set_text_color(*WHITE)
        for c, header in enumerate(headers):
            self.set_xy(table_x + c * col_width, table_y + 4)
            self.cell(col_width, 12, header, align="C")

        # Data rows
        for r, row_data in enumerate(data_rows):
            y = table_y + (r + 1) * row_height

            if r % 2 == 0:
                self.set_fill_color(245, 250, 255)
            else:
                self.set_fill_color(*WHITE)
            self.rect(table_x, y, table_width, row_height, "F")

            self.set_draw_color(220, 230, 240)
            self.set_line_width(0.3)
            self.rect(table_x, y, table_width, row_height, "D")

            self.set_font("Courier", "", 12)
            self.set_text_color(*NAVY)
            for c, val in enumerate(row_data):
                self.set_xy(table_x + c * col_width, y + 4)
                self.cell(col_width, 12, val, align="C")

        # Notes below table
        table_bottom = table_y + (len(data_rows) + 1) * row_height
        note_y = table_bottom + 10
        self.centered_text(
            note_y,
            "Aggregate to: static ATT, event study, or by cohort",
            size=16, bold=True, color=NAVY,
        )
        self.centered_text(
            note_y + 20,
            "Or analyze individual treatment effect heterogeneity",
            size=15, bold=False, color=GRAY,
        )

        self.add_footer()

    # ── Slide 8: Code Example ─────────────────────────────────────────

    def slide_code(self):
        """Slide 8: Drop-in replacement code example."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(30, "Drop-in", size=36)
        self.centered_text(60, "Replacement", size=36, color=MID_BLUE)

        margin = 30
        code_y = 95
        code_lines = [
            ("# Switch in one line", 1.0),
            ("from diff_diff import TwoStageDiD", 1.0),
            ("", 0.5),
            ("est = TwoStageDiD()", 1.0),
            ("results = est.fit(", 1.0),
            ("    data,", 1.0),
            ("    outcome='sales',", 1.0),
            ("    unit='firm_id',", 1.0),
            ("    time='year',", 1.0),
            ("    first_treat='first_treat',", 1.0),
            ("    aggregate='event_study'", 1.0),
            (")", 1.0),
            ("", 0.5),
            ("# Per-observation effects", 1.0),
            ("results.treatment_effects.head()", 1.0),
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
            "Same fit() API as CallawaySantAnna and ImputationDiD.",
            size=15, bold=False, color=GRAY,
        )
        self.centered_text(
            subtitle_y + 17,
            "Identical point estimates to ImputationDiD.",
            size=15, bold=False, color=GRAY,
        )
        self.add_footer()

    # ── Slide 9: Full Toolkit (5x2 Grid) ─────────────────────────────

    def slide_full_toolkit(self):
        """Slide 9: 10 methods, one library (5x2 grid)."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(20, "Every Method", size=36)
        self.centered_text(50, "You Need", size=36, color=MID_BLUE)

        margin = 25
        box_width = (WIDTH - margin * 3) / 2
        box_height = 34
        gap_y = 3
        y_start = 80

        methods = [
            ("Basic DiD / TWFE", "Classic 2x2 and panel", False),
            ("Callaway-Sant'Anna", "Staggered adoption (2021)", False),
            ("Sun-Abraham", "Interaction-weighted (2021)", False),
            ("Imputation DiD", "Borusyak et al. (2024)", False),
            ("Two-Stage DiD", "Gardner (2022)", True),
            ("Synthetic DiD", "Arkhangelsky et al. (2021)", False),
            ("Triple Difference", "DDD with proper covariates", False),
            ("TROP", "Factor-adjusted DiD (2025)", False),
            ("Honest DiD", "Rambachan-Roth sensitivity", False),
            ("Bacon Decomposition", "TWFE diagnostic weights", False),
        ]

        for i, (title, desc, is_new) in enumerate(methods):
            col = i % 2
            row = i // 2
            x = margin + col * (box_width + margin)
            y = y_start + row * (box_height + gap_y)

            self.set_fill_color(*WHITE)
            if is_new:
                self.set_draw_color(*TEAL)
                self.set_line_width(1.2)
            else:
                self.set_draw_color(*MID_BLUE)
                self.set_line_width(0.8)
            self.rect(x, y, box_width, box_height, "DF")

            # Title
            self.set_xy(x + 5, y + 3)
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(*TEAL if is_new else MID_BLUE)
            display_title = title + "  [NEW]" if is_new else title
            self.cell(box_width - 10, 10, display_title, align="C")

            # Description
            self.set_xy(x + 5, y + 19)
            self.set_font("Helvetica", "", 11)
            self.set_text_color(*GRAY)
            self.cell(box_width - 10, 10, desc, align="C")

        # Subtitle below grid
        grid_bottom = y_start + 5 * (box_height + gap_y)
        self.centered_text(
            grid_bottom + 2,
            "The most complete DiD toolkit in any language.",
            size=15, bold=False, color=GRAY,
        )
        self.add_footer()

    # ── Slide 10: CTA ─────────────────────────────────────────────────

    def slide_cta(self):
        """Slide 10: Upgrade today."""
        self.add_page()
        self.light_gradient_background()

        self.centered_text(45, "Upgrade to", size=38)
        self.centered_text(78, "v2.4", size=38, color=TEAL)

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

        self.centered_text(200, "github.com/igerber/diff-diff", size=20, color=MID_BLUE)

        self.centered_text(
            232, "Full documentation & 12 tutorials included",
            size=16, bold=False, color=GRAY,
        )
        self.centered_text(
            252, "MIT Licensed  |  Open Source",
            size=16, bold=False, color=GRAY,
        )

        self.draw_split_logo(278, size=28)

        self.centered_text(
            298, "Difference-in-Differences for Python",
            size=14, bold=False, color=GRAY,
        )



def main():
    pdf = CarouselV24PDF()

    pdf.slide_hook()
    pdf.slide_recap()
    pdf.slide_twfe_problem()
    pdf.slide_two_stage_intro()
    pdf.slide_math()
    pdf.slide_honest_se()
    pdf.slide_per_obs_effects()
    pdf.slide_code()
    pdf.slide_full_toolkit()
    pdf.slide_cta()

    output_path = Path(__file__).parent / "diff-diff-v24-carousel.pdf"
    pdf.output(str(output_path))
    print(f"PDF saved to: {output_path}")

    pdf.cleanup()


if __name__ == "__main__":
    main()
