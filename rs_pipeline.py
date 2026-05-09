import sys
import subprocess
import xml.etree.ElementTree as ET

from pathlib import Path

# =====================================================
# CONFIG
# =====================================================

TRAINER = "brush" # "lichtfeld"

PARAMS_XML = r"""<?xml version="1.0" encoding="utf-8"?>
<Configuration>
  <entry key="calexFolder" value="C:/Temp"/>
  <entry key="calexUndistResMode" value="2"/>
  <entry key="calexUndistPrincipal" value="true"/>
  <entry key="calexTrans" value="1"/>
  <entry key="calexUndistortNaming" value="1"/>
  <entry key="calexUndistortPixelFormat" value="24bppBGR"/>
  <entry key="calexUndistortImageFormat" value="png"/>
  <entry key="calexHasDisabled" value="0x0"/>
  <entry key="calexRequiresUndistortPrincipal" value="0x0"/>
  <entry key="calexExportImages" value="true"/>
  <entry key="MvsExportScaleZ" value="1.0"/>
  <entry key="MvsExportIsGeoreferenced" value="0x1"/>
  <entry key="MvsExportIsModelCoordinates" value="0"/>
  <entry key="colmapDirStructure" value="0"/>
  <entry key="calexRequiresColorCorrection" value="0x1"/>
  <entry key="MvsExportScaleY" value="1.0"/>
  <entry key="calexRequiresEqualResolution" value="0x0"/>
  <entry key="calexDownscale" value="0x1"/>
  <entry key="calexUndistMaxPixels" value="0x0"/>
  <entry key="calexInputHasLayers" value="1"/>
  <entry key="calexCorrectColors" value="true"/>
  <entry key="MvsExportScaleX" value="1.0"/>
  <entry key="calexUndistFitMode" value="4"/>
  <entry key="MvsExportRotationY" value="0.0"/>
  <entry key="MvsExportcoordinatesystemtype" value="0"/>
  <entry key="MvsExportNormalFlipZ" value="false"/>
  <entry key="MvsExportRotationX" value="0.0"/>
  <entry key="calexFolderCustom" value="true"/>
  <entry key="hasCalexFilePath" value="1"/>
  <entry key="MvsExportNormalFlipY" value="false"/>
  <entry key="MvsExportNormalSpace" value="Mikktspace"/>
  <entry key="calexHasUndistort" value="1"/>
  <entry key="colmapExportMasks" value="false"/>
  <entry key="MvsExportNormalFlipX" value="false"/>
  <entry key="MvsExportRotationZ" value="0.0"/>
  <entry key="calexExportUndistorted" value="true"/>
  <entry key="colmapFileType" value="CFT_TXT"/>
  <entry key="calexFileFormat" value="COLMAP"/>
  <entry key="MvsExportMoveZ" value="0.0"/>
  <entry key="calexFileFormatId" value="{280B11A4-F9A3-47D1-AE58-C0DEA33487D8}"/>
  <entry key="calexImageLayerOptions" value="0"/>
  <entry key="calexUndistBackColor" value="0"/>
  <entry key="hasRadianceFieldsTransAABB" value="0"/>
  <entry key="hasCalexFileName" value="1"/>
  <entry key="calexUndistCutOut" value="1.0"/>
  <entry key="calexHasImageExport" value="1"/>
  <entry key="MvsExportMoveX" value="0.0"/>
  <entry key="MvsExportNormalRange" value="ZeroToOne"/>
  <entry key="MvsExportMoveY" value="0.0"/>
</Configuration>
"""

# =====================================================
# ARGS
# =====================================================

if len(sys.argv) < 2:

    print()
    print("Usage:")
    print(
        "python rs_pipeline.py "
        "<input_dir> "
        "[RealityScan folder]"
    )
    print()

    sys.exit(1)

INPUT_DIR = Path(sys.argv[1]).resolve()

# Optional RealityScan folder
if len(sys.argv) >= 3:

    RS_FOLDER = Path(sys.argv[2]).resolve()

