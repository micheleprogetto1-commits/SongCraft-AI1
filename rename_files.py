#!/usr/bin/env python3
"""
Script per rinominare i file rimuovendo caratteri non validi per Windows 10.
Caratteri rimossi: ' " : ; , - _ * #
"""

import os
import re

# Caratteri non accettati da Windows
INVALID_CHARS = r'[\'\"\:\;\,\-\_\*\#]'

def clean_filename(filename):
    """
    Rimuove i caratteri non validi dal nome del file.
    """
    # Separa nome e estensione
    name, ext = os.path.splitext(filename)
    
    # Rimuove i caratteri non validi
    clean_name = re.sub(INVALID_CHARS, '', name)
    
    # Rimuove spazi multipli
    clean_name = re.sub(r'\s+', ' ', clean_name)
    
    # Rimuove spazi all'inizio e fine
    clean_name = clean_name.strip()
    
    return clean_name + ext

# Test su alcuni nomi
test_files = [
    "04 - On The Run (Game Over Outro).wav.mp3",
    "A Thing In A Town.mp3.mp3",
    "Bosch's Garden – Mythical Game Music for Fantasy and AI Projects.mp3",
    "BAS-21022014 - Game Loop 10.mp3.mp3",
    "Hand Crank Music Box B [A5 Notes].mp3",
]

print("Esempi di rinominazione:")
for f in test_files:
    cleaned = clean_filename(f)
    print(f"  '{f}' -> '{cleaned}'")
