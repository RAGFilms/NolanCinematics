"""
NolanCinematics — Blender Add-on
=============================================================
Replicates the full cinematographic pipeline of Christopher Nolan
productions — camera format, lens character, anamorphic DOF,
compositor optical chain, and per-film color grade.

Covers: Batman Begins, The Dark Knight, TDKR, Interstellar,
        Dunkirk, Oppenheimer.

Compatible: Blender 3.x / 4.x / 5.x
Author:     AGW ENTERTAINMENT
Version:    1.0.0
"""

bl_info = {
    "name":        "NolanCinematics",
    "author":      "AGW ENTERTAINMENT",
    "version":     (1, 0, 0),
    "blender":     (3, 0, 0),
    "location":    "3D Viewport › N-Panel › NolanCinematics",
    "description": "Full Nolan/Pfister/van Hoytema cinematography pipeline — "
                   "format, lens, anamorphic DOF, compositor, and per-film grade.",
    "category":    "Cinematics",
}

import bpy
import math
from bpy.props import (
    EnumProperty, FloatProperty, BoolProperty, IntProperty,
    StringProperty,
)
from bpy.types import Panel, Operator, PropertyGroup


# ================================================================
#  FILM GRADES
#  Lift / Gamma / Gain are 3-component RGB tuples for Blender's
#  ColorBalance node in ASC CDL mode. (Blender 4.x dropped the A channel.)
#  Lift:  0.0 = neutral, positive = lift shadows, negative = crush
#  Gamma: 1.0 = neutral
#  Gain:  1.0 = neutral
# ================================================================

FILM_GRADES = {

    'BEGINS': {
        'name':         "Batman Begins  (2005)",
        'dp':           "Wally Pfister ASC",
        'lenses':       "Panavision Primo anamorphic",
        'description':  (
            "Amber-warm interiors versus cold blue-grey exteriors. "
            "Ra's al Ghul sequences push yellow-green tint. "
            "Heavy shadow crush. Rich, saturated, theatrical."
        ),
        'lift':         ( 0.022,  0.016, -0.013),
        'gamma':        ( 1.055,  1.000,  0.935),
        'gain':         ( 1.000,  0.978,  1.055),
        'saturation':   0.875,
        'shadow_lift':  -0.055,    # negative = crush blacks
        'exposure':      0.0,
    },

    'TDK': {
        'name':         "The Dark Knight  (2008)",
        'dp':           "Wally Pfister ASC",
        'lenses':       "Panavision C- and H-Series anamorphic / IMAX spherical",
        'description':  (
            "Near-neutral, documentary clean. Slight green push in mids. "
            "The IMAX sequences are especially white and crisp. "
            "Maximum shadow crush. No stylization — Gotham is a real city."
        ),
        'lift':         ( 0.000,  0.006, -0.006),
        'gamma':        ( 1.000,  1.022,  0.978),
        'gain':         ( 1.000,  1.000,  0.972),
        'saturation':   0.980,
        'shadow_lift':  -0.068,
        'exposure':      0.0,
    },

    'TDKR': {
        'name':         "The Dark Knight Rises  (2012)",
        'dp':           "Wally Pfister ASC",
        'lenses':       "Panavision anamorphic / IMAX spherical",
        'description':  (
            "Coldest film in the trilogy. Heavy desaturation, "
            "blue pushed into shadows, flat overcast quality throughout. "
            "The Pit sequences go warm ochre as deliberate contrast."
        ),
        'lift':         (-0.013, -0.007,  0.020),
        'gamma':        ( 0.938,  0.942,  1.028),
        'gain':         ( 0.938,  0.950,  1.012),
        'saturation':   0.775,
        'shadow_lift':  -0.062,
        'exposure':     -0.10,
    },

    'INTERSTELLAR': {
        'name':         "Interstellar  (2014)",
        'dp':           "Hoyte van Hoytema FSF NSC",
        'lenses':       "Panavision anamorphic + IMAX spherical (65mm)",
        'description':  (
            "Warm on Earth, clinical cold in space. Extremely clean — "
            "van Hoytema resisted heavy grading. "
            "Strong IMAX sequences. Filmic but pristine."
        ),
        'lift':         ( 0.010,  0.005, -0.006),
        'gamma':        ( 1.022,  1.000,  0.978),
        'gain':         ( 1.012,  1.000,  0.978),
        'saturation':   0.948,
        'shadow_lift':  -0.045,
        'exposure':      0.10,
    },

    'DUNKIRK': {
        'name':         "Dunkirk  (2017)",
        'dp':           "Hoyte van Hoytema FSF NSC",
        'lenses':       "IMAX 65mm spherical / Panavision anamorphic 35mm",
        'description':  (
            "Desaturated, naturalistic. Grey-green overcast ocean light. "
            "Purely documentary in feel — zero stylization. "
            "Shot 75% IMAX. Extremely large frame, no wasted real estate."
        ),
        'lift':         (-0.006,  0.002,  0.003),
        'gamma':        ( 0.968,  0.978,  0.972),
        'gain':         ( 0.958,  0.972,  0.958),
        'saturation':   0.798,
        'shadow_lift':  -0.052,
        'exposure':     -0.15,
    },

    'OPPENHEIMER': {
        'name':         "Oppenheimer  (2023)",
        'dp':           "Hoyte van Hoytema FSF NSC",
        'lenses':       "IMAX 65mm / Panavision 65mm — no digital intermediate",
        'description':  (
            "High contrast, rich absolute blacks. Color sequences warm-neutral. "
            "B&W (Strauss POV) is stark and graphic. "
            "Shot on Kodak 65mm with visible grain. Extreme sharpness and punch."
        ),
        'lift':         ( 0.006,  0.003, -0.004),
        'gamma':        ( 1.012,  1.000,  0.990),
        'gain':         ( 1.022,  1.012,  0.980),
        'saturation':   0.920,
        'shadow_lift':  -0.078,
        'exposure':      0.05,
    },
}


