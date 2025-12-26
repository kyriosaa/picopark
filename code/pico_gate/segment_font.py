# 7-segment display font bcs we wanna display "FULL" when parking is full
# A B C D E F G DP
# bit order usually: DP G F E D C B A (MSB to LSB) or A B C... depends on wiring
# we'll use standard: Q0=A, Q1=B, ... Q7=DP

F = 0b01110001
U = 0b00111110
L = 0b00111000
BLANK = 0b00000000

WORD_FULL = [F, U, L, L]