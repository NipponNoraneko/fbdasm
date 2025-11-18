# Family BASIC Internal Details

This document presents details about some of the inner workings of Family BASIC.

## BASIC Program In-Memory Representation

The start of the storage area for (tokenized) BASIC program text is indicated by the variable [zpTXTTAB](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymzpTXTTAB) ($05.06). Family BASIC initializes this to `$6006` (in cartridge RAM, battery-backed&mdash;in this case by a pair of literal AA batteries), and never changes from that. It's possible that a BASIC program might be able to modify Family BASIC's understanding of where the program starts and re-run, providing reliable space for some machine-language code to live in "LOMEM" (Note: `LOMEM` is not a keyword or special variable name used by Family BASIC).

The end of the program (and start of variable data) is tracked by [zpVARTAB](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymzpVARTAB).

### Line Linkage

A line of BASIC code is represented as:
 1. A single byte indicating the offset from this position to the start of the next line of the program - that is, the number of bytes from this offset byte to the offset byte of the next line. Alternatively, it is 4 more than the *length* of the tokenized line (accounting for this byte, the two that follow it, and a terminating null character). If you have a pointer to this byte, add its value and you now have a pointer to the next line.
 2. A word containing the line number.
 3. The tokenized line contents.
 4. A terminating null byte (`$00`).

Note that the maximum length of a program line is 251 characters. If a user types a (numbered) line longer than this, Family BASIC will silently truncate it to fit.

Some related starting points: [DirectModeLoop](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymDirectModeLoop), where user lines are read in via [ReadLine](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymReadLine), which reads the line into [LineBuffer](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymLineBuffer) (`$500`) and, if numbered, sent along to [ProcessNumberedLine](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymProcessNumberedLine). The line gets [Tokenize](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymTokenize)d and stored in [TokenizeBuffer](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymTokenizeBuffer) (`$300`), any existing line with the same number gets deleted by [TxtDeleteLine](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymTxtDeleteLine), and then it gets inserted into its spot via [TxtInsertLine](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymTxtInsertLine), which finds its spot using [FindLineNum](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymFindLineNum).

### Tokenizing

