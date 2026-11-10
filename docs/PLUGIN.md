# Dot Art

Turn a picture into a printed halftone: big blobs of a second filament on a base, whose size carries the tone, like newspaper print enlarged. The nozzle stays still over each blob, so the dots are domes of filament and not drawn circles.

**How to use**
1. Open the Dot Art tab and pick an image. Drag it to position it, scroll to zoom.
2. Choose the frame shape, the art size, the base and dot filaments, the spacing and the blob sizes. The preview shows the planned blobs in your filament colors.
3. Press Save job and add base to plate. The base lands on the plate, with each filament already assigned.
4. In the process preset, under Multimaterial, enable the prime tower. Without it the first blobs print in the previous color.
5. In the process preset, under Others, set Slicing Pipeline Plugin to Dot Art G-code.
6. Slice. On a Bambu Lab printer the preview shows the blobs.

**The Slicing Pipeline Plugin setting**
The picture is made when you slice. Dot Art adds a slicing step that finds the top layer of its base and replaces it with blobs. OrcaSlicer runs that step only when it is selected: in the process preset, open Others, find Slicing Pipeline Plugin, press Add plugin and choose Dot Art G-code. Save the preset to keep it. A print that is not the Dot Art base is left as it is, so the setting can stay on.

**What it does**
- Prints each dot as a blob from a still nozzle, up to 8 mm wide.
- Six frame shapes: square, circle, rectangle, oval, rounded rectangle and hexagon. The base is made in the same shape.
- Lays the smallest blobs first, so melt left on the nozzle tip does not smear them.
- Spacing sets the density. Below the largest blob's width, the darkest blobs merge.
- Auto tone stretches and sharpens the picture, and can be turned off.
- Contrast, gamma and invert, with sliders for the settings that reshape the dots.

**Notes**
- Needs two filaments and a 0.4 mm nozzle. It is tuned for the Bambu Lab X1 Carbon, the only printer it has been printed on.
- The print in the photo is 100 mm square, at 3.2 mm spacing. Spacing below about 3 mm has not been print-tested.
- Auto tone and the frame shapes came after that print. They were checked on real sliced files and have not been printed.
- Thin strings between dots usually mean the filament's retraction or temperature needs adjusting. Retraction starts from your printer preset, and Retraction, Z lift and Hold after blob are in the tab's Nozzle section.
- OrcaSlicer's own time and filament totals still count the plain top layer. The tab shows the blob layer's time and filament.
- The slicer preview draws each blob as a diamond. It prints as a round dome.
- Adding the base to the plate automatically is Windows only. Elsewhere, the page shows the file to import.
- Free and open source, GPL-3.0-or-later.

Has a picture that did not come out well? Leave a comment with a photo of the print and your settings.