# ================================================================
#  FORMAT / SENSOR SPECS
# ================================================================

FORMAT_SPECS = {
    'SCOPE_HD': {
        'name':           "Scope 1080p Preview  (2.39:1)",
        'res_x':          1920,
        'res_y':          804,
        'sensor_w':       36.0,
        'sensor_h':       24.0,
        'sensor_fit':     'HORIZONTAL',
        'aperture_ratio': 2.0,          # oval bokeh — anamorphic
        'distortion_k1':  -0.022,
        'desc':           "Fast preview renders. Full scope aspect ratio.",
    },
    'SCOPE_2K': {
        'name':           "Anamorphic Scope 2K  (2.39:1)",
        'res_x':          2048,
        'res_y':          858,
        'sensor_w':       36.0,
        'sensor_h':       24.0,
        'sensor_fit':     'HORIZONTAL',
        'aperture_ratio': 2.0,
        'distortion_k1':  -0.022,
        'desc':           "2048×858. Panavision anamorphic character.",
    },
    'SCOPE_4K': {
        'name':           "Anamorphic Scope 4K  (2.39:1)",
        'res_x':          4096,
        'res_y':          1716,
        'sensor_w':       36.0,
        'sensor_h':       24.0,
        'sensor_fit':     'HORIZONTAL',
        'aperture_ratio': 2.0,
        'distortion_k1':  -0.022,
        'desc':           "4096×1716. Full 4K scope output.",
    },
    'IMAX_2K': {
        'name':           "IMAX 15-perf 2K  (1.43:1)",
        'res_x':          2048,
        'res_y':          1433,
        'sensor_w':       70.41,
        'sensor_h':       52.48,
        'sensor_fit':     'AUTO',
        'aperture_ratio': 1.0,          # circular bokeh — spherical lens
        'distortion_k1':  -0.004,
        'desc':           "2048×1433. Full IMAX frame. Near-zero distortion.",
    },
    'IMAX_4K': {
        'name':           "IMAX 15-perf 4K  (1.43:1)",
        'res_x':          4096,
        'res_y':          2866,
        'sensor_w':       70.41,
        'sensor_h':       52.48,
        'sensor_fit':     'AUTO',
        'aperture_ratio': 1.0,
        'distortion_k1':  -0.004,
        'desc':           "4096×2866. Full 4K IMAX.",
    },
}


# ================================================================
#  FOCAL LENGTH PRESETS
# ================================================================

FOCAL_PRESETS = [
    ('F21',    "21mm — Environmental Wide",
               "Gotham scale and oppression. Maximum anamorphic distortion. City as villain."),
    ('F27',    "27mm — Wide Coverage",
               "Wide action, large groups, interiors. Mild distortion."),
    ('F40',    "40mm — Workhorse Normal",
               "Pfister's primary lens for dialogue and action. Near-zero distortion."),
    ('F50',    "50mm — Neutral Normal",
               "Close to human eye. Clean and natural."),
    ('F65',    "65mm — Long Normal",
               "Portraits and mid-close coverage. Slight background compression."),
    ('F100',   "100mm — Telephoto",
               "Isolation shots. City lights become horizontal oval bokeh streaks."),
    ('F150',   "150mm — Long Telephoto",
               "Extreme compression. Rooftop silhouettes against bokeh skylines."),
    ('CUSTOM', "Custom Focal Length",
               "Enter exact mm below."),
]

FOCAL_MM = {
    'F21': 21.0, 'F27': 27.0, 'F40': 40.0, 'F50': 50.0,
    'F65': 65.0, 'F100': 100.0, 'F150': 150.0,
}

APERTURE_PRESETS = [
    ('T1_9', "T1.9 — Wide Open Night",   "Max bokeh, very shallow focus. Night exteriors."),
    ('T2_8', "T2.8 — Standard Night",    "Primary night and interior setting. Pfister default."),
    ('T4',   "T4   — Day Interior",      "Controlled DOF. Day interior standard."),
    ('T5_6', "T5.6 — Day Exterior",      "Landscape and city exteriors stopped down."),
    ('T8',   "T8   — IMAX Deep Focus",   "IMAX maximum clarity. Near-infinite depth of field."),
]

APERTURE_FSTOP = {
    'T1_9': 1.9, 'T2_8': 2.8, 'T4': 4.0, 'T5_6': 5.6, 'T8': 8.0,
}