Tokenization starts at [Tokenize](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymTokenize). [TokenizeKeyword](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymTokenizeKeyword) handles tokenizing keywords (*gasp!*), looking them up in [tbl_KeywordTokens](https://famibe.addictivecode.org/disassembly/fb3.nes.html#Symtbl_KeywordTokens) to swap them for token bytes. This table consists of a token byte (high bit is always set), followed by the keyword (high bit always unset). The table terminates with a `#$FF` byte.

If a keyword token is identified, it stores the token and then additionally checks if the keyword requires special token handling beyond this point (`REM` and `DATA` being obvious cases, but also any commands that accept line numbers as arguments, as these are tokenized differently from other numbers; see [Tokenized Numbers](#tokenized-numbers), immediately below).

#### Tokenized Numbers

When multi-digit, integer numbers are encountered, they are converted from decimal via [TokenizeNumber](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymTokenizeNumber) (or hexadecimal via [TokenizeHexNum](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymTokenizeHexNum), if preceded by `&`) to binary, and preceded by a special signifier byte, which is normally `#$12` if the number was in decimal, or `#$11` if it was hexadecimal (for redisplay purposes by `LIST`).

When a single-digit number is encountered, it is handled a little differently by [TokenizeNumber](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymTokenizeNumber): the number is incremented (so it goes from a value of 0-9, to a value of 1-10), and is then stored directly in the token stream. (The increment is to ensure we don't end up with the null terminating byte; it is re-decremented before display or interpretation.)

When a keyword is recognized and converted into a token, the tokenizer hands off to [StoreTokenAndHandleArgs](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymStoreTokenAndHandleArgs), which among other things checks to see whether the just-tokenized keyword expects line number arguments. If it does, then those args are handled *differently* from normal numeric literals, in that they get a `#$0B` prefix byte instead of `$#11` or `$#12`.

## The NMI Dispatch

The NMI vector at `#$FFFA` has the value `#$00ED`, an in-memory location in the Zero Page. Family BASIC sets RAM locations `$ED` through `$EF` to: `#$4C`, `#$71`, and `#$89`, very early on in [_Reset](https://famibe.addictivecode.org/disassembly/fb3.nes.html#Sym_Reset), before enabling NMI for vertical blanking. These byte values correspond to `jmp $8971`, which transfers execution to [NMI_DefaultHandler](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymNMI_DefaultHandler). Family BASIC never touches those bytes again, but there's nothing stopping a BASIC program author with solid 6502 programming skills, from installing a custom machine-code handler in memory, and poking its adress in place of the default handler's address. Presumably, that's why a RAM trampoline was used for NMI in the first place.

The default handler acts mainly as a sort of dispatch: code outside of NMI handling will set the value in [zpNMICMD](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymzpNMICMD) (`$63`), representing which command it wants the NMI handler to execute, and then loops until the value at that location changes to zero, indicating that the NMI action completed, and normal operations may continue. [zpNMICMD](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymzpNMICMD) is an index (starting at 1) into a table of handler routines; [NMI_DefaultHandler](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymNMI_DefaultHandler) subtracts 1, doubles the value, and then directly indexes [NMICMD_JumpTable](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymNMICMD_JumpTable) (whose indexed routines, at this time, have only been explored a small ways).

The subroutine typically used to set [zpNMICMD](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymzpNMICMD) and then wait for it to clear, is [WaitForNmiSubcommand](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymWaitForNmiSubcommand)

### Overriding Within BASIC Programs

As mentioned above, it is possible for an expert programmer to replace the default NMI handler with custom code in RAM. However, a replacement NMI handler must take great care, because the existing default handler manages things like printing screen output and reading input lines. I haven't explored enough yet to see it, but presumably it must also handle the automated sprite movement stuff (Family BASIC's `MOVE` command). As mentioned, there are numerous places that set [zpNMICMD](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymzpNMICMD) and then loop until the NMI handler clears it, so a replacement handler would either have to be sure to clear that (mercilessly discarding the requested action), or more likely it needs to call [NMI_DefaultHandler](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymNMI_DefaultHandler) itself (and let it do the `RTI` to return from interrupt handling). Of course, if it calls the default handler, then it should bear in mind that it might run for a significant portion of the vertical blank window, leaving less time for the user's custom handler to safely run without risking skipped frames.

Even so, one could probably manage things like stutterless background music (if it's simple enough to fit in available memory), or additional quick little checks or adjustments to sprite behaviors beyond the basic facilities included in Family BASIC.

### Printing Program Output

Most microcomputer BASIC implementations I've seen just poke values into video RAM directly within the print routines. Family BASIC can't do this, because the CPU can't access the video RAM directly, and the PPU can only do so at specific times, such as during vertical blank. So, nothing in the code for printing things to the screen can actually... print things to screen&mdash;not directly.

Instead, output is queued into a buffer, [outTxtBuf](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymoutTxtBuf), [zpNMICMD](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymzpNMICMD) is set to `#$01`, which (on next vertical blank) causes the NMI handler to call out to [NMICMD_FlushQueuedOutput](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymNMICMD_FlushQueuedOutput), which does the actual printing.

When, in the course of printing, the cursor goes past the end of a line and wraps to the next, [NMICMD_FlushQueuedOutput](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymNMICMD_FlushQueuedOutput) handles wrapping to the next row, including any scrolling if the cursor has run off the screen, and then returns from the interrupt handling, saving its current state, and leaving [zpNMICMD](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymzpNMICMD) with its current value so that NMI will return control back to the same routine at the next vertical blank.

If the cursor enters the 15th column (of 30) in the course of printing output, [NMICMD_FlushQueuedOutput](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymNMICMD_FlushQueuedOutput) again returns from interrupting handling, leaving things set up for a return next vertical blank. Thus, only a maximum of 15 characters are printed in any single vertical blanking period, to help ensure that printing completes before the vertical blank does.

#### Scrolling the Screen

On many, if not most, microcomputer implementations of BASIC in the 80's, scrolling past the end of the screen meant a fairly laborious process of copying the entire screenful of text up by one line, and then erasing the bottom line. But this is a Famicom, and we have vertical scroll registers. The Family BASIC cartridge has vertical mirroring set, which lets it treat the text screen like a ring buffer. So, scrolling the screen is as simple as incrementing the vertical scroll by 8 pixels, and bam! It's scrolled. Before it does that, Family BASIC first erases the top line of the currently-displayed screen. After scrolling, that line is now at the bottom of the screen, below the "text" contents of the screen. Family BASIC uses a 3-row vertical margin (and 2-column horizontal margin), so the formerly top line of the top margin has now become the bottom line of the bottom margin, after being erased.

The current vertical scroll value is saved in [zpVScroll0](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymzpVScroll0) (`$E4`) when `SCREEN 0` is active, and [zpVScroll1](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymzpVScroll1) (`$E5`) for `SCREEN 1`.

There is one additional thing that needs to be done when scrolling: Family BASIC keeps an array of flag bytes, one for each of 24 rows of screen text, that tracks whether a given row was "wrapped to" from a previous row, during printing. This is used for tracking single lines that span multiple rows. When the screen is scrolled by one line, then the values in this array must also be rotated.

The array used differs depending on whether `SCREEN 0` or `SCREEN 1` is active. [isRowWrappedArray0](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymisRowWrappedArray0) is used for the former, and [isRowWrappedArray1](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymisRowWrappedArray1) for the latter.

[ScrollScreenOneRowNoErase](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymScrollScreenOneRowNoErase) is the routine that handles the actual screen scrolling, including adjusting the line-wrap arrays.  It is used only by [ScrollScreenUpOneRow](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymScrollScreenUpOneRow) (erases the top line before scrolling, trampling [zpNMICMD](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymzpNMICMD)), and by [NMICMD_FlushQueuedOutput](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymNMICMD_FlushQueuedOutput) which has its own separate code for top-line erasure (avoiding the trample of its own zpNMICMD value).

Although Family BASIC itself never uses [ScrollScreenUpOneRow](https://famibe.addictivecode.org/disassembly/fb3.nes.html#SymScrollScreenUpOneRow) without first erasing the top row, its address can be called from BASIC (`CALL -18988`). The following example program infinitely scrolls a listing of numbers from 1 to 30, in a loop:

```
10 CLS
20 FOR I=1 TO 30:LOCATE 0,0:PRINT I;:CALL -18988:NEXT:GOTO 20
```

### Reading Line Input from the User

## Magnetic Data Cassette Representation

## BASIC Variables (TODO)
