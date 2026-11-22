// Box.asm — Nand to Tetris, Project 5 / Capstone (Part C)
// Shaurya Vinay Singh, Roll No. 2501010296, ETCCNT301
// Personal number K = 96  (K mod 4 = 0)
//
// Draws a black box on the Hack screen while any key is pressed and
// erases it (white) when no key is pressed.
//   Box start row : 96
//   Box height    : 20 rows  (rows 96..115)
//   Box width     : 16 pixels = 1 word, from the left edge
//   First word address = SCREEN + 32*96 = 16384 + 3072 = 19456
//   Each next row is 32 words further (one full screen row).
//
// Polls @KBD in a loop. If KBD != 0 the colour is -1 (black),
// otherwise it is 0 (white). The 20-row box is then (re)drawn
// with that colour, one word per row.

// ---- main loop: poll the keyboard and pick the colour ----
(LOOP)
  @KBD
  D=M
  @SETBLACK
  D;JNE          // key pressed -> black
  @color
  M=0            // no key -> white
  @DRAW
  0;JMP
(SETBLACK)
  @color
  M=-1           // black

// ---- draw the box: 20 rows starting at address 19456 ----
(DRAW)
  @19456
  D=A
  @addr
  M=D            // addr = first word of row 96
  @20
  D=A
  @i
  M=D            // i = 20 rows remaining
(DRAWLOOP)
  @i
  D=M
  @LOOP
  D;JEQ          // 0 rows left -> poll the keyboard again
  @color
  D=M
  @addr
  A=M
  M=D            // write the colour word (16 pixels) at this row
  @32
  D=A
  @addr
  M=D+M          // next row is 32 words further down
  @i
  M=M-1          // one row fewer to draw
  @DRAWLOOP
  0;JMP