# ================================================================
#  COMPOSITOR HELPER
# ================================================================

def _set_socket(node, name, index, value):
    """Set a node socket value by name, falling back to index.
    Silently skips if neither is available — guards against
    Blender 4.x socket renames."""
    try:
        node.inputs[name].default_value = value
        return
    except (KeyError, TypeError):
        pass
    try:
        node.inputs[index].default_value = value
    except (IndexError, TypeError):
        pass




def _clear_nc_nodes(tree):
    """Remove all NC_-prefixed nodes from the compositor tree."""
    for node in list(tree.nodes):
        if node.name.startswith("NC_"):
            tree.nodes.remove(node)


def build_compositor(context):
    scene  = context.scene
    props  = scene.nolan_cinematics
    grade  = FILM_GRADES.get(props.film_grade, FILM_GRADES['TDK'])

    scene.use_nodes = True
    tree   = scene.node_tree
    nodes  = tree.nodes
    links  = tree.links

    _clear_nc_nodes(tree)

    # Anchor nodes — locate or create
    rl = next((n for n in nodes if n.type == 'R_LAYERS'),  None)
    co = next((n for n in nodes if n.type == 'COMPOSITE'), None)

    if rl is None:
        rl          = nodes.new('CompositorNodeRLayers')
        rl.location = (0, 300)

    if co is None:
        co          = nodes.new('CompositorNodeComposite')
        co.location = (2600, 300)

    x   = rl.location.x + 340
    y   = rl.location.y
    GAP = 290

    prev = rl.outputs['Image']

    # ── 1 · Lens Distortion + Chromatic Aberration ────────────────
    if props.enable_distortion:
        ld             = nodes.new('CompositorNodeLensdist')
        ld.name        = "NC_LensDistortion"
        ld.label       = "NC · Lens Distortion"
        ld.location    = (x, y)
        # Use both name and index fallback for 4.x compatibility
        _set_socket(ld, 'Distortion', 1, props.distortion_k1)
        _set_socket(ld, 'Dispersion', 2, props.chromatic_aberration)
        links.new(prev, ld.inputs[0])
        prev = ld.outputs['Image']
        x   += GAP

    # ── 2 · Anamorphic Flare Streaks ──────────────────────────────
    if props.enable_flare:
        gl                  = nodes.new('CompositorNodeGlare')
        gl.name             = "NC_AnamorphicFlare"
        gl.label            = "NC · Anamorphic Flare"
        gl.location         = (x, y)
        gl.glare_type       = 'STREAKS'
        gl.streaks          = 2
        gl.angle_offset     = 0.0
        gl.threshold        = 0.88
        gl.fade             = 0.92
        gl.iterations       = 3
        try:
            gl.color_modulation = 0.15
        except AttributeError:
            pass  # renamed in some 4.x builds
        gl.mix = -1.0 + (props.flare_intensity * 0.65)
        links.new(prev, gl.inputs['Image'])
        prev = gl.outputs['Image']
        x   += GAP

    # ── 3 · Film Color Grade (Lift / Gamma / Gain) ────────────────
    if props.enable_grade:
        cb                      = nodes.new('CompositorNodeColorBalance')
        cb.name                 = "NC_FilmGrade"
        cb.label                = f"NC · Grade · {grade['name']}"
        cb.location             = (x, y)
        cb.correction_method    = 'LIFT_GAMMA_GAIN'
        # Blender 4.x uses 3-component RGB tuples (not RGBA)
        cb.lift                 = grade['lift']
        cb.gamma                = grade['gamma']
        cb.gain                 = grade['gain']
        links.new(prev, cb.inputs['Image'])
        prev = cb.outputs['Image']
        x   += GAP

        # Saturation — use index access for 4.x socket name safety
        hs          = nodes.new('CompositorNodeHueSat')
        hs.name     = "NC_Saturation"
        hs.label    = "NC · Saturation"
        hs.location = (x, y)
        # index 0=Image 1=Hue 2=Saturation 3=Value 4=Fac
        try:
            hs.inputs[2].default_value = grade['saturation'] * props.saturation_mult
        except (IndexError, AttributeError):
            _set_socket(hs, 'Saturation', 2, grade['saturation'] * props.saturation_mult)
        links.new(prev, hs.inputs[0])
        prev = hs.outputs['Image']
        x   += GAP

    # ── 4 · Shadow Crush ──────────────────────────────────────────
    if props.enable_shadow_crush:
        sc                   = nodes.new('CompositorNodeColorBalance')
        sc.name              = "NC_ShadowCrush"
        sc.label             = "NC · Shadow Crush"
        sc.location          = (x, y)
        sc.correction_method = 'LIFT_GAMMA_GAIN'
        sc.inputs['Fac'].default_value = 0.5   # 0.5 = subtle crush; 1.0 is too aggressive
        crush = grade['shadow_lift'] * props.shadow_crush_amount
        # 3-component RGB tuples for Blender 4.x
        sc.lift  = (crush, crush, crush)
        sc.gamma = (1.0, 1.0, 1.0)
        sc.gain  = (1.0, 1.0, 1.0)
        links.new(prev, sc.inputs['Image'])
        prev = sc.outputs['Image']
        x   += GAP

    # ── 5 · Vignette (Ellipse Mask → Gaussian Blur → Multiply) ───
    if props.enable_vignette:
        vx = x
        vy = y - 300

        em          = nodes.new('CompositorNodeEllipseMask')
        em.name     = "NC_VignetteMask"
        em.label    = "NC · Vignette Mask"
        em.location = (vx, vy)
        em.width    = props.vignette_size
        em.height   = props.vignette_size * 0.72

        bl              = nodes.new('CompositorNodeBlur')
        bl.name         = "NC_VignetteBlur"
        bl.label        = "NC · Vignette Blur"
        bl.location     = (vx + GAP, vy)
        bl.filter_type  = 'GAUSS'
        bl.size_x       = 130
        bl.size_y       = 130
        bl.use_relative = False
        links.new(em.outputs['Mask'], bl.inputs['Image'])

        # Mix multiply: image × mask = bright center, dark edges
        mx             = nodes.new('CompositorNodeMixRGB')
        mx.name        = "NC_VignetteMix"
        mx.label       = "NC · Vignette Mix"
        mx.location    = (x, y)
        mx.blend_type  = 'MULTIPLY'
        mx.inputs[0].default_value = props.vignette_intensity  # Fac
        links.new(prev,                mx.inputs[1])
        links.new(bl.outputs['Image'], mx.inputs[2])
        prev = mx.outputs['Image']
        x   += GAP * 2

    # ── 6 · Output Nodes ──────────────────────────────────────────
    co.location = (x + GAP * 0.4, y)
    links.new(prev, co.inputs['Image'])

    vn          = nodes.new('CompositorNodeViewer')
    vn.name     = "NC_Viewer"
    vn.label    = "NC · Viewer"
    vn.location = (x + GAP * 0.4, y - 220)
    links.new(prev, vn.inputs['Image'])

    return True


