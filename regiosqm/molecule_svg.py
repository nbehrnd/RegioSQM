# name:  molecule_svg.py
# edit:  2020-12-03 (YYYY-MM-DD)
#
"""Prepare RDKit to generate .svg files after MOPAC's work.

    The script was adjusted for compatibility with Python 3 (3.8.4rc1)
    backed by RDKit (release 2019.9) in mind.  Do not use it with now
    legacy Python 2.7.17 (which would require RDKit prior release
    2019.3)."""

# rdkit
from rdkit import Chem
from rdkit.Chem import Draw


def create_svg(rdkitmol, highlights=None):
    """Define parameters per .svg file."""
    img = Draw.MolsToGridImage([rdkitmol],
                               molsPerRow=1,
                               subImgSize=(400, 400),
                               useSVG=True,
                               highlightAtomLists=[highlights])
    svg = img
    # svg = img.data
    svg = svg.replace("xmlns:svg", "xmlns")
    svg = svg[:-7]  # prevent an early closing svg tag.
    return svg


def get_highlights(svg, measured=False):
    """List all ellipses the current .svg file contains."""
    svg = svg.split("\n")
    highlights = []

    for line in svg:
        if "ellipse" in line:
            if measured:
                line = line.replace('fill:#FF7F7F', 'fill:none')
                line = line.replace('stroke-width:1px;', 'stroke-width:6px;')
            else:
                line = line.replace('stroke-width:1px;', 'stroke-width:0;')

            highlights.append(line)

    return highlights


def pretty_svg(svg):
    """Join elements of the molecular formula."""
    svg = svg.split("\n")

    for i, line in enumerate(svg):

        # Atom letters
        if "text" in line:

            replacetext = "font-size"
            borderline = """fill:none; fill-opacity:1; stroke:#FFFFFF;
                stroke-width:10px; stroke-linecap:butt; stroke-linejoin:miter;
                stroke-opacity:1;"""

            # Add border to text
            border_text = line
            border_text = border_text.replace('stroke:none;', '')
            border_text = border_text.replace(replacetext,
                                              borderline + replacetext)

            svg[i] = border_text + "\n" + line

            continue

        if "path" in line:

            # thicker lines
            line = line.replace('stroke-width:2px', 'stroke-width:3px')
            svg[i] = line

    svg = "\n".join(svg)

    return svg


def change_color(ellipse, color, find="#FF7F7F"):
    """Substitute the ellipses default fill color."""
    ellipse = ellipse.replace(find, color)
    return ellipse


def merge_svg(svg, highlights):
    """Accommodate ellipses (highlights) in the .svg string."""
    svg = svg.split("\n")

    index = 1
    for i, line in enumerate(svg):
        if "transform" in line:
            index = i
            break

    index += 1
    # svg = svg[0:index] + highlights + svg[index:]
    # better consecution, but ending </svg> too early:
    svg = svg[0:index] + svg[index:] + highlights
    svg = "\n".join(svg)
    #   svg += "</svg>"  # manually close the .svg string
    return svg


def generate_structure(smiles, predicted, highlight_measure=None):
    """Join molecular formula and predictions in one .svg string."""
    highlight_predicted, highlight_loseicted = predicted

    m = Chem.MolFromSmiles(smiles)
    Chem.Kekulize(m)

    # color_measured = "#9932CC" # Purple
    color_measured = "#000000"  # Black
    color_predicted = "#4daf4a"  # Green
    color_loseicted = "#e41a1c"  # Red

    base = create_svg(m)

    svg_measure = create_svg(m, highlights=highlight_measure)
    highlights_measure = get_highlights(svg_measure, measured=True)
    highlights_measure = [
        el.replace("#FF7F7F", color_measured) for el in highlights_measure
    ]

    svg_predicted = create_svg(m, highlights=highlight_predicted)
    highlights_predicted = get_highlights(svg_predicted)
    highlights_predicted = [
        el.replace("#FF7F7F", color_predicted) for el in highlights_predicted
    ]

    # did threshold find some predictions?
    # find ones not in predicted list
    highlight_loseicted = list(
        set(highlight_loseicted) - set(highlight_predicted))

    if highlight_loseicted is not None:
        svg_loseicted = create_svg(m, highlights=highlight_loseicted)
        highlights_loseicted = get_highlights(svg_loseicted)
        highlights_loseicted = [
            el.replace("#FF7F7F", color_loseicted)
            for el in highlights_loseicted
        ]
    else:
        highlights_loseicted = []

    svg = merge_svg(
        base, highlights_loseicted + highlights_predicted + highlights_measure)
    svg = pretty_svg(svg)

    return svg


def svg_corrector(recorder):
    """adjust the consecution of entries in the .svg

    The altered functions create_svg and merge_svg of this file yield
    a .svg where ellipses partially hide the structure formula plot.
    A move of the ellipses' definition within the .svg string ahead of
    those about the strokes of the formula corrects this, i.e., moves
    them into the background of the formula."""
    register_raw = []
    register_ellipses = []
    output_string = ""

    register_raw = recorder.split("\n")

    # identify entries to highlight positions
    for entry in register_raw:
        if str("ellipse") in str(entry):
            retain = str(entry).strip()
            register_ellipses.append(retain)
    register_ellipses = "\n".join(register_ellipses)
    register_ellipses += str("\n")

    # rebuild the .svg with an adjusted consecution of entries
    for entry in register_raw:
        if str("bond") in str(entry):
            output_string += str(register_ellipses)
            register_ellipses = ""
            output_string += str("{}\n".format(entry))

        elif (str("ellipse") or str("</svg>")) in str(entry):
            pass
        else:
            output_string += str("{}\n".format(entry))
    output_string += str("</svg>")
    return output_string


if __name__ == "__main__":

    smiles = "n1ccc[nH]1"
    highlight_measure = [1, 2]
    highlight_predicted = [2]

    smiles = "c1c(nnc(c1)c1ccc(cc1)N)OC1CN2CCC1CC2"
    highlight_measure = [8, 9]
    highlight_predicted = [8, 1, 5]
    highlight_loseicted = [1, 5, 10, 14]

    print(
        generate_structure(smiles, [highlight_predicted, highlight_loseicted],
                           highlight_measure=highlight_measure))
