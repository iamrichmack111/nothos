Output assets/demo/nothos-dictionary.gif

Set Shell "bash"
Set FontSize 16
Set Width 1500
Set Height 1000
Set Theme "Dracula"
Set TypingSpeed 35ms

Type "clear"
Enter
Sleep 1s

Type ".venv/bin/nothos banner"
Enter
Sleep 5s

Type ".venv/bin/nothos research 'μυστήριον' --no-ai --top-k 5 --banner none"
Enter
Sleep 30s

Type ".venv/bin/nothos research 'Ἑρμῆς' --no-ai --top-k 5 --banner none"
Enter
Sleep 30s