# ================================================================
#  LIVE NODE UPDATE HELPERS
#  Called by property update= callbacks. Directly poke existing
#  NC_ compositor nodes so sliders respond in real time without
#  requiring a full Rebuild.
# ================================================================

def _nc_node(context, name):
    """Return a compositor node by name, or None."""
    scene = context.scene
    if scene.use_nodes and scene.node_tree:
        return scene.node_tree.nodes.get(name)
    return None


def _upd_saturation(self, context):
    node = _nc_node(context, 'NC_Saturation')
    if node:
        grade = FILM_GRADES.get(self.film_grade, {})
        node.inputs[2].default_value = grade.get('saturation', 1.0) * self.saturation_mult


def _upd_grade_fac(self, context):
    node = _nc_node(context, 'NC_FilmGrade')
    if node:
        node.inputs[0].default_value = self.grade_fac


def _upd_shadow_fac(self, context):
    node = _nc_node(context, 'NC_ShadowCrush')
    if node:
        node.inputs[0].default_value = self.shadow_crush_fac


def _upd_shadow_amount(self, context):
    node = _nc_node(context, 'NC_ShadowCrush')
    if node:
        grade = FILM_GRADES.get(self.film_grade, {})
        crush = grade.get('shadow_lift', -0.06) * self.shadow_crush_amount
        node.lift = (crush, crush, crush)


def _upd_flare(self, context):
    node = _nc_node(context, 'NC_AnamorphicFlare')
    if node:
        node.mix = -1.0 + (self.flare_intensity * 0.65)


def _upd_distortion(self, context):
    node = _nc_node(context, 'NC_LensDistortion')
    if node:
        try:
            node.inputs['Distortion'].default_value = self.distortion_k1
        except KeyError:
            try: node.inputs[1].default_value = self.distortion_k1
            except Exception: pass


def _upd_chromatic(self, context):
    node = _nc_node(context, 'NC_LensDistortion')
    if node:
        try:
            node.inputs['Dispersion'].default_value = self.chromatic_aberration
        except KeyError:
            try: node.inputs[2].default_value = self.chromatic_aberration
            except Exception: pass


def _upd_vignette_intensity(self, context):
    node = _nc_node(context, 'NC_VignetteMix')
    if node:
        node.inputs[0].default_value = self.vignette_intensity


def _upd_vignette_size(self, context):
    mask = _nc_node(context, 'NC_VignetteMask')
    if mask:
        mask.width  = self.vignette_size
        mask.height = self.vignette_size * 0.72


def _upd_exposure(self, context):
    if hasattr(context.scene, 'cycles'):
        context.scene.cycles.film_exposure = self.exposure


def _upd_bokeh_ratio(self, context):
    cam_obj = context.active_object
    if cam_obj is None or cam_obj.type != 'CAMERA':
        cam_obj = next(
            (o for o in context.scene.objects if o.type == 'CAMERA'), None
        )
    if cam_obj:
        cam_obj.data.dof.aperture_ratio = self.bokeh_ratio


# ================================================================
#  PROPERTIES
# ================================================================

def _grade_items(self, context):
    return [(k, v['name'], v['description']) for k, v in FILM_GRADES.items()]