else:

    RS_FOLDER = Path(
        r"P:\Programme\Epic Games\RealityScan_2.1"
    )

# =====================================================
# PATHS
# =====================================================

PROJECT_DIR = INPUT_DIR.parent

RS_EXE = RS_FOLDER / "RealityScan.exe"

# =====================================================
# CHECKS
# =====================================================

if not INPUT_DIR.exists():

    raise RuntimeError(
        f"Input folder not found:\n{INPUT_DIR}"
    )

if not RS_EXE.exists():

    raise RuntimeError(
        f"RealityScan.exe not found:\n{RS_EXE}"
    )

# =====================================================
# PATCH XML
# =====================================================

print()
print("Patching params.xml...")
print()

root = ET.fromstring(PARAMS_XML)

tree = ET.ElementTree(root)

export_path = PROJECT_DIR.as_posix() + "/"

patched = False

for entry in root.iter("entry"):

    if entry.attrib.get("key") == "calexFolder":

        print("Old calexFolder:")
        print(entry.attrib.get("value"))

        entry.set("value", export_path)

        print()
        print("New calexFolder:")
        print(export_path)

        patched = True
        break

if not patched:

    raise RuntimeError(
        "calexFolder not found in embedded params.xml"
    )

# =====================================================
# SAVE PATCHED XML
# =====================================================

RS_PARAMS = PROJECT_DIR / "rs_params.xml"

tree.write(
    RS_PARAMS,
    encoding="utf-8",
    xml_declaration=True
)

print()
print("Saved:")
print(RS_PARAMS)

# =====================================================
# REALITYSCAN COMMAND
# =====================================================

cmd = [

    str(RS_EXE),

    # "-headless",
    "-hideUI",
    "-stdConsole",

    "-newScene",

    "-addFolder",
    str(INPUT_DIR),

    "-generateAIMasks",

    "-align",

    "-exportRegistration",
    str(PROJECT_DIR),
    str(RS_PARAMS),

    "-quit",
]

print()
print("Running RealityScan:")
print()

print(" ".join(cmd))
print()

# =====================================================
# RUN REALITYSCAN
# =====================================================

result = subprocess.run(cmd)

if result.returncode != 0:

    raise RuntimeError(
        f"RealityScan failed: {result.returncode}"
    )

# =====================================================
# VERIFY OUTPUT
# =====================================================

required = [

    PROJECT_DIR / "images",
    PROJECT_DIR / "sparse/0/cameras.txt",
    PROJECT_DIR / "sparse/0/images.txt",
    PROJECT_DIR / "sparse/0/points3D.txt",
]

missing = []

for path in required:

    if not path.exists():

        missing.append(path)

if missing:

    print()

    for m in missing:

        print("Missing:", m)

    raise RuntimeError(
        "RealityScan export incomplete"
    )

print()
print("RealityScan export successful.")
print()

# =====================================================
# START TRAINER
# =====================================================

if TRAINER == "brush":

    print("==========================================")
    print("Starting Brush")
    print("==========================================")
    print()

    cmd = [

        "brush_app",

        str(PROJECT_DIR),

        "--total-steps", "10000",
        "--max-resolution", "1920",
        "--export-every", "5000",

        "--export-path",
        str(PROJECT_DIR / "brush"),
    ]

elif TRAINER == "lichtfeld":

    print("==========================================")
    print("Starting Lichtfeld Studio")
    print("==========================================")
    print()

    cmd = [

        "lichtfeld-studio",

        "--data-path",
        str(PROJECT_DIR),

        "--output-path",
        str(PROJECT_DIR / "lichtfeld"),

        "--iter", "10000",

        "--train",
        "--headless",
        "--no-splash",

        "--log-level", "info",

        "--log-file",
        str(PROJECT_DIR / "lichtfeld.log"),
    ]

else:

    raise RuntimeError(
        f"Unknown trainer: {TRAINER}"
    )

# =====================================================
# RUN TRAINER
# =====================================================

subprocess.run(cmd, check=True)

print()
print("Pipeline complete.")
print()
