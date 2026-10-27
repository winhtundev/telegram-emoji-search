Telegram Emoji Search — hosting instructions
=============================================
1. Unzip this file.
2. Upload the whole telegram-emoji-search folder to your hosting
   (or upload its contents to your web root).
3. Open index.html in a browser. No server code, database or build
   step is needed — it is plain HTML + JavaScript.
4. Search by name (e.g. ChatGPT), by pack, or by emoji ID.
   Hover a card to play the animated WebM; click a card (or Copy ID)
   to copy the Telegram custom-emoji ID.

Contents
--------
- index.html      : search page
- emojis.json     : 2,412 entries {id, name, alt, pack, thumb, webm}
- thumbs/         : 2,411 static JPG previews, by pack
- webm/           : 2,408 animated WebM files, by pack
- 4 emojis have no WebM file (Telegram refused to serve them) and
  1 has no thumbnail; those cards still show their name/pack/ID.