class NolanCinematicsProperties(PropertyGroup):

    # ── Film & Format ─────────────────────────────────────────────
    film_grade: EnumProperty(
        name        = "Film Grade",
        items       = _grade_items,
        description = "Color grade from a Nolan production",
    )
    format_mode: EnumProperty(
        name  = "Format",
        items = [
            ('SCOPE_HD',  "Scope 1080p Preview (2.39)",  "1920×804, fast preview"),
            ('SCOPE_2K',  "Anamorphic Scope 2K  (2.39)", "2048×858"),
            ('SCOPE_4K',  "Anamorphic Scope 4K  (2.39)", "4096×1716"),
            ('IMAX_2K',   "IMAX 1.43:1  2K",             "2048×1433"),
            ('IMAX_4K',   "IMAX 1.43:1  4K",             "4096×2866"),
        ],
        default = 'SCOPE_HD',
    )

    # ── Focal / Aperture ──────────────────────────────────────────
    focal_preset: EnumProperty(
        name    = "Focal Length",
        items   = FOCAL_PRESETS,
        default = 'F40',
    )
    custom_focal: FloatProperty(
        name = "Custom mm", default = 50.0, min = 10.0, max = 600.0, precision = 1,
    )
    aperture_preset: EnumProperty(
        name    = "Aperture",
        items   = APERTURE_PRESETS,
        default = 'T2_8',
    )

    # ── Compositor Toggles ────────────────────────────────────────
    enable_distortion:   BoolProperty(name = "Lens Distortion",   default = True)
    enable_flare:        BoolProperty(name = "Anamorphic Flare",  default = True)
    enable_grade:        BoolProperty(name = "Film Grade",        default = True)
    enable_shadow_crush: BoolProperty(name = "Shadow Crush",      default = True)
    enable_vignette:     BoolProperty(name = "Vignette",          default = True)

    # ── Compositor Parameters  (all have live update callbacks) ───

    # Exposure
    exposure: FloatProperty(
        name        = "Exposure",
        description = "Cycles film exposure. 0.0 = film-accurate baseline.",
        default     = 0.0, min = -3.0, max = 3.0, precision = 2,
        update      = _upd_exposure,
    )

    # Grade
    grade_fac: FloatProperty(
        name        = "Grade Strength",
        description = "Fac on the film colour balance node. 1.0 = full grade, 0.0 = bypass.",
        default     = 1.0, min = 0.0, max = 1.0, subtype = 'FACTOR',
        update      = _upd_grade_fac,
    )
    saturation_mult: FloatProperty(
        name        = "Saturation",
        description = "Multiplier on the film's baseline saturation. 1.0 = film-accurate.",
        default     = 1.0, min = 0.0, max = 2.0, subtype = 'FACTOR',
        update      = _upd_saturation,
    )

    # Shadow Crush
    shadow_crush_fac: FloatProperty(
        name        = "Crush Blend",
        description = "How much the shadow crush node blends in. 0.5 = default safe start.",
        default     = 0.5, min = 0.0, max = 1.0, subtype = 'FACTOR',
        update      = _upd_shadow_fac,
    )
    shadow_crush_amount: FloatProperty(
        name        = "Crush Depth",
        description = "Depth of the black crush lift. 1.0 = film-accurate baseline.",
        default     = 1.0, min = 0.0, max = 2.5, subtype = 'FACTOR',
        update      = _upd_shadow_amount,
    )

    # Flare
    flare_intensity: FloatProperty(
        name        = "Flare Intensity",
        description = "Horizontal anamorphic streak intensity from bright sources.",
        default     = 0.38, min = 0.0, max = 1.0, subtype = 'FACTOR',
        update      = _upd_flare,
    )

    # Lens Distortion
    distortion_k1: FloatProperty(
        name        = "Barrel (K1)",
        description = "Negative = barrel. -0.022 anamorphic, -0.004 IMAX.",
        default     = -0.022, min = -0.20, max = 0.20, precision = 4,
        update      = _upd_distortion,
    )
    chromatic_aberration: FloatProperty(
        name        = "Chromatic Ab.",
        description = "Edge fringing on high-contrast lines. Keep ≤ 0.01.",
        default     = 0.003, min = 0.0, max = 0.05, precision = 4,
        update      = _upd_chromatic,
    )

    # Anamorphic bokeh
    bokeh_ratio: FloatProperty(
        name        = "Bokeh Ratio",
        description = "1.0 = circular (spherical/IMAX). 2.0 = oval anamorphic.",
        default     = 2.0, min = 0.5, max = 4.0, precision = 2,
        update      = _upd_bokeh_ratio,
    )

    # Vignette
    vignette_intensity: FloatProperty(
        name        = "Vignette",
        description = "0 = off. ~0.6 is Pfister's typical scope value.",
        default     = 0.62, min = 0.0, max = 1.0, subtype = 'FACTOR',
        update      = _upd_vignette_intensity,
    )
    vignette_size: FloatProperty(
        name        = "Clear Center",
        description = "Bright zone size. Smaller = more aggressive vignette.",
        default     = 0.80, min = 0.30, max = 1.0, subtype = 'FACTOR',
        update      = _upd_vignette_size,
    )




