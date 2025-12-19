# 7-segment display font bcs we wanna display "FULL" when parking is full
# A B C D E F G DP
# bit order usually: DP G F E D C B A (MSB to LSB) or A B C... depends on wiring
# we'll use standard: Q0=A, Q1=B, ... Q7=DP

NUMBERS = [
    0b00111111, # 0
    0b00000110, # 1
    0b01011011, # 2
    0b01001111, # 3
    0b01100110, # 4
    0b01101101, # 5
    0b01111101, # 6
    0b00000111, # 7
    0b01111111, # 8
    0b01101111  # 9
]

F = 0b01110001
U = 0b00111110
L = 0b00111000
BLANK = 0b00000000

WORD_FULL = [F, U, L, L]

# dictionary for generic lookup if needed later
FONT = {
    '0': NUMBERS[0], '1': NUMBERS[1], '2': NUMBERS[2], '3': NUMBERS[3],
    '4': NUMBERS[4], '5': NUMBERS[5], '6': NUMBERS[6], '7': NUMBERS[7],
    '8': NUMBERS[8], '9': NUMBERS[9],
    'F': F, 'U': U, 'L': L, ' ': BLANK
}