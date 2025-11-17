
# fbdasm README

## About

**fbdasm** is an attempt at annotated 6502 disassemblies for [Family BASIC](https://en.wikipedia.org/wiki/Family_BASIC), which is an implementation of the BASIC programming language for Famicom, allowing you to write small games in an accessible music, with background graphics, animated sprites, and sound effects/music. It was developed jointly by Hudson Soft, Sharp, and Nintendo. (An earlier version, called "Playbox BASIC", was very similar to v2.0, but did not involve Nintendo in the development. That version was targeted specifically at Sharp's "My Computer TV C1", which was a TV that included a built-in Famicom, and came with a keyboard

There were two major releases of the software, v2.0 and v3.0. v2.1 also existed, fixing a bug with one of the commands in v2.0 not working properly. I'm given to understand that v2.1 was never commercially released, but was available directly from Nintendo upon request.

It is planned to have annotated disassemblies of versions v2 and v3, but at this time there is only a partially-annotated disassembly of v3.

**NOTE:** The disassemblies produced by this project are *not* intended to be suitable for reassembly (rebuilding the original ROM file from the assembly code produced). The purpose of this disassembly is to inpsect and understand the code making up the ROM file. The CHAR ROM (graphics) is not included as part of the disassembly.

## How to Use This Project

Although this project is dedicated toward creating a disassembly of the 6502 code present in the Family BASIC cartridges, you will not see a disassembly present here in this git repo - the disassembly is *generated* from the files contained in this project, as well as one file *not* contained in this project (the ROM file for the Family Basic cartridge itself).

If you just want to see the finished product, [the hyperlinked disassembled code is available at this link](http://famibe.addictivecode.org/disassembly/fb3.nes.html) (updated only sporadically).

If you would like to know how to rebuild the disassembly, or contribute additions or changes to it, read on.

### Prerequisites

In order to generate the Family BASIC disassembly, you will need:

 - [SourceGen](https://6502bench.com/), the disassembly/annotation tool. Windows-only, but runs well on Wine 9+. This project was developed using [SourceGen version 1.10.0](https://github.com/fadden/6502bench/releases/tag/v1.10.0).
 - A ROM file containing the dump for the Family Basic v3 cartridge. You will have to find or dump this yourself, don't ask me where you can get it, nor to provide you with it. The ROM will need to be renamed to `fb3.nes` and placed in the project folder. It must be 40,976 bytes in size, and match the MD% checksum `2ba1dbbb774118eb903465f8e66f92a2`.

### Using SourceGen

Once the `fb3.nes` file is placed in the git repo working directory, then you can open the `fb3.nes.dis65` disassembly project file in SourceGen. SourceGen will use the info in the `.dis65` file, your added `fb3.nes` file, and the `fb3.sym65` file, to reconstruct the 6502 disassembly listing, which you can then explore within SourceGen.

To generate the disassembly as an external file (HTML or plain text), use the `Export...` entry in the `File` menu. The settings I personally use, look similar to what you see in the image below.

![The Export dialog window from SourceGen. Checked boxes are "Show Address column", "Show Bytes column", and "Put long labels on separate line". Column widths for label, opcode, oeprand, and comment, are 16, 8, 24, and 100, respectively.](images/export-diag.png)