# ================================================================
#  OPERATORS
# ================================================================

class NC_OT_SetupCamera(Operator):
    bl_idname     = "nolan_cinematics.setup_camera"
    bl_label      = "Setup Camera"
    bl_description = "Configure active camera: sensor, focal, DOF, anamorphic bokeh ratio"

    def execute(self, context):
        scene  = context.scene
        props  = scene.nolan_cinematics
        fmt    = FORMAT_SPECS[props.format_mode]
        grade  = FILM_GRADES[props.film_grade]

        # Render resolution
        scene.render.resolution_x          = fmt['res_x']
        scene.render.resolution_y          = fmt['res_y']
        scene.render.resolution_percentage = 100

        # Cycles film exposure
        if hasattr(scene, 'cycles'):
            scene.cycles.film_exposure = 1.0 + grade['exposure']

        # Sync distortion K1 to the format
        props.distortion_k1 = fmt['distortion_k1']

        # Find camera
        cam_obj = context.active_object
        if cam_obj is None or cam_obj.type != 'CAMERA':
            cam_obj = next(
                (o for o in scene.objects if o.type == 'CAMERA'), None
            )
        if cam_obj is None:
            self.report({'WARNING'},
                "No camera in scene — render settings applied. "
                "Add a camera to apply lens settings.")
            return {'FINISHED'}

        cam = cam_obj.data

        # Sensor
        cam.sensor_fit    = fmt['sensor_fit']
        cam.sensor_width  = fmt['sensor_w']
        cam.sensor_height = fmt['sensor_h']

        # Focal length
        if props.focal_preset == 'CUSTOM':
            cam.lens = props.custom_focal
        else:
            cam.lens = FOCAL_MM.get(props.focal_preset, 40.0)

        # Depth of field
        cam.dof.use_dof           = True
        f_stop                    = APERTURE_FSTOP.get(props.aperture_preset, 2.8)
        cam.dof.aperture_fstop    = f_stop
        # aperture_ratio > 1.0 = wider bokeh = anamorphic horizontal oval
        cam.dof.aperture_ratio    = fmt['aperture_ratio']
        cam.dof.aperture_rotation = 0.0   # keep horizontal

        self.report({'INFO'},
            f"Camera set: {fmt['name']} | "
            f"{cam.lens:.0f}mm | T{f_stop} | "
            f"bokeh ratio {fmt['aperture_ratio']:.1f}×")
        return {'FINISHED'}


class NC_OT_BuildCompositor(Operator):
    bl_idname     = "nolan_cinematics.build_compositor"
    bl_label      = "Build Compositor"
    bl_description = "Build the NolanCinematics compositor node chain"

    def execute(self, context):
        build_compositor(context)
        self.report({'INFO'}, "NolanCinematics compositor built.")
        return {'FINISHED'}


class NC_OT_RebuildCompositor(Operator):
    bl_idname     = "nolan_cinematics.rebuild_compositor"
    bl_label      = "Rebuild"
    bl_description = "Clear and rebuild compositor — use after changing grade or format"

    def execute(self, context):
        scene = context.scene
        if scene.use_nodes and scene.node_tree:
            _clear_nc_nodes(scene.node_tree)
        build_compositor(context)
        self.report({'INFO'}, "NolanCinematics compositor rebuilt.")
        return {'FINISHED'}


class NC_OT_ClearCompositor(Operator):
    bl_idname     = "nolan_cinematics.clear_compositor"
    bl_label      = "Clear NC Nodes"
    bl_description = "Remove all NC_ nodes from the compositor. User nodes untouched."

    def execute(self, context):
        scene = context.scene
        if scene.use_nodes and scene.node_tree:
            _clear_nc_nodes(scene.node_tree)
        self.report({'INFO'}, "NolanCinematics nodes cleared.")
        return {'FINISHED'}


class NC_OT_QuickSetup(Operator):
    bl_idname     = "nolan_cinematics.quick_setup"
    bl_label      = "QUICK SETUP"
    bl_description = "Configure camera AND build compositor in one shot"

    def execute(self, context):
        bpy.ops.nolan_cinematics.setup_camera()
        bpy.ops.nolan_cinematics.rebuild_compositor()
        self.report({'INFO'}, "NolanCinematics pipeline applied.")
        return {'FINISHED'}


# ================================================================
#  PANELS  —  N-Panel tab in 3D Viewport
# ================================================================

class NC_PT_Main(Panel):
    bl_label      = "NolanCinematics"
    bl_idname     = "NC_PT_Main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "NolanCinematics"

    def draw(self, context):
        layout = self.layout
        props  = context.scene.nolan_cinematics
        grade  = FILM_GRADES.get(props.film_grade, {})

        # ── Film Selector ─────────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Film Style", icon='CAMERA_DATA')
        col.prop(props, "film_grade", text="")

        if grade:
            info = box.column(align=True)
            info.scale_y = 0.72
            info.label(text=f"DP: {grade.get('dp', '')}", icon='COMMUNITY')
            info.label(text=f"Glass: {grade.get('lenses', '')}", icon='LIGHT_SPOT')
            desc = grade.get('description', '')
            # Wrap at ~54 chars
            for i in range(0, len(desc), 54):
                info.label(text=desc[i:i+54])

        layout.separator()

        # ── Format Selector ───────────────────────────────────────
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Format / Resolution", icon='RENDER_RESULT')
        col.prop(props, "format_mode", text="")
        fmt = FORMAT_SPECS.get(props.format_mode, {})
        if fmt:
            box.label(text=fmt.get('desc', ''), icon='INFO')

        layout.separator()

        # ── QUICK SETUP ───────────────────────────────────────────
        row = layout.row()
        row.scale_y = 2.0
        row.operator("nolan_cinematics.quick_setup",
                     text="⚡  QUICK SETUP  ⚡", icon='LIGHT_SUN')


class NC_PT_CameraLens(Panel):
    bl_label      = "Camera & Lens"
    bl_idname     = "NC_PT_CameraLens"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "NolanCinematics"
    bl_parent_id  = "NC_PT_Main"
    bl_options    = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props  = context.scene.nolan_cinematics

        layout.prop(props, "focal_preset", text="Focal")

        if props.focal_preset == 'CUSTOM':
            layout.prop(props, "custom_focal")

        # Focal description
        for item in FOCAL_PRESETS:
            if item[0] == props.focal_preset:
                b = layout.box()
                b.scale_y = 0.70
                desc = item[2]
                for i in range(0, len(desc), 50):
                    b.label(text=desc[i:i+50])
                break

        layout.separator()
        layout.prop(props, "aperture_preset", text="Aperture")

        layout.separator()
        layout.operator("nolan_cinematics.setup_camera",
                        text="Apply to Camera", icon='CAMERA_DATA')

        # Live camera readout
        cam_obj = context.active_object
        if cam_obj and cam_obj.type == 'CAMERA':
            cam = cam_obj.data
            fmt = FORMAT_SPECS.get(props.format_mode, {})
            b   = layout.box()
            col = b.column(align=True)
            col.scale_y = 0.78
            col.label(text=f"Lens:    {cam.lens:.1f}mm")
            col.label(text=f"Aperture: T{cam.dof.aperture_fstop:.1f}")
            col.label(text=f"Sensor:  {cam.sensor_width:.1f} × {cam.sensor_height:.1f}mm")
            col.label(text=f"Bokeh ratio: {fmt.get('aperture_ratio', 1.0):.1f}× "
                           f"({'oval — anamorphic' if fmt.get('aperture_ratio',1)>1 else 'circular — spherical'})")
            col.label(text=f"Resolution: {fmt.get('res_x','?')}×{fmt.get('res_y','?')}")


class NC_PT_ShotControls(Panel):
    bl_label      = "Per-Shot Controls"
    bl_idname     = "NC_PT_ShotControls"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "NolanCinematics"
    bl_parent_id  = "NC_PT_Main"
    bl_order      = 5

    def draw(self, context):
        layout = self.layout
        props  = context.scene.nolan_cinematics

        # ── Exposure ──────────────────────────────────────────────
        box = layout.box()
        box.label(text="Exposure", icon='LIGHT_SUN')
        box.prop(props, "exposure", slider=True, text="Film Exposure")

        # ── Grade ─────────────────────────────────────────────────
        box = layout.box()
        box.label(text="Film Grade", icon='COLOR')
        col = box.column(align=True)
        col.prop(props, "grade_fac",       slider=True, text="Grade Strength")
        col.prop(props, "saturation_mult", slider=True, text="Saturation")

        # ── Shadow Crush ──────────────────────────────────────────
        box = layout.box()
        box.label(text="Shadow Crush", icon='SHADING_RENDERED')
        col = box.column(align=True)
        col.prop(props, "shadow_crush_fac",    slider=True, text="Blend")
        col.prop(props, "shadow_crush_amount", slider=True, text="Depth")

        # ── Anamorphic ────────────────────────────────────────────
        box = layout.box()
        box.label(text="Anamorphic", icon='CAMERA_DATA')
        col = box.column(align=True)
        col.prop(props, "bokeh_ratio",     slider=True, text="Bokeh Ratio")
        col.prop(props, "flare_intensity", slider=True, text="Flare Streaks")

        # ── Lens Distortion ───────────────────────────────────────
        box = layout.box()
        box.label(text="Lens Distortion", icon='SPHERECURVE')
        col = box.column(align=True)
        col.prop(props, "distortion_k1",        text="Barrel K1")
        col.prop(props, "chromatic_aberration",  text="Chromatic Ab.")

        # ── Vignette ──────────────────────────────────────────────
        box = layout.box()
        box.label(text="Vignette", icon='ANTIALIASED')
        col = box.column(align=True)
        col.prop(props, "vignette_intensity", slider=True, text="Intensity")
        col.prop(props, "vignette_size",      slider=True, text="Clear Center")

        # ── Status strip ──────────────────────────────────────────
        layout.separator()
        scene = context.scene
        if scene.use_nodes and scene.node_tree:
            nc_nodes = [n for n in scene.node_tree.nodes if n.name.startswith("NC_")]
            if nc_nodes:
                layout.label(text=f"● {len(nc_nodes)} NC nodes live", icon='CHECKMARK')
            else:
                layout.label(text="○ Build compositor first", icon='ERROR')


class NC_PT_Compositor(Panel):
    bl_label      = "Compositor Pipeline"
    bl_idname     = "NC_PT_Compositor"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "NolanCinematics"
    bl_parent_id  = "NC_PT_Main"
    bl_options    = {'DEFAULT_CLOSED'}
    bl_order      = 15

    def draw(self, context):
        layout = self.layout
        props  = context.scene.nolan_cinematics

        # ── Enable / Disable toggles ──────────────────────────────
        box = layout.box()
        box.label(text="Enable / Disable Stages", icon='NODETREE')
        col = box.column(align=True)
        col.prop(props, "enable_distortion",   text="Lens Distortion",  icon='SPHERECURVE')
        col.prop(props, "enable_flare",        text="Anamorphic Flare", icon='LIGHT_SPOT')
        col.prop(props, "enable_grade",        text="Film Grade",       icon='COLOR')
        col.prop(props, "enable_shadow_crush", text="Shadow Crush",     icon='SHADING_RENDERED')
        col.prop(props, "enable_vignette",     text="Vignette",         icon='ANTIALIASED')

        layout.separator()

        # ── Build / Rebuild / Clear ───────────────────────────────
        row = layout.row(align=True)
        row.operator("nolan_cinematics.build_compositor",
                     text="Build",   icon='NODETREE')
        row.operator("nolan_cinematics.rebuild_compositor",
                     text="Rebuild", icon='FILE_REFRESH')
        layout.operator("nolan_cinematics.clear_compositor",
                        text="Clear NC Nodes", icon='X')

        # ── Status ────────────────────────────────────────────────
        scene = context.scene
        if scene.use_nodes and scene.node_tree:
            nc_nodes = [n for n in scene.node_tree.nodes if n.name.startswith("NC_")]
            if nc_nodes:
                layout.label(text=f"● {len(nc_nodes)} NC nodes active", icon='CHECKMARK')
            else:
                layout.label(text="○ No NC nodes — click Build",        icon='INFO')




class NC_PT_Tips(Panel):
    bl_label      = "Lighting Notes"
    bl_idname     = "NC_PT_Tips"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "NolanCinematics"
    bl_parent_id  = "NC_PT_Main"
    bl_options    = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props  = context.scene.nolan_cinematics

        tips = {
            'BEGINS': [
                "Every light has a visible source.",
                "Amber practical fill for interiors.",
                "Cold blue LED/HMI for exteriors.",
                "Ra's scenes: push slight green-yellow.",
                "Hard shadows. No beauty fill on Batman.",
            ],
            'TDK': [
                "Nolan's rule: motivated light only.",
                "Joker scenes: green-tinted fluorescents.",
                "No fill light in interrogation scenes.",
                "IMAX: overexpose 1/3 stop for punch.",
                "Gotham=Chicago: don't make it weird.",
            ],
            'TDKR': [
                "Overcast sky as key light everywhere.",
                "Suppress saturation globally.",
                "Pit sequences: go warm, break the cold.",
                "Batman suit in shadow: it disappears.",
                "Bane's light is always flat and hard.",
            ],
            'INTERSTELLAR': [
                "Earth = warm 3200K practicals.",
                "Space = 5600K hard, zero fill.",
                "Gargantua: single point source only.",
                "Interiors: natural window light only.",
                "van Hoytema: 'Just turn the lights off.'",
            ],
            'DUNKIRK': [
                "Overcast = single soft top key.",
                "No color grading in photography.",
                "Handheld for all beach sequences.",
                "Shoot into sun for beach flares.",
                "Water reflections do the work.",
            ],
            'OPPENHEIMER': [
                "Trinity explosion: 65mm wide, no VFX.",
                "Boardroom: hard bare bulb overhead.",
                "Hearing rooms: cold fluorescent base.",
                "Color desaturates toward climax.",
                "B&W sections: 1.0 contrast, hard blacks.",
            ],
        }

        film_tips = tips.get(props.film_grade, [])
        col = layout.column(align=True)
        col.scale_y = 0.82
        for tip in film_tips:
            col.label(text=f"  • {tip}")


# ================================================================
#  REGISTRATION
# ================================================================

CLASSES = [
    NolanCinematicsProperties,
    NC_OT_SetupCamera,
    NC_OT_BuildCompositor,
    NC_OT_RebuildCompositor,
    NC_OT_ClearCompositor,
    NC_OT_QuickSetup,
    NC_PT_Main,
    NC_PT_ShotControls,
    NC_PT_CameraLens,
    NC_PT_Compositor,
    NC_PT_Tips,
]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.nolan_cinematics = bpy.props.PointerProperty(
        type=NolanCinematicsProperties
    )
    print("[NolanCinematics] Registered — pipeline ready.")


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.nolan_cinematics
    print("[NolanCinematics] Unregistered.")


if __name__ == "__main__":
    register()
